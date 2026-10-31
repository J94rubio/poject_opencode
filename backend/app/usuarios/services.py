"""Servicios de gestión de usuarios (spec `usuarios`; design.md, D3, D6, D7 y D8).

Contienen las reglas de negocio de la gestión de cuentas y confirman las
transacciones. La autorización por permiso la resuelve el guard de las rutas;
aquí se aplican las validaciones de datos y la protección del acceso
administrativo (un `admin` no puede desactivarse ni cambiar su propio rol).
"""

import re

from flask import current_app
from sqlalchemy.exc import IntegrityError

from ..auth.errors import (
    ContrasenaInvalida,
    CorreoDuplicado,
    DatosInvalidos,
    OperacionNoPermitida,
    RolInvalido,
    UsuarioNoEncontrado,
)
from ..auth.services import generar_hash_password
from ..extensions import db
from ..models import ROLES_DEL_CATALOGO
from . import repositories

# Longitudes máximas de las columnas `nombre` y `correo` (models/usuario.py).
NOMBRE_MAX = 120
CORREO_MAX = 254

# Campos que admite la edición de una cuenta (spec `usuarios`).
CAMPOS_EDITABLES = frozenset({"nombre", "correo", "rol"})

# Formato de correo: una parte local, una arroba y un dominio con al menos un
# punto, sin espacios ni arrobas adicionales.
_PATRON_CORREO = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# --- Validaciones -----------------------------------------------------------


def _validar_nombre(nombre):
    if not isinstance(nombre, str) or not nombre.strip() or len(nombre.strip()) > NOMBRE_MAX:
        raise DatosInvalidos()
    return nombre.strip()


def _validar_correo(correo):
    if not isinstance(correo, str):
        raise DatosInvalidos()
    correo = correo.strip()
    if len(correo) > CORREO_MAX or not _PATRON_CORREO.match(correo):
        raise DatosInvalidos()
    return correo


def _validar_contrasena(contrasena):
    """Política de contraseñas (D6): mínimo de caracteres, sin reglas de composición."""
    if not isinstance(contrasena, str) or contrasena == "":
        raise DatosInvalidos()
    if len(contrasena) < current_app.config["PASSWORD_MIN_LENGTH"]:
        raise ContrasenaInvalida()
    return contrasena


def _validar_rol(nombre_rol):
    if not isinstance(nombre_rol, str) or nombre_rol not in ROLES_DEL_CATALOGO:
        raise RolInvalido()
    rol = repositories.obtener_rol_por_nombre(nombre_rol)
    if rol is None:
        raise RolInvalido()
    return rol


def _correo_libre(correo, excepto_id=None):
    existente = repositories.obtener_usuario_por_correo(correo)
    if existente is not None and existente.id != excepto_id:
        raise CorreoDuplicado()


def _confirmar():
    """Confirma la transacción; el índice único de correo resuelve las carreras."""
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise CorreoDuplicado() from None


def _obtener(usuario_id):
    usuario = repositories.obtener_usuario_por_id(usuario_id)
    if usuario is None:
        raise UsuarioNoEncontrado()
    return usuario


# --- Operaciones ------------------------------------------------------------


def crear_usuario(datos):
    """Alta de una cuenta activa con nombre, correo, contraseña y rol."""
    if not isinstance(datos, dict):
        raise DatosInvalidos()
    for campo in ("nombre", "correo", "contrasena", "rol"):
        if datos.get(campo) is None:
            raise DatosInvalidos()

    nombre = _validar_nombre(datos["nombre"])
    correo = _validar_correo(datos["correo"])
    contrasena = _validar_contrasena(datos["contrasena"])
    rol = _validar_rol(datos["rol"])
    _correo_libre(correo)

    usuario = repositories.crear_usuario(nombre, correo, generar_hash_password(contrasena), rol)
    _confirmar()
    return usuario


def listar_usuarios():
    """Todas las cuentas, incluidas las desactivadas."""
    return repositories.listar_usuarios()


def obtener_usuario(usuario_id):
    return _obtener(usuario_id)


def editar_usuario(usuario_id, datos, actor):
    """Actualiza nombre, correo y rol, sin tocar el estado ni la contraseña.

    Cualquier otro campo del cuerpo (incluidos `activo` y `contrasena`) se
    rechaza con `datos_invalidos` sin modificar nada; un cuerpo vacío no
    cambia nada. Un `admin` no puede cambiar su propio rol
    (`operacion_no_permitida`).
    """
    if not isinstance(datos, dict):
        raise DatosInvalidos()
    usuario = _obtener(usuario_id)
    if not set(datos) <= CAMPOS_EDITABLES:
        raise DatosInvalidos()

    nombre = _validar_nombre(datos["nombre"]) if "nombre" in datos else None
    correo = _validar_correo(datos["correo"]) if "correo" in datos else None
    rol = _validar_rol(datos["rol"]) if "rol" in datos else None

    if rol is not None and usuario.id == actor.id and rol.id != usuario.rol_id:
        raise OperacionNoPermitida()
    if correo is not None:
        _correo_libre(correo, excepto_id=usuario.id)

    if nombre is not None:
        usuario.nombre = nombre
    if correo is not None:
        usuario.correo = repositories.normalizar_correo(correo)
    if rol is not None:
        usuario.rol = rol
    _confirmar()
    return usuario


def restablecer_contrasena(usuario_id, datos):
    """Asigna una contraseña nueva; la vigente nunca se expone."""
    if not isinstance(datos, dict):
        raise DatosInvalidos()
    usuario = _obtener(usuario_id)
    contrasena = _validar_contrasena(datos.get("contrasena"))
    usuario.password_hash = generar_hash_password(contrasena)
    db.session.commit()


def desactivar_usuario(usuario_id, actor):
    """Desactiva la cuenta conservando sus datos; pierde el acceso de inmediato (D5).

    Un `admin` no puede desactivar su propia cuenta (`operacion_no_permitida`).
    """
    usuario = _obtener(usuario_id)
    if usuario.id == actor.id:
        raise OperacionNoPermitida()
    usuario.activo = False
    # Aserción defensiva (D7): la regla anterior garantiza que siempre queda
    # al menos un administrador activo, el propio actor.
    assert repositories.contar_admins_activos() >= 1
    db.session.commit()
    return usuario


def activar_usuario(usuario_id):
    usuario = _obtener(usuario_id)
    usuario.activo = True
    db.session.commit()
    return usuario


def listar_roles():
    return repositories.listar_roles()
