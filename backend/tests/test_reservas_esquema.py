"""Persistencia de reservas: migraciones, modelo y restricciones (tareas 1.1 a 1.3).

Requisitos «Catálogo de estados de una reserva» y «Garantía de integridad
contra solapamientos aprobados» de la spec `reservas`. Todo se verifica contra
`reservas_test`.
"""

from contextlib import contextmanager
from datetime import datetime, timezone

import pytest
from sqlalchemy import CheckConstraint, DateTime, create_engine, inspect, select, text
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import ExcludeConstraint
from sqlalchemy.exc import IntegrityError
from sqlalchemy.schema import CreateIndex, CreateTable

from backend.app.extensions import Base
from backend.app.models import ESTADOS_DE_RESERVA, Reserva

CHECKS_ESPERADOS = {"ck_reservas_estado", "ck_reservas_rango"}
EXCLUSION = "ex_reservas_aprobadas_sin_solape"
INDICES_ESPERADOS = {"ix_reservas_espacio_rango", "ix_reservas_solicitante_id"}
ESQUEMA_DEL_MODELO = "modelo_reservas_tmp"


@contextmanager
def _conectar(url):
    motor = create_engine(url)
    try:
        with motor.connect() as conexion:
            yield conexion
    finally:
        motor.dispose()


def _h(hora, minuto=0):
    return datetime(2026, 11, 3, hora, minuto, tzinfo=timezone.utc)


def _btree_gist_instalada(conexion):
    return conexion.execute(
        text("SELECT count(*) FROM pg_extension WHERE extname = 'btree_gist'")
    ).scalar_one() == 1


def _definiciones(conexion, esquema):
    """Restricciones de `reservas` (salvo PK y FK) e índices secundarios del esquema."""
    restricciones = dict(
        conexion.execute(
            text(
                "SELECT c.conname, pg_get_constraintdef(c.oid) FROM pg_constraint c "
                "JOIN pg_class t ON t.oid = c.conrelid "
                "JOIN pg_namespace n ON n.oid = t.relnamespace "
                "WHERE t.relname = 'reservas' AND n.nspname = :esquema "
                "AND c.contype IN ('c', 'x')"
            ),
            {"esquema": esquema},
        ).all()
    )
    indices = {
        nombre: definicion.replace(f"{esquema}.", "")
        for nombre, definicion in conexion.execute(
            text(
                "SELECT indexname, indexdef FROM pg_indexes "
                "WHERE tablename = 'reservas' AND schemaname = :esquema "
                "AND indexname NOT IN ('reservas_pkey', :exclusion)"
            ),
            {"esquema": esquema, "exclusion": EXCLUSION},
        ).all()
    }
    return restricciones, indices


# --- 1.1 Extensión btree_gist ------------------------------------------------


def test_la_extension_btree_gist_esta_instalada_en_reservas_test(esquema, test_database_url):
    with _conectar(test_database_url) as conexion:
        assert _btree_gist_instalada(conexion)


def test_downgrade_menos_uno_y_upgrade_head_paso_a_paso(esquema, migrar, test_database_url):
    """Cada `downgrade -1` revierte una migración del change y `upgrade head` las restaura."""
    migrar("downgrade", "-1")  # 0006: restricción de exclusión e índices
    with _conectar(test_database_url) as conexion:
        assert "reservas" in inspect(conexion).get_table_names()
        restricciones, indices = _definiciones(conexion, "public")
        assert EXCLUSION not in restricciones
        assert not INDICES_ESPERADOS & set(indices)

    migrar("downgrade", "-1")  # 0005: tabla reservas
    with _conectar(test_database_url) as conexion:
        assert "reservas" not in inspect(conexion).get_table_names()
        assert _btree_gist_instalada(conexion)

    migrar("downgrade", "-1")  # 0004: extensión btree_gist
    with _conectar(test_database_url) as conexion:
        assert not _btree_gist_instalada(conexion)
        assert {"roles", "usuarios", "espacios"} <= set(inspect(conexion).get_table_names())

    migrar("upgrade", "head")
    with _conectar(test_database_url) as conexion:
        assert _btree_gist_instalada(conexion)
        assert "reservas" in inspect(conexion).get_table_names()
        restricciones, indices = _definiciones(conexion, "public")
        assert EXCLUSION in restricciones
        assert INDICES_ESPERADOS == set(indices)


# --- 1.2 Tabla reservas -------------------------------------------------------


def test_el_modelo_declara_la_tabla_reservas():
    tabla = Base.metadata.tables["reservas"]
    assert tabla is Reserva.__table__
    for nombre in ("espacio_id", "solicitante_id", "inicio_utc", "fin_utc", "estado"):
        assert tabla.c[nombre].nullable is False
    for nombre in ("inicio_utc", "fin_utc"):
        assert isinstance(tabla.c[nombre].type, DateTime)
        assert tabla.c[nombre].type.timezone is True
    assert [c.target_fullname for c in tabla.c.espacio_id.foreign_keys] == ["espacios.id"]
    assert [c.target_fullname for c in tabla.c.solicitante_id.foreign_keys] == ["usuarios.id"]
    assert ESTADOS_DE_RESERVA == ("pendiente", "aprobada", "rechazada", "cancelada")
    checks = {r.name for r in tabla.constraints if isinstance(r, CheckConstraint)}
    assert checks == CHECKS_ESPERADOS


def test_el_esquema_de_la_tabla_reservas(esquema, test_database_url):
    with _conectar(test_database_url) as conexion:
        inspector = inspect(conexion)
        columnas = {c["name"]: c for c in inspector.get_columns("reservas")}
        claves = {
            (tuple(c["constrained_columns"]), c["referred_table"])
            for c in inspector.get_foreign_keys("reservas")
        }
        restricciones, _ = _definiciones(conexion, "public")

    assert set(columnas) == {"id", "espacio_id", "solicitante_id", "inicio_utc", "fin_utc",
                             "estado"}
    for nombre in ("inicio_utc", "fin_utc"):
        assert columnas[nombre]["type"].timezone is True
    assert claves == {(("espacio_id",), "espacios"), (("solicitante_id",), "usuarios")}
    for estado in ESTADOS_DE_RESERVA:
        assert f"'{estado}'" in restricciones["ck_reservas_estado"]
    assert "fin_utc > inicio_utc" in restricciones["ck_reservas_rango"]


@pytest.fixture
def ids(sesion, crear_cuenta, nuevo_espacio):
    return nuevo_espacio(), crear_cuenta("solicitante")


def _insertar_y_rechazar(sesion, **campos):
    with pytest.raises(IntegrityError):
        sesion.add(Reserva(**campos))
        sesion.flush()
    sesion.rollback()
    assert sesion.execute(select(Reserva)).scalars().all() == []


@pytest.mark.parametrize("estado", ["confirmada", "PENDIENTE", ""])
def test_un_estado_fuera_del_catalogo_es_rechazado(sesion, ids, estado):
    espacio_id, usuario_id = ids
    _insertar_y_rechazar(sesion, espacio_id=espacio_id, solicitante_id=usuario_id,
                         inicio_utc=_h(10), fin_utc=_h(12), estado=estado)


@pytest.mark.parametrize("fin", [_h(10), _h(9)], ids=["fin_igual", "fin_anterior"])
def test_un_rango_con_fin_igual_o_anterior_al_inicio_es_rechazado(sesion, ids, fin):
    espacio_id, usuario_id = ids
    _insertar_y_rechazar(sesion, espacio_id=espacio_id, solicitante_id=usuario_id,
                         inicio_utc=_h(10), fin_utc=fin, estado="pendiente")


@pytest.mark.parametrize("clave", ["espacio_id", "solicitante_id"])
def test_una_clave_foranea_inexistente_es_rechazada(sesion, ids, clave):
    espacio_id, usuario_id = ids
    campos = {"espacio_id": espacio_id, "solicitante_id": usuario_id,
              "inicio_utc": _h(10), "fin_utc": _h(12), "estado": "pendiente"}
    campos[clave] = 999_999
    _insertar_y_rechazar(sesion, **campos)


@pytest.mark.parametrize("estado", ESTADOS_DE_RESERVA)
def test_cada_estado_del_catalogo_se_acepta(sesion, ids, estado):
    espacio_id, usuario_id = ids
    sesion.add(Reserva(espacio_id=espacio_id, solicitante_id=usuario_id,
                       inicio_utc=_h(10), fin_utc=_h(12), estado=estado))
    sesion.commit()
    assert sesion.execute(select(Reserva.estado)).scalars().all() == [estado]


# --- 1.3 Restricción de exclusión e índices -----------------------------------


def test_el_modelo_declara_la_exclusion_y_los_indices_con_expresiones():
    tabla = Reserva.__table__
    dialecto = postgresql.dialect()
    assert any(isinstance(r, ExcludeConstraint) for r in tabla.constraints)
    # Se compila `CreateTable` y no `AddConstraint`: construir `AddConstraint`
    # desactiva en SQLAlchemy la emisión de la restricción dentro de `CREATE TABLE`
    # y alteraría el modelo para las pruebas siguientes.
    ddl = str(CreateTable(tabla).compile(dialect=dialecto))
    assert (
        f"CONSTRAINT {EXCLUSION} EXCLUDE USING gist (espacio_id WITH =, "
        "tstzrange(inicio_utc, fin_utc, '[)') WITH &&) WHERE (estado = 'aprobada')"
    ) in ddl

    indices = {i.name: str(CreateIndex(i).compile(dialect=dialecto)) for i in tabla.indexes}
    assert set(indices) == INDICES_ESPERADOS
    assert indices["ix_reservas_espacio_rango"] == (
        "CREATE INDEX ix_reservas_espacio_rango ON reservas "
        "USING gist (espacio_id, tstzrange(inicio_utc, fin_utc, '[)'))"
    )
    assert indices["ix_reservas_solicitante_id"] == (
        "CREATE INDEX ix_reservas_solicitante_id ON reservas (solicitante_id)"
    )


def test_el_esquema_contiene_la_exclusion_y_los_indices(esquema, test_database_url):
    with _conectar(test_database_url) as conexion:
        restricciones, indices = _definiciones(conexion, "public")

    assert set(restricciones) == CHECKS_ESPERADOS | {EXCLUSION}
    exclusion = restricciones[EXCLUSION]
    for fragmento in ("EXCLUDE USING gist", "espacio_id WITH =",
                      "tstzrange(inicio_utc, fin_utc, '[)'", "WITH &&", "'aprobada'"):
        assert fragmento in exclusion
    assert set(indices) == INDICES_ESPERADOS
    assert "USING gist (espacio_id, tstzrange(inicio_utc, fin_utc, '[)'" in (
        indices["ix_reservas_espacio_rango"]
    )
    assert "USING btree (solicitante_id)" in indices["ix_reservas_solicitante_id"]


def test_el_ddl_del_modelo_coincide_con_el_de_las_migraciones(esquema, test_database_url):
    """El modelo, creado en un esquema temporal, produce exactamente las mismas
    restricciones e índices que las migraciones en `public`."""
    tablas = [Base.metadata.tables[n] for n in ("roles", "usuarios", "espacios", "reservas")]
    with _conectar(test_database_url) as conexion:
        transaccion = conexion.begin()
        try:
            conexion.execute(text(f"CREATE SCHEMA {ESQUEMA_DEL_MODELO}"))
            conexion.execute(text(f"SET LOCAL search_path TO {ESQUEMA_DEL_MODELO}, public"))
            # Sin `checkfirst`: las tablas de `public` son visibles en el search_path.
            Base.metadata.create_all(conexion, tables=tablas, checkfirst=False)
            del_modelo = _definiciones(conexion, ESQUEMA_DEL_MODELO)
            de_las_migraciones = _definiciones(conexion, "public")
        finally:
            transaccion.rollback()

    assert del_modelo == de_las_migraciones
