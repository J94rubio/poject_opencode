"""Motivo de rechazo de las reservas (tarea 1.1 de `aprobacion-reservas`).

Añade la columna `motivo_rechazo` y el `CHECK` que exige motivo cuando el estado
es `rechazada`. La restricción de exclusión de reservas aprobadas no cambia.

Revision ID: 0007_reservas_motivo_rechazo
Revises: 0006_reservas_exclusion
Create Date: 2026-11-04
"""

from alembic import op
import sqlalchemy as sa

revision = "0007_reservas_motivo_rechazo"
down_revision = "0006_reservas_exclusion"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("reservas", sa.Column("motivo_rechazo", sa.Text(), nullable=True))
    op.create_check_constraint(
        "ck_reservas_motivo_rechazo",
        "reservas",
        "estado <> 'rechazada' OR motivo_rechazo IS NOT NULL",
    )


def downgrade():
    op.drop_constraint("ck_reservas_motivo_rechazo", "reservas", type_="check")
    op.drop_column("reservas", "motivo_rechazo")
