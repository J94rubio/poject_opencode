"""Rutas del módulo de autenticación (`/api/auth`)."""

from flask import Blueprint, g, request

from . import services
from .tokens import TIPO_TOKEN, emitir_token, vigencia_en_segundos

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def datos_publicos(usuario):
    """Datos públicos de la cuenta: nunca la contraseña ni su hash."""
    return {
        "id": usuario.id,
        "nombre": usuario.nombre,
        "correo": usuario.correo,
        "rol": usuario.rol.nombre,
    }


@bp.post("/login")
def login():
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict):
        datos = {}
    usuario = services.autenticar(datos.get("correo"), datos.get("contrasena"))
    return {
        "token": emitir_token(usuario.id),
        "tipo_token": TIPO_TOKEN,
        "expira_en": vigencia_en_segundos(),
        "usuario": datos_publicos(usuario),
    }


@bp.get("/me")
@services.requiere_autenticacion
def me():
    usuario = g.usuario_actual
    return {**datos_publicos(usuario), "activo": usuario.activo}
