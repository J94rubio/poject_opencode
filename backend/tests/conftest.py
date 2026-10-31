"""Configuración común de pytest.

Las pruebas se ejecutan siempre contra la base PostgreSQL dedicada
`reservas_test`, cuya URL se lee de `TEST_DATABASE_URL`. La clave JWT de
prueba se genera en cada sesión; nunca se guarda en el repositorio.

El esquema de `reservas_test` se prepara una vez por sesión con las
migraciones de Alembic (`alembic downgrade base` + `alembic upgrade head`),
de modo que las pruebas de repositorio parten de un esquema creado desde cero.
"""

import os
import secrets
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import text

from backend.app import create_app
from backend.app.extensions import db

ALEMBIC_INI = Path(__file__).resolve().parent.parent / "alembic.ini"


@pytest.fixture(scope="session")
def test_database_url():
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.exit("La variable de entorno TEST_DATABASE_URL no está definida.", returncode=1)
    return url


@pytest.fixture(scope="session")
def jwt_secret_key_de_prueba():
    return secrets.token_hex(32)


@pytest.fixture(scope="session")
def migrar(test_database_url):
    """Ejecuta un comando de Alembic sobre reservas_test.

    `migrations/env.py` lee la URL de `DATABASE_URL`, que aquí se apunta
    temporalmente a `TEST_DATABASE_URL`.
    """
    config = Config(str(ALEMBIC_INI))

    def _migrar(accion, destino):
        with pytest.MonkeyPatch.context() as mp:
            mp.setenv("DATABASE_URL", test_database_url)
            getattr(command, accion)(config, destino)

    return _migrar


@pytest.fixture(scope="session")
def esquema(migrar):
    """Prepara el esquema de reservas_test con `alembic upgrade head`."""
    migrar("downgrade", "base")
    migrar("upgrade", "head")


@pytest.fixture(autouse=True)
def entorno_de_pruebas(monkeypatch, test_database_url, jwt_secret_key_de_prueba):
    """Apunta la configuración del entorno a la base de pruebas en cada prueba.

    La vigencia del token parte del valor por defecto (60 minutos), para que
    las pruebas sean deterministas; las que la cambian la fijan ellas mismas.
    """
    monkeypatch.setenv("DATABASE_URL", test_database_url)
    monkeypatch.setenv("JWT_SECRET_KEY", jwt_secret_key_de_prueba)
    monkeypatch.delenv("JWT_ACCESS_TOKEN_MINUTES", raising=False)


@pytest.fixture
def app():
    app = create_app({"TESTING": True})
    yield app
    if db.engine is not None:
        db.engine.dispose()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def sesion(esquema, app):
    """Sesión de base de datos sobre el esquema ya migrado.

    Al terminar la prueba se descartan los cambios pendientes y se vacía la
    tabla `usuarios`; el catálogo de roles se conserva.
    """
    with app.app_context():
        yield db.session
        db.session.rollback()
        db.session.execute(text("TRUNCATE usuarios RESTART IDENTITY"))
        db.session.commit()
