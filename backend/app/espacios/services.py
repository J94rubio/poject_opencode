"""Servicios del catálogo de espacios (spec `espacios`; design.md, D3, D4 y D5).

Contienen las validaciones y las transiciones de estado, y confirman las
transacciones. La autorización por permiso la resuelve el guard de las rutas.

Orden de validación (D4): cuerpo con forma válida y sin campos ajenos,
campos obligatorios presentes (solo en el alta), nombre, tipo, capacidad y
unicidad del nombre. Un campo presente con valor `null` se valida según su
tipo, no se trata como ausente.
"""

from sqlalchemy.exc import IntegrityError

from ..auth.errors import (
    CapacidadInvalida,
    DatosInvalidos,
    EspacioDuplicado,
    EspacioNoEncontrado,
    EspacioYaActivo,
    EspacioYaInactivo,
    TipoEspacioInvalido,
)
from ..extensions import db
from ..models.espacio import TIPOS_DE_ESPACIO
from . import repositories

# Campos que admiten el alta (todos obligatorios) y la edición (todos
# opcionales). Cualquier otro campo, incluidos `estado` e `id`, se rechaza.
CAMPOS = frozenset({"nombre", "tipo", "capacidad"})

INDICE_NOMBRE = "ux_espacios_nombre"

# Máximo del tipo INTEGER de PostgreSQL (columna `capacidad`). Es un límite
# técnico, no una regla de negocio: evita que la base rechace el valor con un
# error interno.
CAPACIDAD_MAXIMA = 2_147_483_647


# --- Validaciones -----------------------------------------------------------


def _validar_cuerpo(datos):
    if not isinstance(datos, dict) or not set(datos) <= CAMPOS:
        raise DatosInvalidos()


def _validar_nombre(nombre):
    if not isinstance(nombre, str) or not repositories.normalizar_nombre(nombre):
        raise DatosInvalidos()
    return repositories.normalizar_nombre(nombre)


def _validar_tipo(tipo):
    if not isinstance(tipo, str) or tipo not in TIPOS_DE_ESPACIO:
        raise TipoEspacioInvalido()
    return tipo


def _validar_capacidad(capacidad):
    # `bool` es subtipo de `int` en Python, pero no es una capacidad (D4).
    if not isinstance(capacidad, int) or isinstance(capacidad, bool):
        raise CapacidadInvalida()
    if not 0 < capacidad <= CAPACIDAD_MAXIMA:
        raise CapacidadInvalida()
    return capacidad


def _nombre_libre(nombre, excepto_id=None):
    """Unicidad contra cualquier espacio, activo o inactivo, salvo el propio."""
    existente = repositories.obtener_espacio_por_nombre(nombre)
    if existente is not None and existente.id != excepto_id:
        raise EspacioDuplicado()


def _es_violacion_del_nombre(error):
    diag = getattr(error.orig, "diag", None)
    return getattr(diag, "constraint_name", None) == INDICE_NOMBRE


def _escribir(operacion):
    """Ejecuta la escritura y confirma; el índice único resuelve las carreras."""
    try:
        resultado = operacion()
        db.session.commit()
    except IntegrityError as error:
        db.session.rollback()
        if _es_violacion_del_nombre(error):
            raise EspacioDuplicado() from None
        raise
    return resultado


def _obtener(espacio_id):
    espacio = repositories.obtener_espacio_por_id(espacio_id)
    if espacio is None:
        raise EspacioNoEncontrado()
    return espacio


# --- Operaciones ------------------------------------------------------------


def crear_espacio(datos):
    """Alta de un espacio en estado `activo` con nombre, tipo y capacidad."""
    _validar_cuerpo(datos)
    if set(datos) != CAMPOS:
        raise DatosInvalidos()

    nombre = _validar_nombre(datos["nombre"])
    tipo = _validar_tipo(datos["tipo"])
    capacidad = _validar_capacidad(datos["capacidad"])
    _nombre_libre(nombre)

    return _escribir(lambda: repositories.crear_espacio(nombre, tipo, capacidad))


def listar_espacios():
    """Todos los espacios, incluidos los inactivos."""
    return repositories.listar_espacios()


def obtener_espacio(espacio_id):
    return _obtener(espacio_id)


def editar_espacio(espacio_id, datos):
    """Edición parcial de nombre, tipo y capacidad; nunca cambia el estado.

    Los campos omitidos conservan su valor y un cuerpo vacío no cambia nada.
    """
    espacio = _obtener(espacio_id)
    _validar_cuerpo(datos)

    cambios = {}
    if "nombre" in datos:
        cambios["nombre"] = _validar_nombre(datos["nombre"])
    if "tipo" in datos:
        cambios["tipo"] = _validar_tipo(datos["tipo"])
    if "capacidad" in datos:
        cambios["capacidad"] = _validar_capacidad(datos["capacidad"])
    if "nombre" in cambios:
        _nombre_libre(cambios["nombre"], excepto_id=espacio.id)

    return _escribir(lambda: repositories.actualizar_espacio(espacio, **cambios))


def desactivar_espacio(espacio_id):
    """`activo` → `inactivo`, conservando el resto de datos."""
    espacio = _obtener(espacio_id)
    if espacio.estado == "inactivo":
        raise EspacioYaInactivo()
    return _escribir(lambda: repositories.cambiar_estado(espacio, "inactivo"))


def activar_espacio(espacio_id):
    """`inactivo` → `activo`, conservando el resto de datos."""
    espacio = _obtener(espacio_id)
    if espacio.estado == "activo":
        raise EspacioYaActivo()
    return _escribir(lambda: repositories.cambiar_estado(espacio, "activo"))
