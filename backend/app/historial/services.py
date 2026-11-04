"""Consulta del historial (spec `historial`; design.md de `cancelacion-historial`).

Valida los filtros y aplica la visibilidad del rol: con `historial:ver_todos` se
ven todas las entradas; si no, solo las de las reservas del propio usuario. Los
filtros mal formados (400) se detectan antes que el espacio inexistente (404), en
el mismo orden que la consulta de disponibilidad.
"""

import re

from ..auth.errors import DatosInvalidos
from ..auth.permissions import tiene_permiso
from ..models import ESTADOS_DE_RESERVA
from ..reservas.services import _obtener_espacio, validar_rango
from . import repositories


def _espacio_id(valor):
    """Identificador de espacio del parámetro de consulta: solo un entero decimal."""
    if re.fullmatch(r"-?[0-9]+", valor) is None:
        raise DatosInvalidos()
    try:
        return int(valor)
    except ValueError:  # Python limita los dígitos convertibles.
        raise DatosInvalidos() from None


def _rango(desde, hasta):
    """`desde` y `hasta` se exigen juntos, con zona horaria y `hasta` posterior."""
    try:
        return validar_rango(desde, hasta)
    except OverflowError:  # Una fecha extrema no se puede expresar en UTC.
        raise DatosInvalidos() from None


def consultar(usuario, espacio_id=None, estado=None, desde=None, hasta=None):
    """Entradas visibles para el usuario con los filtros recibidos como texto (o `None`)."""
    espacio = _espacio_id(espacio_id) if espacio_id is not None else None
    if estado is not None and estado not in ESTADOS_DE_RESERVA:
        raise DatosInvalidos()
    desde_utc, hasta_utc = (None, None)
    if desde is not None or hasta is not None:
        desde_utc, hasta_utc = _rango(desde, hasta)
    if espacio is not None:
        _obtener_espacio(espacio)

    visibles = (
        repositories.TODOS
        if tiene_permiso(usuario.rol.nombre, "historial:ver_todos")
        else usuario.id
    )
    return repositories.listar(visibles, espacio, estado, desde_utc, hasta_utc)
