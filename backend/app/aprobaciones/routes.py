"""Rutas de decisión sobre solicitudes (`/api/reservas/{id}/aprobar` y `/rechazar`).

Cada ruta declara su permiso de la matriz. Aprobar ignora el cuerpo. Rechazar
espera un objeto JSON con solo `motivo`; una forma inválida llega al servicio
como motivo ausente, para que se responda `datos_invalidos` en el lugar que le
corresponde en el orden de comprobaciones: después de la existencia y la autoría.
"""

from flask import Blueprint, g

from ..auth.errors import DatosInvalidos
from ..auth.services import requiere_permiso
from ..reservas.routes import _reloj, datos_de_reserva
from ..usuarios.routes import _cuerpo_json
from . import services

bp = Blueprint("aprobaciones", __name__, url_prefix="/api")


def _motivo_del_cuerpo():
    try:
        datos = _cuerpo_json()
    except DatosInvalidos:
        return None
    return datos["motivo"] if set(datos) == {"motivo"} else None


@bp.post("/reservas/<int:reserva_id>/aprobar")
@requiere_permiso("aprobaciones:aprobar")
def aprobar_solicitud(reserva_id):
    reserva = services.decidir(reserva_id, g.usuario_actual, services.APROBAR, reloj=_reloj())
    return datos_de_reserva(reserva)


@bp.post("/reservas/<int:reserva_id>/rechazar")
@requiere_permiso("aprobaciones:rechazar")
def rechazar_solicitud(reserva_id):
    reserva = services.decidir(
        reserva_id, g.usuario_actual, services.RECHAZAR, _motivo_del_cuerpo(), reloj=_reloj()
    )
    return datos_de_reserva(reserva)
