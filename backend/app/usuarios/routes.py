"""Rutas del módulo de gestión de usuarios (`/api/usuarios`, `/api/roles`)."""

from flask import Blueprint

bp = Blueprint("usuarios", __name__, url_prefix="/api")
