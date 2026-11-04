"""Modelo `EntradaHistorial`: registro de los cambios de estado de una reserva.

Change `cancelacion-historial`. `espacio_id` es una copia del espacio de la
reserva en el momento del cambio, para filtrar sin unir tablas. `estado_anterior`
es nulo si y solo si el estado nuevo es `pendiente` (la creación). La tabla es
inmutable: un disparador, creado en la migración 0009, rechaza `UPDATE` y `DELETE`.
"""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..extensions import Base

_CATALOGO_SQL = "('pendiente', 'aprobada', 'rechazada', 'cancelada')"


class EntradaHistorial(Base):
    __tablename__ = "historial_reservas"
    __table_args__ = (
        CheckConstraint(
            f"estado_anterior IN {_CATALOGO_SQL}", name="ck_historial_reservas_estado_anterior"
        ),
        CheckConstraint(
            f"estado_nuevo IN {_CATALOGO_SQL}", name="ck_historial_reservas_estado_nuevo"
        ),
        CheckConstraint(
            "(estado_anterior IS NULL) = (estado_nuevo = 'pendiente')",
            name="ck_historial_reservas_creacion",
        ),
        Index("ix_historial_reservas_reserva_id", "reserva_id"),
        Index("ix_historial_reservas_espacio_id", "espacio_id"),
        Index("ix_historial_reservas_fecha_utc", "fecha_utc"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    reserva_id: Mapped[int] = mapped_column(
        ForeignKey("reservas.id", name="fk_historial_reservas_reserva_id_reservas"), nullable=False
    )
    espacio_id: Mapped[int] = mapped_column(Integer, nullable=False)
    estado_anterior: Mapped[str | None] = mapped_column(Text, nullable=True)
    estado_nuevo: Mapped[str] = mapped_column(Text, nullable=False)
    actor_id: Mapped[int] = mapped_column(
        ForeignKey("usuarios.id", name="fk_historial_reservas_actor_id_usuarios"), nullable=False
    )
    fecha_utc: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
