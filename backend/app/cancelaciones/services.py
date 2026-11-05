"""Cancelación de reservas propias (spec `cancelaciones`; design.md de `cancelacion-historial`).

El permiso lo resuelve el guard de la ruta; el resto de comprobaciones, en este
orden: existencia, dueño, estado (`pendiente` o `aprobada`) e inicio posterior al
instante actual.

La solicitud se lee con `SELECT ... FOR UPDATE`, igual que en `decidir`: una
cancelación y otra cancelación o una decisión sobre la misma solicitud se
serializan, y la segunda ve el estado ya cambiado. No se bloquea el espacio: pasar
a `cancelada` no puede crear un solapamiento. El cambio de estado y su entrada del
historial se confirman juntos; cualquier fallo deshace ambos. La solicitud devuelta
describe el resultado de esa transacción, no una relectura posterior a confirmarla.
"""

from ..auth.errors import (
    PermisoInsuficiente,
    ReservaIniciada,
    SolicitudNoEncontrada,
    TransicionInvalida,
)
from ..extensions import db
from ..historial import repositories as repositorio_historial
from ..models.usuario import ahora_utc
from ..reservas import repositories
from ..validaciones import ID_MAXIMO

ESTADOS_CANCELABLES = ("pendiente", "aprobada")


def cancelar(solicitud_id, usuario, reloj=ahora_utc):
    """Cancela la solicitud del propio usuario y la devuelve."""
    usuario_id = usuario.id
    try:
        reserva = (
            repositories.buscar_por_id_para_decidir(solicitud_id)
            if 0 < solicitud_id <= ID_MAXIMO
            else None
        )
        if reserva is None:
            raise SolicitudNoEncontrada()
        # Regla para todos los roles, incluido `admin`.
        if reserva.solicitante_id != usuario_id:
            raise PermisoInsuficiente()
        estado_anterior = reserva.estado
        if estado_anterior not in ESTADOS_CANCELABLES:
            raise TransicionInvalida()
        # Una reserva que empieza en el instante actual ya comenzó.
        if reserva.inicio_utc <= reloj():
            raise ReservaIniciada()

        repositories.registrar_decision(reserva, "cancelada")
        repositorio_historial.registrar(
            db.session, reserva, estado_anterior, "cancelada", usuario, reloj=reloj
        )
        repositories.desvincular(reserva)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return reserva
