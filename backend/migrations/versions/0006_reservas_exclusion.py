"""Restricción de exclusión de reservas aprobadas e índices (tarea 1.3).

La restricción impide, solo entre filas `aprobada`, dos reservas del mismo
espacio con rangos semiabiertos `[inicio_utc, fin_utc)` solapados. Las
expresiones coinciden exactamente con las declaradas en `app/models/reserva.py`.

Revision ID: 0006_reservas_exclusion
Revises: 0005_reservas
Create Date: 2026-10-31
"""

from alembic import op
import sqlalchemy as sa

revision = "0006_reservas_exclusion"
down_revision = "0005_reservas"
branch_labels = None
depends_on = None

RANGO_SQL = "tstzrange(inicio_utc, fin_utc, '[)')"


def upgrade():
    op.execute(
        "ALTER TABLE reservas ADD CONSTRAINT ex_reservas_aprobadas_sin_solape "
        f"EXCLUDE USING gist (espacio_id WITH =, {RANGO_SQL} WITH &&) "
        "WHERE (estado = 'aprobada')"
    )
    op.create_index(
        "ix_reservas_espacio_rango",
        "reservas",
        ["espacio_id", sa.text(RANGO_SQL)],
        postgresql_using="gist",
    )
    op.create_index("ix_reservas_solicitante_id", "reservas", ["solicitante_id"])


def downgrade():
    op.drop_index("ix_reservas_solicitante_id", table_name="reservas")
    op.drop_index("ix_reservas_espacio_rango", table_name="reservas")
    op.drop_constraint("ex_reservas_aprobadas_sin_solape", "reservas")
