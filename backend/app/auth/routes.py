"""Rutas del módulo de autenticación (`/api/auth`)."""

from flask import Blueprint

bp = Blueprint("auth", __name__, url_prefix="/api/auth")
