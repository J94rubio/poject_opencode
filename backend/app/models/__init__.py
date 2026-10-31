"""Modelos ORM del sistema."""

from .rol import ROLES_DEL_CATALOGO, Rol
from .usuario import Usuario

__all__ = ["ROLES_DEL_CATALOGO", "Rol", "Usuario"]
