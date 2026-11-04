"""Disparador de inmutabilidad del historial (tarea 1.2 de `cancelacion-historial`).

Rechaza con una excepción cualquier `UPDATE` o `DELETE` sobre `historial_reservas`.
`TRUNCATE` no activa disparadores de fila: es la limpieza de las pruebas y un límite
aceptado (design.md, «Risks / Trade-offs»).

Revision ID: 0009_historial_inmutable
Revises: 0008_historial_reservas
Create Date: 2026-11-04
"""

from alembic import op

revision = "0009_historial_inmutable"
down_revision = "0008_historial_reservas"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        CREATE FUNCTION historial_reservas_inmutable() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION 'historial_reservas es inmutable: % no permitido', TG_OP;
        END;
        $$
        """
    )
    op.execute(
        "CREATE TRIGGER tr_historial_reservas_inmutable "
        "BEFORE UPDATE OR DELETE ON historial_reservas "
        "FOR EACH ROW EXECUTE FUNCTION historial_reservas_inmutable()"
    )


def downgrade():
    op.execute("DROP TRIGGER tr_historial_reservas_inmutable ON historial_reservas")
    op.execute("DROP FUNCTION historial_reservas_inmutable()")
