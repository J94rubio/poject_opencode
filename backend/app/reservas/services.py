"""Servicios de reservas (spec `reservas`; design.md del change `reservas-disponibilidad`).

Contienen las validaciones, la regla de ocupación y el control por rol del
listado y el detalle, y confirman las transacciones. La autenticación y el
permiso de cada ruta los resuelve el guard `requiere_permiso`.

Fechas: solo ISO 8601 con zona horaria explícita; se convierten a UTC. El
instante actual se obtiene de un reloj inyectable (`reloj`), de modo que las
validaciones no dependen de la fecha real en las pruebas.

Orden de validación al crear: cuerpo con forma válida y sin campos ajenos
(incluidos el solicitante y el estado), campos obligatorios presentes, tipo
del espacio, fechas (zona horaria, fin posterior al inicio, inicio posterior
al instante actual), existencia y estado del espacio y, por último,
solapamiento con reservas aprobadas.
"""

from datetime import datetime, timezone

from ..auth.errors import (
    DatosInvalidos,
    EspacioInactivo,
    PermisoInsuficiente,
    ReservaSolapada,
    SolicitudNoEncontrada,
)
from ..auth.permissions import tiene_permiso
from ..espacios import services as servicio_espacios
from ..extensions import db
from ..historial import repositories as repositorio_historial
from ..models.usuario import ahora_utc
from ..validaciones import ID_MAXIMO
from . import repositories

# Campos de una solicitud: todos obligatorios y ningún otro. El solicitante es
# siempre el usuario autenticado y el estado inicial siempre `pendiente`.
CAMPOS = frozenset({"espacio_id", "inicio", "fin"})

# Último fin admitido en una solicitud. PostgreSQL devuelve cada fecha en la zona de
# su sesión y `datetime` no representa el año 10000: el último día de 9999 no se podría
# leer con un desfase positivo. Es un límite técnico, no una regla de negocio; las
# consultas por rango no lo aplican porque sus fechas no se vuelven a leer.
FIN_MAXIMO_UTC = datetime(9999, 12, 31, tzinfo=timezone.utc)


# --- Validaciones -----------------------------------------------------------


def convertir_fecha(valor):
    """ISO 8601 con zona horaria explícita → `datetime` en UTC.

    Una fecha sin zona horaria, con formato inválido, que no es texto o que no
    se puede expresar en UTC es `datos_invalidos`.
    """
    if not isinstance(valor, str):
        raise DatosInvalidos()
    try:
        fecha = datetime.fromisoformat(valor)
    except ValueError:
        raise DatosInvalidos() from None
    if fecha.tzinfo is None or fecha.utcoffset() is None:
        raise DatosInvalidos()
    try:
        return fecha.astimezone(timezone.utc)
    except OverflowError:
        raise DatosInvalidos() from None


def validar_rango(inicio, fin):
    """Rango semiabierto `[inicio, fin)` en UTC con fin posterior al inicio."""
    inicio_utc = convertir_fecha(inicio)
    fin_utc = convertir_fecha(fin)
    if fin_utc <= inicio_utc:
        raise DatosInvalidos()
    return inicio_utc, fin_utc


def _es_entero(valor):
    # `bool` es subtipo de `int` en Python, pero no es un identificador.
    return isinstance(valor, int) and not isinstance(valor, bool)


def _obtener_espacio(espacio_id):
    """Espacio del catálogo de `espacios`, activo o inactivo; 404 si no existe."""
    return servicio_espacios.obtener_espacio(espacio_id)


def _ve_todas(usuario):
    return tiene_permiso(usuario.rol.nombre, "reservas:ver_todas")


# --- Operaciones ------------------------------------------------------------


def crear_solicitud(datos, solicitante, reloj=ahora_utc):
    """Crea una solicitud `pendiente` del usuario autenticado `solicitante`."""
    if not isinstance(datos, dict) or set(datos) != CAMPOS:
        raise DatosInvalidos()
    if not _es_entero(datos["espacio_id"]):
        raise DatosInvalidos()

    inicio_utc, fin_utc = validar_rango(datos["inicio"], datos["fin"])
    # Una solicitud que empieza en el instante actual ya comenzó.
    if inicio_utc <= reloj() or fin_utc > FIN_MAXIMO_UTC:
        raise DatosInvalidos()

    espacio = _obtener_espacio(datos["espacio_id"])
    if espacio.estado != "activo":
        raise EspacioInactivo()

    # Solo las reservas aprobadas ocupan; las pendientes pueden solaparse.
    if repositories.listar_aprobadas_por_espacio_y_rango(espacio.id, inicio_utc, fin_utc):
        raise ReservaSolapada()

    # La solicitud y su entrada del historial se confirman juntas o no se aplican. La
    # solicitud devuelta describe el resultado de esa transacción, no una relectura posterior.
    try:
        reserva = repositories.crear(espacio.id, solicitante.id, inicio_utc, fin_utc)
        repositorio_historial.registrar(
            db.session, reserva, None, "pendiente", solicitante, reloj=reloj
        )
        repositories.desvincular(reserva)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return reserva


def consultar_disponibilidad(espacio_id, inicio, fin):
    """Reservas aprobadas del espacio que ocupan parte del rango consultado.

    El espacio debe existir, aunque esté inactivo.
    """
    inicio_utc, fin_utc = validar_rango(inicio, fin)
    espacio = _obtener_espacio(espacio_id)
    return repositories.listar_aprobadas_por_espacio_y_rango(espacio.id, inicio_utc, fin_utc)


def listar_solicitudes(usuario):
    """Todas las solicitudes con `reservas:ver_todas`; si no, solo las propias."""
    if _ve_todas(usuario):
        return repositories.listar_todas()
    return repositories.listar_por_solicitante(usuario.id)


def obtener_solicitud(reserva_id, usuario):
    """Detalle de una solicitud: 404 si no existe; 403 si es ajena y el
    usuario no tiene `reservas:ver_todas`."""
    reserva = repositories.buscar_por_id(reserva_id) if 0 < reserva_id <= ID_MAXIMO else None
    if reserva is None:
        raise SolicitudNoEncontrada()
    if reserva.solicitante_id != usuario.id and not _ve_todas(usuario):
        raise PermisoInsuficiente()
    return reserva
