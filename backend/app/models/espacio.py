"""Modelo `Espacio`: catálogo de espacios académicos (design.md, D2).

El nombre es único sin distinguir mayúsculas ni espacios exteriores gracias al
índice único funcional `lower(btrim(nombre))`; el tipo, la capacidad y el
estado se restringen con `CHECK`. Las marcas de tiempo se guardan como
`TIMESTAMP WITH TIME ZONE` en UTC.
"""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Index, Integer, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from ..extensions import Base
from .usuario import ahora_utc

TIPOS_DE_ESPACIO = ("laboratorio", "auditorio", "sala_de_computo")
ESTADOS_DE_ESPACIO = ("activo", "inactivo")


class Espacio(Base):
    __tablename__ = "espacios"
    __table_args__ = (
        CheckConstraint(
            "tipo IN ('laboratorio', 'auditorio', 'sala_de_computo')",
            name="ck_espacios_tipo",
        ),
        CheckConstraint("capacidad > 0", name="ck_espacios_capacidad"),
        CheckConstraint("estado IN ('activo', 'inactivo')", name="ck_espacios_estado"),
        Index("ux_espacios_nombre", text("lower(btrim(nombre))"), unique=True),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(Text, nullable=False)
    tipo: Mapped[str] = mapped_column(Text, nullable=False)
    capacidad: Mapped[int] = mapped_column(Integer, nullable=False)
    estado: Mapped[str] = mapped_column(
        Text, nullable=False, default="activo", server_default="activo"
    )
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=ahora_utc
    )
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=ahora_utc, onupdate=ahora_utc
    )
