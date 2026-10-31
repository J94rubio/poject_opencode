"""Tabla espacios con sus CHECK y el índice único funcional (design.md, D2).

Revision ID: 0003_espacios
Revises: 0002_correo_lower_unico
Create Date: 2026-10-31
"""

from alembic import op
import sqlalchemy as sa

revision = "0003_espacios"
down_revision = "0002_correo_lower_unico"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "espacios",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.Text(), nullable=False),
        sa.Column("tipo", sa.Text(), nullable=False),
        sa.Column("capacidad", sa.Integer(), nullable=False),
        sa.Column("estado", sa.Text(), nullable=False, server_default="activo"),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "tipo IN ('laboratorio', 'auditorio', 'sala_de_computo')",
            name="ck_espacios_tipo",
        ),
        sa.CheckConstraint("capacidad > 0", name="ck_espacios_capacidad"),
        sa.CheckConstraint("estado IN ('activo', 'inactivo')", name="ck_espacios_estado"),
    )
    op.create_index(
        "ux_espacios_nombre",
        "espacios",
        [sa.text("lower(btrim(nombre))")],
        unique=True,
    )


def downgrade():
    op.drop_index("ux_espacios_nombre", table_name="espacios")
    op.drop_table("espacios")
