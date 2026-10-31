"""Pruebas del modelo `Espacio` y de la migración de `espacios` (tarea 1.1)."""

from contextlib import contextmanager

from sqlalchemy import CheckConstraint, DateTime, create_engine, inspect, text
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateIndex

from backend.app.extensions import Base
from backend.app.models import Espacio

CHECKS_ESPERADOS = {"ck_espacios_tipo", "ck_espacios_capacidad", "ck_espacios_estado"}


@contextmanager
def _conectar(url):
    motor = create_engine(url)
    try:
        with motor.connect() as conexion:
            yield conexion
    finally:
        motor.dispose()


def _definicion_del_indice_del_modelo():
    indice = next(i for i in Espacio.__table__.indexes if i.name == "ux_espacios_nombre")
    return str(CreateIndex(indice).compile(dialect=postgresql.dialect()))


def test_el_modelo_declara_la_tabla_espacios_con_sus_restricciones():
    tabla = Base.metadata.tables["espacios"]
    assert tabla is Espacio.__table__
    for nombre in ("nombre", "tipo", "capacidad", "estado", "creado_en", "actualizado_en"):
        assert tabla.c[nombre].nullable is False
    assert tabla.c.estado.server_default.arg == "activo"
    for nombre in ("creado_en", "actualizado_en"):
        assert isinstance(tabla.c[nombre].type, DateTime)
        assert tabla.c[nombre].type.timezone is True

    checks = {r.name for r in tabla.constraints if isinstance(r, CheckConstraint)}
    assert checks == CHECKS_ESPERADOS

    # El índice funcional se declara como expresión, no como columna literal.
    ddl = _definicion_del_indice_del_modelo()
    assert "CREATE UNIQUE INDEX ux_espacios_nombre ON espacios (lower(btrim(nombre)))" in ddl


def test_upgrade_downgrade_y_upgrade_de_la_tabla_espacios(esquema, migrar, test_database_url):
    # Revierte hasta la revisión anterior a `espacios` (y las que dependen de ella).
    migrar("downgrade", "0002_correo_lower_unico")
    with _conectar(test_database_url) as conexion:
        assert "espacios" not in inspect(conexion).get_table_names()
        assert {"roles", "usuarios"} <= set(inspect(conexion).get_table_names())

    migrar("upgrade", "head")
    with _conectar(test_database_url) as conexion:
        assert "espacios" in inspect(conexion).get_table_names()


def test_el_esquema_tiene_los_tres_check_y_el_indice_unico_funcional(esquema, test_database_url):
    with _conectar(test_database_url) as conexion:
        checks = dict(
            conexion.execute(
                text(
                    "SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint "
                    "WHERE conrelid = 'espacios'::regclass AND contype = 'c'"
                )
            ).all()
        )
        indices = dict(
            conexion.execute(
                text("SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'espacios'")
            ).all()
        )
        estado_por_defecto = conexion.execute(
            text(
                "SELECT column_default FROM information_schema.columns "
                "WHERE table_name = 'espacios' AND column_name = 'estado'"
            )
        ).scalar_one()

    assert set(checks) == CHECKS_ESPERADOS
    for valor in ("laboratorio", "auditorio", "sala_de_computo"):
        assert f"'{valor}'" in checks["ck_espacios_tipo"]
    assert "capacidad > 0" in checks["ck_espacios_capacidad"]
    for valor in ("activo", "inactivo"):
        assert f"'{valor}'" in checks["ck_espacios_estado"]
    assert "'activo'" in estado_por_defecto

    assert indices["ux_espacios_nombre"] == (
        "CREATE UNIQUE INDEX ux_espacios_nombre ON public.espacios "
        "USING btree (lower(btrim(nombre)))"
    )
