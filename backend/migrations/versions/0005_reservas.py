"""Tabla reservas con sus claves foráneas y CHECK (tarea 1.2).

Revision ID: 0005_reservas
Revises: 0004_btree_gist
Create Date: 2026-10-31
"""

from alembic import op
import sqlalchemy as sa

revision = "0005_reservas"
down_revision = "0004_btree_gist"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "reservas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "espacio_id",
            sa.Integer(),
            sa.ForeignKey("espacios.id", name="fk_reservas_espacio_id_espacios"),
            nullable=False,
        ),
        sa.Column(
            "solicitante_id",
            sa.Integer(),
            sa.ForeignKey("usuarios.id", name="fk_reservas_solicitante_id_usuarios"),
            nullable=False,
        ),
        sa.Column("inicio_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fin_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("estado", sa.Text(), nullable=False, server_default="pendiente"),
        sa.CheckConstraint(
            "estado IN ('pendiente', 'aprobada', 'rechazada', 'cancelada')",
            name="ck_reservas_estado",
        ),
        sa.CheckConstraint("fin_utc > inicio_utc", name="ck_reservas_rango"),
    )


def downgrade():
    op.drop_table("reservas")
