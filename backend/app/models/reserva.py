"""Modelo `Reserva`: solicitudes de reserva de espacios (change `reservas-disponibilidad`).

Las fechas se guardan como `TIMESTAMP WITH TIME ZONE` en UTC y el rango es
semiabierto `[inicio_utc, fin_utc)`. La base impone el catálogo cerrado de
estados y `fin_utc > inicio_utc` con `CHECK`, y la restricción de exclusión
`ex_reservas_aprobadas_sin_solape` impide dos reservas `aprobada` solapadas
del mismo espacio (requiere la extensión `btree_gist`).

La restricción y los índices con expresiones se declaran con `text` para que
el DDL del modelo coincida exactamente con el de las migraciones 0005 y 0006.
"""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Text, text
from sqlalchemy.dialects.postgresql import ExcludeConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..extensions import Base

ESTADOS_DE_RESERVA = ("pendiente", "aprobada", "rechazada", "cancelada")

# Rango semiabierto de una reserva, como expresión SQL.
RANGO_SQL = "tstzrange(inicio_utc, fin_utc, '[)')"


class Reserva(Base):
    __tablename__ = "reservas"
    __table_args__ = (
        CheckConstraint(
            "estado IN ('pendiente', 'aprobada', 'rechazada', 'cancelada')",
            name="ck_reservas_estado",
        ),
        CheckConstraint("fin_utc > inicio_utc", name="ck_reservas_rango"),
        ExcludeConstraint(
            ("espacio_id", "="),
            (text(RANGO_SQL), "&&"),
            name="ex_reservas_aprobadas_sin_solape",
            using="gist",
            where=text("estado = 'aprobada'"),
        ),
        Index(
            "ix_reservas_espacio_rango",
            "espacio_id",
            text(RANGO_SQL),
            postgresql_using="gist",
        ),
        Index("ix_reservas_solicitante_id", "solicitante_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    espacio_id: Mapped[int] = mapped_column(
        ForeignKey("espacios.id", name="fk_reservas_espacio_id_espacios"), nullable=False
    )
    solicitante_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", name="fk_reservas_solicitante_id_usuarios"), nullable=False
    )
    inicio_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fin_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    estado: Mapped[str] = mapped_column(
        Text, nullable=False, default="pendiente", server_default="pendiente"
    )
