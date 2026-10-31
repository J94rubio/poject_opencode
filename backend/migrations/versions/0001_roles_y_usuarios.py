"""Tablas roles y usuarios, y catálogo de roles (design.md, D3).

Revision ID: 0001_roles_y_usuarios
Revises:
Create Date: 2026-10-30
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_roles_y_usuarios"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    roles = op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(30), nullable=False),
        sa.UniqueConstraint("nombre", name="uq_roles_nombre"),
    )
    op.create_table(
        "usuarios",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nombre", sa.String(120), nullable=False),
        sa.Column("correo", sa.String(254), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("rol_id", sa.Integer(), nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["rol_id"], ["roles.id"], name="fk_usuarios_rol_id_roles"),
        sa.UniqueConstraint("correo", name="uq_usuarios_correo"),
    )
    op.create_index("ix_usuarios_rol_id", "usuarios", ["rol_id"])

    # Datos de catálogo: los tres roles existen desde el primer despliegue.
    op.bulk_insert(
        roles,
        [{"nombre": "solicitante"}, {"nombre": "aprobador"}, {"nombre": "admin"}],
    )


def downgrade():
    op.drop_index("ix_usuarios_rol_id", table_name="usuarios")
    op.drop_table("usuarios")
    op.drop_table("roles")
