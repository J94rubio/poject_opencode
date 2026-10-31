"""Modelo `Usuario` (design.md, D3).

Cada usuario tiene un único rol (`rol_id`, no nulo) y las marcas de tiempo se
guardan como `TIMESTAMP WITH TIME ZONE` en UTC.
"""

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..extensions import Base


def ahora_utc():
    return datetime.now(timezone.utc)


class Usuario(Base):
    __tablename__ = "usuarios"
    __table_args__ = (
        UniqueConstraint("correo", name="uq_usuarios_correo"),
        Index("ix_usuarios_rol_id", "rol_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(120), nullable=False)
    correo: Mapped[str] = mapped_column(String(254), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    rol_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id", name="fk_usuarios_rol_id_roles"), nullable=False
    )
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=ahora_utc
    )
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=ahora_utc, onupdate=ahora_utc
    )

    rol: Mapped["Rol"] = relationship(back_populates="usuarios")  # noqa: F821
