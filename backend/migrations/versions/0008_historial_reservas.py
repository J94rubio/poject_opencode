"""Tabla `historial_reservas` (tarea 1.1 de `cancelacion-historial`).

El `downgrade` borra también la función del disparador de la migración 0009, de
modo que retirar la tabla no deja ningún objeto del historial en la base.

Revision ID: 0008_historial_reservas
Revises: 0007_reservas_motivo_rechazo
Create Date: 2026-11-04
"""

from alembic import op
import sqlalchemy as sa

revision = "0008_historial_reservas"
down_revision = "0007_reservas_motivo_rechazo"
branch_labels = None
depends_on = None

CATALOGO_SQL = "('pendiente', 'aprobada', 'rechazada', 'cancelada')"


def upgrade():
    op.create_table(
        "historial_reservas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "reserva_id",
            sa.Integer(),
            sa.ForeignKey("reservas.id", name="fk_historial_reservas_reserva_id_reservas"),
            nullable=False,
        ),
        sa.Column("espacio_id", sa.Integer(), nullable=False),
        sa.Column("estado_anterior", sa.Text(), nullable=True),
        sa.Column("estado_nuevo", sa.Text(), nullable=False),
        sa.Column(
            "actor_id",
            sa.Integer(),
            sa.ForeignKey("usuarios.id", name="fk_historial_reservas_actor_id_usuarios"),
            nullable=False,
        ),
        sa.Column("fecha_utc", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            f"estado_anterior IN {CATALOGO_SQL}", name="ck_historial_reservas_estado_anterior"
        ),
        sa.CheckConstraint(
            f"estado_nuevo IN {CATALOGO_SQL}", name="ck_historial_reservas_estado_nuevo"
        ),
        sa.CheckConstraint(
            "(estado_anterior IS NULL) = (estado_nuevo = 'pendiente')",
            name="ck_historial_reservas_creacion",
        ),
    )
    op.create_index("ix_historial_reservas_reserva_id", "historial_reservas", ["reserva_id"])
    op.create_index("ix_historial_reservas_espacio_id", "historial_reservas", ["espacio_id"])
    op.create_index("ix_historial_reservas_fecha_utc", "historial_reservas", ["fecha_utc"])


def downgrade():
    op.drop_table("historial_reservas")
    op.execute("DROP FUNCTION IF EXISTS historial_reservas_inmutable()")
