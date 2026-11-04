"""Decisiones sobre solicitudes de reserva (spec `aprobaciones`; design.md de `aprobacion-reservas`).

`decidir` es la única función que cambia el estado por una decisión, para que
`cancelacion-historial` pueda registrarla después en un solo sitio. El permiso
lo resuelve el guard de la ruta; el resto de comprobaciones, en este orden:

- Aprobar: existencia, autoría, estado `pendiente`, vigencia, espacio activo y
  solapamiento.
- Rechazar: existencia, autoría, motivo y estado `pendiente`.

La solicitud se lee con `SELECT ... FOR UPDATE`, de modo que dos decisiones
sobre la misma solicitud se serializan y la segunda ve el estado ya cambiado.

Las aprobaciones de un mismo espacio se serializan además con un bloqueo de la
fila del espacio. Sin él, dos actualizaciones simultáneas pueden esperarse entre
sí dentro de la restricción de exclusión y PostgreSQL aborta una con un deadlock
(`40P01`), que llegaría al cliente como error interno. Con él, la segunda
aprobación ve la primera ya confirmada y responde `reserva_solapada`.

La restricción de exclusión sigue siendo la última barrera ante cualquier otra
escritura: su violación se traduce a `reserva_solapada`. Cualquier fallo deshace
la transacción y libera los bloqueos.
"""

from sqlalchemy.exc import IntegrityError

from ..auth.errors import (
    DatosInvalidos,
    EspacioInactivo,
    PermisoInsuficiente,
    ReservaSolapada,
    SolicitudNoEncontrada,
    SolicitudVencida,
    TransicionInvalida,
)
from ..espacios import repositories as repositorio_espacios
from ..extensions import db
from ..models.usuario import ahora_utc
from ..reservas import repositories
from ..reservas.services import ID_MAXIMO

APROBAR = "aprobar"
RECHAZAR = "rechazar"

MOTIVO_LONGITUD_MAXIMA = 500

_SQLSTATE_EXCLUSION = "23P01"
_RESTRICCION_EXCLUSION = "ex_reservas_aprobadas_sin_solape"


def _validar_motivo(motivo):
    """Motivo recortado: texto no vacío de hasta 500 caracteres que PostgreSQL
    pueda almacenar (sin NUL ni sustitutos UTF-16 sueltos)."""
    if not isinstance(motivo, str):
        raise DatosInvalidos()
    recortado = motivo.strip()
    if not recortado or len(recortado) > MOTIVO_LONGITUD_MAXIMA or "\x00" in recortado:
        raise DatosInvalidos()
    try:
        recortado.encode("utf-8")
    except UnicodeEncodeError:
        raise DatosInvalidos() from None
    return recortado


def _exigir_pendiente(reserva):
    if reserva.estado != "pendiente":
        raise TransicionInvalida()


def _aprobar(reserva, reloj):
    _exigir_pendiente(reserva)
    # Una solicitud que empieza en el instante actual ya comenzó.
    if reserva.inicio_utc <= reloj():
        raise SolicitudVencida()
    if repositorio_espacios.bloquear_espacio(reserva.espacio_id).estado != "activo":
        raise EspacioInactivo()
    if repositories.listar_aprobadas_por_espacio_y_rango(
        reserva.espacio_id, reserva.inicio_utc, reserva.fin_utc
    ):
        raise ReservaSolapada()
    repositories.registrar_decision(reserva, "aprobada")


def _rechazar(reserva, motivo):
    motivo_valido = _validar_motivo(motivo)
    _exigir_pendiente(reserva)
    repositories.registrar_decision(reserva, "rechazada", motivo_valido)


def _es_violacion_de_exclusion(error):
    original = error.orig
    return (
        getattr(original, "sqlstate", None) == _SQLSTATE_EXCLUSION
        and original.diag.constraint_name == _RESTRICCION_EXCLUSION
    )


def decidir(solicitud_id, usuario, accion, motivo=None, reloj=ahora_utc):
    """Aplica la decisión `accion` del usuario sobre la solicitud y la devuelve."""
    if accion not in (APROBAR, RECHAZAR):
        raise ValueError(f"Acción de decisión desconocida: {accion!r}")

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
        if reserva.solicitante_id == usuario_id:
            raise PermisoInsuficiente()

        if accion == APROBAR:
            _aprobar(reserva, reloj)
        else:
            _rechazar(reserva, motivo)
        db.session.commit()
    except IntegrityError as error:
        db.session.rollback()
        if _es_violacion_de_exclusion(error):
            raise ReservaSolapada() from None
        raise
    except Exception:
        db.session.rollback()
        raise
    return reserva
