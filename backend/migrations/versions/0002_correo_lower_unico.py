"""Índice único funcional sobre lower(correo) (design.md, D3).

Revision ID: 0002_correo_lower_unico
Revises: 0001_roles_y_usuarios
Create Date: 2026-10-30
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_correo_lower_unico"
down_revision = "0001_roles_y_usuarios"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        "uq_usuarios_correo_lower",
        "usuarios",
        [sa.text("lower(correo)")],
        unique=True,
    )


def downgrade():
    op.drop_index("uq_usuarios_correo_lower", table_name="usuarios")
