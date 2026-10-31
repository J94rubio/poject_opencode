"""Configuración común de pytest.

Las pruebas se ejecutan siempre contra la base PostgreSQL dedicada
`reservas_test`, cuya URL se lee de `TEST_DATABASE_URL`. La clave JWT de
prueba se genera en cada sesión; nunca se guarda en el repositorio.
"""

import os
import secrets

import pytest

from backend.app import create_app
from backend.app.extensions import db


@pytest.fixture(scope="session")
def test_database_url():
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.exit("La variable de entorno TEST_DATABASE_URL no está definida.", returncode=1)
    return url


@pytest.fixture(scope="session")
def jwt_secret_key_de_prueba():
    return secrets.token_hex(32)


@pytest.fixture(autouse=True)
def entorno_de_pruebas(monkeypatch, test_database_url, jwt_secret_key_de_prueba):
    """Apunta la configuración del entorno a la base de pruebas en cada prueba."""
    monkeypatch.setenv("DATABASE_URL", test_database_url)
    monkeypatch.setenv("JWT_SECRET_KEY", jwt_secret_key_de_prueba)


@pytest.fixture
def app():
    app = create_app({"TESTING": True})
    yield app
    if db.engine is not None:
        db.engine.dispose()


@pytest.fixture
def client(app):
    return app.test_client()
