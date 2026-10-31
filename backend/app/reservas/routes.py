"""Rutas de reservas (`/api/reservas` y `/api/espacios/{id}/disponibilidad`).

Cada ruta declara su permiso de la matriz; el guard `requiere_permiso`
autentica la petición y lo comprueba antes de la lógica. El listado y el
detalle exigen `reservas:ver_propias` (que todos los roles poseen) y el
servicio amplía la visibilidad a todas las solicitudes con
`reservas:ver_todas`.

Las fechas de las respuestas se serializan siempre en UTC con sufijo `Z`,
sea cual sea la zona horaria de la sesión de PostgreSQL. El reloj de la
validación de fechas es inyectable mediante `app.config["RELOJ"]`.
"""

from datetime import timezone

from flask import Blueprint, current_app, g, jsonify, request

from ..auth.services import requiere_permiso
from ..models.usuario import ahora_utc
from ..usuarios.routes import _cuerpo_json
from . import services

bp = Blueprint("reservas", __name__, url_prefix="/api")


def fecha_utc(fecha):
    """`datetime` con zona → ISO 8601 en UTC con sufijo `Z`."""
    texto = fecha.astimezone(timezone.utc).isoformat()
    return texto.removesuffix("+00:00") + "Z"


def datos_de_reserva(reserva):
    """Representación de una solicitud: id, espacio, solicitante, inicio, fin y estado."""
    return {
        "id": reserva.id,
        "espacio_id": reserva.espacio_id,
        "solicitante_id": reserva.solicitante_id,
        "inicio": fecha_utc(reserva.inicio_utc),
        "fin": fecha_utc(reserva.fin_utc),
        "estado": reserva.estado,
    }


def datos_de_intervalo(reserva):
    """Intervalo ocupado: solo inicio y fin, sin datos del solicitante."""
    return {"inicio": fecha_utc(reserva.inicio_utc), "fin": fecha_utc(reserva.fin_utc)}


def _reloj():
    return current_app.config.get("RELOJ", ahora_utc)


@bp.post("/reservas")
@requiere_permiso("reservas:crear")
def crear_solicitud():
    reserva = services.crear_solicitud(_cuerpo_json(), g.usuario_actual, reloj=_reloj())
    return datos_de_reserva(reserva), 201


@bp.get("/espacios/<int:espacio_id>/disponibilidad")
@requiere_permiso("espacios:ver")
def consultar_disponibilidad(espacio_id):
    ocupadas = services.consultar_disponibilidad(
        espacio_id, request.args.get("inicio"), request.args.get("fin")
    )
    return jsonify([datos_de_intervalo(r) for r in ocupadas])


@bp.get("/reservas")
@requiere_permiso("reservas:ver_propias")
def listar_solicitudes():
    return jsonify([datos_de_reserva(r) for r in services.listar_solicitudes(g.usuario_actual)])


@bp.get("/reservas/<int:reserva_id>")
@requiere_permiso("reservas:ver_propias")
def obtener_solicitud(reserva_id):
    return datos_de_reserva(services.obtener_solicitud(reserva_id, g.usuario_actual))
