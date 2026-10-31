"""Repositorio de espacios: acceso a datos con SQLAlchemy (design.md, D1 y D2).

No contiene reglas de negocio ni confirma transacciones: eso corresponde a la
capa de servicios. Al escribir, el nombre se guarda sin espacios exteriores;
la unicidad sin distinguir mayúsculas la garantiza el índice
`ux_espacios_nombre` sobre `lower(btrim(nombre))`.
"""

from sqlalchemy import select

from ..extensions import db
from ..models import Espacio

_SIN_CAMBIO = object()


def normalizar_nombre(nombre):
    """Elimina los espacios exteriores del nombre (spec `espacios`)."""
    return nombre.strip()


def crear_espacio(nombre, tipo, capacidad):
    """Da de alta un espacio; la base lo crea en estado `activo`."""
    espacio = Espacio(nombre=normalizar_nombre(nombre), tipo=tipo, capacidad=capacidad)
    db.session.add(espacio)
    db.session.flush()
    return espacio


def listar_espacios():
    """Todos los espacios, activos e inactivos, ordenados por id."""
    return db.session.execute(select(Espacio).order_by(Espacio.id)).scalars().all()


def obtener_espacio_por_id(espacio_id):
    return db.session.get(Espacio, espacio_id)


def actualizar_espacio(espacio, *, nombre=_SIN_CAMBIO, tipo=_SIN_CAMBIO, capacidad=_SIN_CAMBIO):
    """Actualiza solo los campos indicados; el estado no se modifica aquí."""
    if nombre is not _SIN_CAMBIO:
        espacio.nombre = normalizar_nombre(nombre)
    if tipo is not _SIN_CAMBIO:
        espacio.tipo = tipo
    if capacidad is not _SIN_CAMBIO:
        espacio.capacidad = capacidad
    db.session.flush()
    return espacio


def cambiar_estado(espacio, estado):
    """Fija el estado (`activo` o `inactivo`) conservando el resto de datos."""
    espacio.estado = estado
    db.session.flush()
    return espacio
