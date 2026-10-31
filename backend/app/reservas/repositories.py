"""Repositorio de reservas: acceso a datos con SQLAlchemy.

No contiene reglas de negocio ni confirma transacciones: eso corresponde a la
capa de servicios. Los rangos son semiabiertos `[inicio_utc, fin_utc)` y el
solapamiento se evalúa con el operador `&&` de `tstzrange`, la misma
expresión que usan la restricción de exclusión y el índice
`ix_reservas_espacio_rango`.
"""

from sqlalchemy import func, literal_column, select

from ..extensions import db
from ..models import Reserva

# Límites del rango semiabierto `[)` como literal SQL fijo.
_LIMITES = literal_column("'[)'")


def _rango(inicio, fin):
    return func.tstzrange(inicio, fin, _LIMITES)


def crear(espacio_id, solicitante_id, inicio_utc, fin_utc, estado="pendiente"):
    """Inserta una reserva. El servicio solo crea `pendiente`; las pruebas
    siembran otros estados directamente (la aprobación llega en otro change)."""
    reserva = Reserva(
        espacio_id=espacio_id,
        solicitante_id=solicitante_id,
        inicio_utc=inicio_utc,
        fin_utc=fin_utc,
        estado=estado,
    )
    db.session.add(reserva)
    db.session.flush()
    return reserva


def buscar_por_id(reserva_id):
    return db.session.get(Reserva, reserva_id)


def _ordenadas(consulta):
    return db.session.execute(
        consulta.order_by(Reserva.inicio_utc, Reserva.id)
    ).scalars().all()


def listar_por_solicitante(solicitante_id):
    """Reservas del solicitante, por inicio ascendente y luego por id."""
    return _ordenadas(select(Reserva).where(Reserva.solicitante_id == solicitante_id))


def listar_todas():
    """Todas las reservas, por inicio ascendente y luego por id."""
    return _ordenadas(select(Reserva))


def listar_aprobadas_por_espacio_y_rango(espacio_id, inicio_utc, fin_utc):
    """Reservas `aprobada` del espacio cuyo rango se solapa con `[inicio_utc, fin_utc)`.

    Se devuelven completas, sin recortar; las que solo tocan un extremo del
    rango no se solapan y no se incluyen.
    """
    return _ordenadas(
        select(Reserva).where(
            Reserva.espacio_id == espacio_id,
            Reserva.estado == "aprobada",
            _rango(Reserva.inicio_utc, Reserva.fin_utc).op("&&")(_rango(inicio_utc, fin_utc)),
        )
    )
