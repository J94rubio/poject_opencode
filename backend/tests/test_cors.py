"""Pruebas de CORS para el origen de desarrollo del frontend (tarea 1.7)."""

import pytest

from backend.app import create_app

ORIGEN_FRONTEND = "http://localhost:5173"
ORIGEN_NO_PERMITIDO = "http://sitio-no-permitido.example"


@pytest.fixture
def app_con_cors(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", f"{ORIGEN_FRONTEND}, http://127.0.0.1:5173")
    app = create_app({"TESTING": True})

    # Ruta registrada únicamente en los tests: aún no existe ninguna ruta real.
    @app.route("/api/_prueba/cors")
    def _ruta_de_prueba():
        return {"ok": True}

    return app


def test_cors_origins_se_lee_del_entorno_como_lista(app_con_cors):
    assert app_con_cors.config["CORS_ORIGINS"] == [ORIGEN_FRONTEND, "http://127.0.0.1:5173"]


def test_sin_cors_origins_no_se_permite_ningun_origen(monkeypatch):
    monkeypatch.delenv("CORS_ORIGINS", raising=False)
    app = create_app({"TESTING": True})

    assert app.config["CORS_ORIGINS"] == []


def test_el_origen_del_frontend_puede_llamar_al_backend(app_con_cors):
    respuesta = app_con_cors.test_client().get(
        "/api/_prueba/cors", headers={"Origin": ORIGEN_FRONTEND}
    )

    assert respuesta.status_code == 200
    assert respuesta.headers.get("Access-Control-Allow-Origin") == ORIGEN_FRONTEND


def test_preflight_del_frontend_permite_la_cabecera_authorization(app_con_cors):
    respuesta = app_con_cors.test_client().options(
        "/api/_prueba/cors",
        headers={
            "Origin": ORIGEN_FRONTEND,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization, Content-Type",
        },
    )

    assert respuesta.headers.get("Access-Control-Allow-Origin") == ORIGEN_FRONTEND
    permitidas = respuesta.headers.get("Access-Control-Allow-Headers", "").lower()
    assert "authorization" in permitidas
    assert "content-type" in permitidas


def test_un_origen_no_listado_no_recibe_permiso_cors(app_con_cors):
    respuesta = app_con_cors.test_client().get(
        "/api/_prueba/cors", headers={"Origin": ORIGEN_NO_PERMITIDO}
    )

    assert "Access-Control-Allow-Origin" not in respuesta.headers
