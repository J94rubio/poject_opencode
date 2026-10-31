"""Pruebas de las migraciones de Alembic (tarea 2.2)."""

from contextlib import contextmanager

from sqlalchemy import create_engine, inspect, text


@contextmanager
def _conectar(url):
    motor = create_engine(url)
    try:
        with motor.connect() as conexion:
            yield conexion
    finally:
        motor.dispose()


def test_upgrade_head_y_downgrade_base_sobre_una_base_vacia(esquema, migrar, test_database_url):
    migrar("downgrade", "base")
    with _conectar(test_database_url) as conexion:
        assert not {"roles", "usuarios"} & set(inspect(conexion).get_table_names())

    migrar("upgrade", "head")
    with _conectar(test_database_url) as conexion:
        inspector = inspect(conexion)
        assert {"roles", "usuarios"} <= set(inspector.get_table_names())

        claves = inspector.get_foreign_keys("usuarios")
        assert [(c["constrained_columns"], c["referred_table"]) for c in claves] == [
            (["rol_id"], "roles")
        ]
        assert "ix_usuarios_rol_id" in {i["name"] for i in inspector.get_indexes("usuarios")}

        columnas = {c["name"]: c for c in inspector.get_columns("usuarios")}
        for nombre in ("creado_en", "actualizado_en"):
            assert columnas[nombre]["type"].timezone is True

        roles = conexion.execute(text("SELECT nombre FROM roles ORDER BY id")).scalars().all()
        assert roles == ["solicitante", "aprobador", "admin"]
