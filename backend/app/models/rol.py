"""Modelo `Rol`: catálogo cerrado de roles del sistema (design.md, D3)."""

from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..extensions import Base

ROLES_DEL_CATALOGO = ("solicitante", "aprobador", "admin")


class Rol(Base):
    __tablename__ = "roles"
    __table_args__ = (UniqueConstraint("nombre", name="uq_roles_nombre"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(30), nullable=False)

    usuarios: Mapped[list["Usuario"]] = relationship(back_populates="rol")  # noqa: F821
