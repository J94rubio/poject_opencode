"""Extensión btree_gist (change `reservas-disponibilidad`, tarea 1.1).

Necesaria para combinar `espacio_id WITH =` con un rango en un índice gist
(restricción de exclusión de la migración 0006).

Revision ID: 0004_btree_gist
Revises: 0003_espacios
Create Date: 2026-10-31
"""

from alembic import op

revision = "0004_btree_gist"
down_revision = "0003_espacios"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")


def downgrade():
    op.execute("DROP EXTENSION IF EXISTS btree_gist")
