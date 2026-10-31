"""Pruebas de la app factory (tarea 1.5)."""

from backend.app.auth.errors import ErrorDeDominio
from backend.app.extensions import db


def test_la_conexion_a_postgresql_responde_a_la_consulta_de_comprobacion(app):
    assert db.comprobar_conexion() == 1


def test_las_pruebas_usan_la_base_reservas_test(app):
    with db.engine.connect() as conexion:
        assert conexion.exec_driver_sql("SELECT current_database()").scalar_one() == "reservas_test"


def test_registra_los_blueprints_de_los_modulos(app):
    assert {"auth", "usuarios"} <= set(app.blueprints)


def test_registra_el_manejador_de_errores_de_dominio(app):
    @app.route("/_prueba/error")
    def _ruta_con_error():
        raise ErrorDeDominio()

    respuesta = app.test_client().get("/_prueba/error")

    assert respuesta.status_code == 400
    assert respuesta.get_json() == {
        "error": {"codigo": "datos_invalidos", "mensaje": "Los datos enviados no son válidos."}
    }
