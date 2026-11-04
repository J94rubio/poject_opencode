"""Persistencia e inmutabilidad del historial (tareas 1.1 y 1.2 de `cancelacion-historial`).

Requisitos «Registro de cada cambio de estado» e «Inmutabilidad del historial» de
la spec `historial`. Todo se verifica contra `reservas_test`.
"""

from contextlib import contextmanager
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, inspect, select, text
from sqlalchemy.exc import DBAPIError, IntegrityError

from backend.app.extensions import Base
from backend.app.models import ESTADOS_DE_RESERVA, EntradaHistorial
from backend.app.reservas import repositories as repositorio_reservas

TABLA = "historial_reservas"
FUNCION = "historial_reservas_inmutable"
DISPARADOR = "tr_historial_reservas_inmutable"
ESQUEMA_DEL_MODELO = "modelo_historial_tmp"
CHECKS = {
    "ck_historial_reservas_estado_anterior",
    "ck_historial_reservas_estado_nuevo",
    "ck_historial_reservas_creacion",
}
INDICES = {
    "ix_historial_reservas_reserva_id": "reserva_id",
    "ix_historial_reservas_espacio_id": "espacio_id",
    "ix_historial_reservas_fecha_utc": "fecha_utc",
}
FECHA = datetime(2030, 1, 10, 8, tzinfo=timezone.utc)


@contextmanager
def _conectar(url):
    motor = create_engine(url)
    try:
        with motor.connect() as conexion:
            yield conexion
    finally:
        motor.dispose()


def _existe_funcion(conexion):
    return conexion.execute(
        text("SELECT count(*) FROM pg_proc WHERE proname = :nombre"), {"nombre": FUNCION}
    ).scalar_one() == 1


def _existe_disparador(conexion):
    return conexion.execute(
        text("SELECT count(*) FROM pg_trigger WHERE tgname = :nombre"), {"nombre": DISPARADOR}
    ).scalar_one() == 1


def _version(conexion):
    return conexion.execute(text("SELECT version_num FROM alembic_version")).scalar_one()


@pytest.fixture
def datos(sesion, crear_cuenta, nuevo_espacio):
    """Reserva y actor válidos; `campos` da una entrada correcta de creación."""
    espacio_id, actor_id = nuevo_espacio(), crear_cuenta("solicitante")
    reserva = repositorio_reservas.crear(
        espacio_id, actor_id, FECHA, FECHA.replace(hour=10)
    )
    sesion.commit()
    return {
        "reserva_id": reserva.id,
        "espacio_id": espacio_id,
        "estado_anterior": None,
        "estado_nuevo": "pendiente",
        "actor_id": actor_id,
        "fecha_utc": FECHA,
    }


def _entradas(sesion):
    sesion.rollback()
    return sesion.execute(select(EntradaHistorial)).scalars().all()


def _rechazada_por_la_base(sesion, campos):
    with pytest.raises(IntegrityError):
        sesion.add(EntradaHistorial(**campos))
        sesion.flush()
    assert _entradas(sesion) == []


# --- 1.1 Tabla ---------------------------------------------------------------


def test_el_esquema_de_la_tabla(esquema, test_database_url):
    with _conectar(test_database_url) as conexion:
        inspector = inspect(conexion)
        columnas = {c["name"]: c for c in inspector.get_columns(TABLA)}
        claves = {
            (tuple(c["constrained_columns"]), c["referred_table"])
            for c in inspector.get_foreign_keys(TABLA)
        }
        checks = {c["name"] for c in inspector.get_check_constraints(TABLA)}
        indices = {i["name"]: i["column_names"] for i in inspector.get_indexes(TABLA)}

    assert set(columnas) == {"id", "reserva_id", "espacio_id", "estado_anterior", "estado_nuevo",
                             "actor_id", "fecha_utc"}
    assert columnas["fecha_utc"]["type"].timezone is True
    assert columnas["estado_anterior"]["nullable"] is True
    for nombre in ("reserva_id", "espacio_id", "estado_nuevo", "actor_id", "fecha_utc"):
        assert columnas[nombre]["nullable"] is False
    assert claves == {(("reserva_id",), "reservas"), (("actor_id",), "usuarios")}
    assert checks == CHECKS
    assert indices == {nombre: [columna] for nombre, columna in INDICES.items()}


def test_el_ddl_del_modelo_coincide_con_el_de_las_migraciones(esquema, test_database_url):
    """El modelo, creado en un esquema temporal, declara las mismas restricciones e índices."""

    def _definiciones(conexion, esquema_):
        restricciones = dict(conexion.execute(
            text(
                "SELECT c.conname, pg_get_constraintdef(c.oid) FROM pg_constraint c "
                "JOIN pg_class t ON t.oid = c.conrelid "
                "JOIN pg_namespace n ON n.oid = t.relnamespace "
                "WHERE t.relname = :tabla AND n.nspname = :esquema AND c.contype = 'c'"
            ),
            {"tabla": TABLA, "esquema": esquema_},
        ).all())
        indices = {
            nombre: definicion.replace(f"{esquema_}.", "")
            for nombre, definicion in conexion.execute(
                text(
                    "SELECT indexname, indexdef FROM pg_indexes "
                    "WHERE tablename = :tabla AND schemaname = :esquema "
                    "AND indexname <> 'historial_reservas_pkey'"
                ),
                {"tabla": TABLA, "esquema": esquema_},
            ).all()
        }
        return restricciones, indices

    tablas = [Base.metadata.tables[n] for n in ("roles", "usuarios", "espacios", "reservas", TABLA)]
    with _conectar(test_database_url) as conexion:
        transaccion = conexion.begin()
        try:
            conexion.execute(text(f"CREATE SCHEMA {ESQUEMA_DEL_MODELO}"))
            conexion.execute(text(f"SET LOCAL search_path TO {ESQUEMA_DEL_MODELO}, public"))
            Base.metadata.create_all(conexion, tables=tablas, checkfirst=False)
            del_modelo = _definiciones(conexion, ESQUEMA_DEL_MODELO)
            de_las_migraciones = _definiciones(conexion, "public")
        finally:
            transaccion.rollback()

    assert del_modelo == de_las_migraciones


@pytest.mark.parametrize("campo", ["estado_nuevo", "estado_anterior"])
def test_un_estado_fuera_del_catalogo_es_rechazado(sesion, datos, campo):
    campos = {**datos, "estado_anterior": "pendiente", "estado_nuevo": "aprobada",
              campo: "confirmada"}
    _rechazada_por_la_base(sesion, campos)


@pytest.mark.parametrize("clave", ["reserva_id", "actor_id"])
def test_una_clave_foranea_inexistente_es_rechazada(sesion, datos, clave):
    _rechazada_por_la_base(sesion, {**datos, clave: 999_999})


@pytest.mark.parametrize(
    "anterior,nuevo",
    [(None, "aprobada"), (None, "rechazada"), (None, "cancelada"), ("pendiente", "pendiente"),
     ("aprobada", "pendiente")],
)
def test_una_combinacion_invalida_de_estados_es_rechazada(sesion, datos, anterior, nuevo):
    _rechazada_por_la_base(sesion, {**datos, "estado_anterior": anterior, "estado_nuevo": nuevo})


@pytest.mark.parametrize(
    "anterior,nuevo",
    [(None, "pendiente"), ("pendiente", "aprobada"), ("pendiente", "rechazada"),
     ("pendiente", "cancelada"), ("aprobada", "cancelada")],
)
def test_las_combinaciones_validas_se_aceptan(sesion, datos, anterior, nuevo):
    sesion.add(EntradaHistorial(**{**datos, "estado_anterior": anterior, "estado_nuevo": nuevo}))
    sesion.commit()
    assert [(e.estado_anterior, e.estado_nuevo) for e in _entradas(sesion)] == [(anterior, nuevo)]


def test_cada_estado_nuevo_del_catalogo_se_acepta(sesion, datos):
    for estado in ESTADOS_DE_RESERVA:
        anterior = None if estado == "pendiente" else "pendiente"
        sesion.add(EntradaHistorial(**{**datos, "estado_anterior": anterior,
                                       "estado_nuevo": estado}))
    sesion.commit()
    assert {e.estado_nuevo for e in _entradas(sesion)} == set(ESTADOS_DE_RESERVA)


def test_migraciones_paso_a_paso_con_downgrade_completo(esquema, migrar, test_database_url):
    """`downgrade -1` retira el disparador y su función; el siguiente, la tabla."""
    try:
        migrar("downgrade", "-1")  # 0009: disparador
        with _conectar(test_database_url) as conexion:
            assert TABLA in inspect(conexion).get_table_names()
            assert not _existe_disparador(conexion)
            assert not _existe_funcion(conexion)
            assert _version(conexion) == "0008_historial_reservas"

        migrar("downgrade", "-1")  # 0008: tabla
        with _conectar(test_database_url) as conexion:
            assert TABLA not in inspect(conexion).get_table_names()
            assert not _existe_funcion(conexion)
            assert _version(conexion) == "0007_reservas_motivo_rechazo"
    finally:
        # Las demás pruebas, y el estado final de reservas_test, necesitan head.
        migrar("upgrade", "head")

    with _conectar(test_database_url) as conexion:
        assert TABLA in inspect(conexion).get_table_names()
        assert _existe_disparador(conexion)
        assert _existe_funcion(conexion)
        assert _version(conexion) == "0009_historial_inmutable"


def test_el_downgrade_de_la_tabla_borra_tambien_la_funcion(esquema, migrar, test_database_url):
    """Aunque la función quedara huérfana, retirar la tabla no la deja en la base."""
    try:
        migrar("downgrade", "-1")
        with _conectar(test_database_url) as conexion:
            conexion.execute(text(
                f"CREATE FUNCTION {FUNCION}() RETURNS trigger LANGUAGE plpgsql "
                "AS $$ BEGIN RETURN NULL; END; $$"
            ))
            conexion.commit()
        migrar("downgrade", "-1")
        with _conectar(test_database_url) as conexion:
            assert not _existe_funcion(conexion)
    finally:
        migrar("upgrade", "head")


# --- 1.2 Inmutabilidad -------------------------------------------------------


@pytest.fixture
def entrada(sesion, datos):
    fila = EntradaHistorial(**datos)
    sesion.add(fila)
    sesion.commit()
    return fila.id


def _valores(sesion, entrada_id):
    sesion.rollback()
    return tuple(sesion.execute(
        select(EntradaHistorial.estado_anterior, EntradaHistorial.estado_nuevo,
               EntradaHistorial.fecha_utc).where(EntradaHistorial.id == entrada_id)
    ).one())


@pytest.mark.parametrize(
    "sentencia",
    [
        "UPDATE historial_reservas SET estado_nuevo = 'pendiente' WHERE id = :id",
        "UPDATE historial_reservas SET fecha_utc = now() WHERE id = :id",
    ],
    ids=["estado", "fecha"],
)
def test_un_update_directo_falla_y_la_entrada_conserva_sus_valores(sesion, entrada, sentencia):
    antes = _valores(sesion, entrada)

    with pytest.raises(DBAPIError) as error:
        sesion.execute(text(sentencia), {"id": entrada})
    assert "inmutable" in str(error.value.orig)

    assert _valores(sesion, entrada) == antes


def test_un_delete_directo_falla_y_la_entrada_sigue_existiendo(sesion, entrada):
    antes = _valores(sesion, entrada)

    with pytest.raises(DBAPIError) as error:
        sesion.execute(text("DELETE FROM historial_reservas WHERE id = :id"), {"id": entrada})
    assert "inmutable" in str(error.value.orig)

    assert _valores(sesion, entrada) == antes


def test_el_orm_tampoco_puede_modificar_ni_borrar_una_entrada(sesion, entrada):
    fila = sesion.get(EntradaHistorial, entrada)
    fila.estado_nuevo = "pendiente"
    fila.fecha_utc = FECHA.replace(year=2031)
    with pytest.raises(DBAPIError):
        sesion.flush()
    sesion.rollback()

    sesion.delete(sesion.get(EntradaHistorial, entrada))
    with pytest.raises(DBAPIError):
        sesion.flush()
    sesion.rollback()

    assert sesion.get(EntradaHistorial, entrada).fecha_utc == FECHA


def test_la_reserva_con_historial_no_se_puede_borrar(sesion, datos, entrada):
    with pytest.raises(IntegrityError):
        sesion.execute(text("DELETE FROM reservas WHERE id = :id"), {"id": datos["reserva_id"]})
    sesion.rollback()


def test_truncate_sigue_siendo_la_limpieza_de_las_pruebas(sesion, entrada):
    """El disparador no impide `TRUNCATE`: es el límite aceptado en design.md."""
    sesion.execute(text("TRUNCATE historial_reservas, reservas, usuarios, espacios RESTART IDENTITY"))
    sesion.commit()
    assert _entradas(sesion) == []
