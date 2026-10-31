"""Rutas del módulo de gestión de usuarios (`/api/usuarios`, `/api/roles`).

Cada ruta declara su permiso de la matriz (design.md, D8); el guard
`requiere_permiso` autentica la petición y lo comprueba antes de la lógica.
"""

from flask import Blueprint, g, jsonify, request

from ..auth.errors import DatosInvalidos
from ..auth.services import requiere_permiso
from . import services

bp = Blueprint("usuarios", __name__, url_prefix="/api")


def datos_de_cuenta(usuario):
    """Datos de la cuenta para la administración: nunca la contraseña ni su hash."""
    return {
        "id": usuario.id,
        "nombre": usuario.nombre,
        "correo": usuario.correo,
        "rol": usuario.rol.nombre,
        "activo": usuario.activo,
    }


def _cuerpo_json():
    """Cuerpo JSON de la petición; si falta o no es un objeto, `datos_invalidos`."""
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict):
        raise DatosInvalidos()
    return datos


@bp.get("/usuarios")
@requiere_permiso("usuarios:ver")
def listar_usuarios():
    return jsonify([datos_de_cuenta(u) for u in services.listar_usuarios()])


@bp.post("/usuarios")
@requiere_permiso("usuarios:crear")
def crear_usuario():
    usuario = services.crear_usuario(_cuerpo_json())
    return datos_de_cuenta(usuario), 201


@bp.get("/usuarios/<int:usuario_id>")
@requiere_permiso("usuarios:ver")
def obtener_usuario(usuario_id):
    return datos_de_cuenta(services.obtener_usuario(usuario_id))


@bp.patch("/usuarios/<int:usuario_id>")
@requiere_permiso("usuarios:editar")
def editar_usuario(usuario_id):
    usuario = services.editar_usuario(usuario_id, _cuerpo_json(), g.usuario_actual)
    return datos_de_cuenta(usuario)


@bp.post("/usuarios/<int:usuario_id>/password")
@requiere_permiso("usuarios:resetear_password")
def restablecer_contrasena(usuario_id):
    services.restablecer_contrasena(usuario_id, _cuerpo_json())
    return "", 200


@bp.post("/usuarios/<int:usuario_id>/desactivar")
@requiere_permiso("usuarios:desactivar")
def desactivar_usuario(usuario_id):
    return datos_de_cuenta(services.desactivar_usuario(usuario_id, g.usuario_actual))


@bp.post("/usuarios/<int:usuario_id>/activar")
@requiere_permiso("usuarios:activar")
def activar_usuario(usuario_id):
    return datos_de_cuenta(services.activar_usuario(usuario_id))


@bp.get("/roles")
@requiere_permiso("roles:ver")
def listar_roles():
    return jsonify([{"id": rol.id, "nombre": rol.nombre} for rol in services.listar_roles()])
