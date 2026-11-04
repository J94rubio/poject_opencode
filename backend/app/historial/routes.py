"""Ruta de consulta del historial (`GET /api/historial`).

El guard exige `historial:ver_propio`, que todos los roles poseen, y el servicio
amplía la visibilidad con `historial:ver_todos`. No existen rutas de escritura:
cualquier otro método responde 405 `metodo_no_permitido` en el manejador común.
Como en la consulta de disponibilidad, los parámetros desconocidos se ignoran.
"""

from flask import Blueprint, g, jsonify, request

from ..auth.services import requiere_permiso
from ..reservas.routes import fecha_utc
from . import services

bp = Blueprint("historial", __name__, url_prefix="/api")


def datos_de_entrada(entrada):
    """Entrada del historial; el actor se expone solo por su identificador."""
    return {
        "id": entrada.id,
        "reserva_id": entrada.reserva_id,
        "espacio_id": entrada.espacio_id,
        "estado_anterior": entrada.estado_anterior,
        "estado_nuevo": entrada.estado_nuevo,
        "actor_id": entrada.actor_id,
        "fecha_utc": fecha_utc(entrada.fecha_utc),
    }


@bp.get("/historial")
@requiere_permiso("historial:ver_propio")
def consultar_historial():
    entradas = services.consultar(
        g.usuario_actual,
        request.args.get("espacio_id"),
        request.args.get("estado"),
        request.args.get("desde"),
        request.args.get("hasta"),
    )
    return jsonify([datos_de_entrada(e) for e in entradas])
