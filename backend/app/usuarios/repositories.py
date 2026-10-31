"""Repositorio de usuarios y roles: acceso a datos con SQLAlchemy.

No contiene reglas de negocio ni confirma transacciones: eso corresponde a la
capa de servicios.
"""

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from ..extensions import db
from ..models import Rol, Usuario


def obtener_rol_por_nombre(nombre):
    return db.session.execute(select(Rol).where(Rol.nombre == nombre)).scalar_one_or_none()


def crear_usuario(nombre, correo, password_hash, rol, activo=True):
    usuario = Usuario(
        nombre=nombre,
        correo=correo,
        password_hash=password_hash,
        rol=rol,
        activo=activo,
    )
    db.session.add(usuario)
    db.session.flush()
    return usuario


def obtener_usuario_por_id(usuario_id):
    """Carga el usuario junto con su rol en una única consulta."""
    return db.session.execute(
        select(Usuario).options(joinedload(Usuario.rol)).where(Usuario.id == usuario_id)
    ).scalar_one_or_none()
