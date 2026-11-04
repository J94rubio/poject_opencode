"""Ruta de cancelación de solicitudes (`POST /api/reservas/{id}/cancelar`).

El cuerpo de la petición se ignora.
"""

from flask import Blueprint, g

from ..auth.services import requiere_permiso
from ..reservas.routes import _reloj, datos_de_reserva
from . import services

bp = Blueprint("cancelaciones", __name__, url_prefix="/api")


@bp.post("/reservas/<int:reserva_id>/cancelar")
@requiere_permiso("reservas:cancelar_propia")
def cancelar_solicitud(reserva_id):
    return datos_de_reserva(services.cancelar(reserva_id, g.usuario_actual, reloj=_reloj()))
