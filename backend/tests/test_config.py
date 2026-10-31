"""Pruebas de la configuración leída del entorno (tarea 1.3)."""

import secrets

import pytest

from backend.app import create_app
from backend.app.config import ConfigError

# Variantes de entorno de ejecución: ninguna debe permitir arrancar sin clave.
ENTORNOS = [
    {},
    {"FLASK_DEBUG": "1"},
    {"FLASK_DEBUG": "0"},
]


def _clave_de_prueba():
    return secrets.token_hex(32)


@pytest.mark.parametrize("entorno", ENTORNOS)
def test_arranque_sin_jwt_secret_key_falla_con_mensaje_explicito(monkeypatch, entorno):
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    for nombre, valor in entorno.items():
        monkeypatch.setenv(nombre, valor)

    with pytest.raises(ConfigError, match="JWT_SECRET_KEY"):
        create_app()


@pytest.mark.parametrize("valor_vacio", ["", "   "])
@pytest.mark.parametrize("entorno", ENTORNOS)
def test_arranque_con_jwt_secret_key_vacia_falla_con_mensaje_explicito(
    monkeypatch, entorno, valor_vacio
):
    monkeypatch.setenv("JWT_SECRET_KEY", valor_vacio)
    for nombre, valor in entorno.items():
        monkeypatch.setenv(nombre, valor)

    with pytest.raises(ConfigError, match="JWT_SECRET_KEY"):
        create_app()


def test_configuracion_por_defecto(monkeypatch):
    clave = _clave_de_prueba()
    monkeypatch.setenv("JWT_SECRET_KEY", clave)
    monkeypatch.delenv("JWT_ACCESS_TOKEN_MINUTES", raising=False)

    app = create_app()

    assert app.config["JWT_SECRET_KEY"] == clave
    assert app.config["JWT_ACCESS_TOKEN_MINUTES"] == 60
    assert app.config["PASSWORD_MIN_LENGTH"] == 8


def test_vigencia_del_token_configurable_desde_el_entorno(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", _clave_de_prueba())
    monkeypatch.setenv("JWT_ACCESS_TOKEN_MINUTES", "15")

    app = create_app()

    assert app.config["JWT_ACCESS_TOKEN_MINUTES"] == 15


def test_url_de_base_de_datos_leida_del_entorno(monkeypatch):
    url_ficticia = "postgresql+psycopg://usuario@localhost/base_ficticia"
    monkeypatch.setenv("JWT_SECRET_KEY", _clave_de_prueba())
    monkeypatch.setenv("DATABASE_URL", url_ficticia)

    app = create_app()

    assert app.config["DATABASE_URL"] == url_ficticia
