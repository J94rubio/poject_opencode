"""Entorno de Alembic.

La URL de la base de datos se lee únicamente de la variable de entorno
`DATABASE_URL`; nunca se escribe en el código ni se muestra en la salida.
"""

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine

from backend.app.extensions import Base
from backend.app import models  # noqa: F401  (registra los modelos en los metadatos)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _url_de_la_base():
    url = os.environ.get("DATABASE_URL", "")
    if not url.strip():
        raise RuntimeError(
            "La variable de entorno DATABASE_URL es obligatoria para ejecutar las migraciones."
        )
    return url


def run_migrations_offline():
    context.configure(
        url=_url_de_la_base(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    motor = create_engine(_url_de_la_base())
    try:
        with motor.connect() as conexion:
            context.configure(connection=conexion, target_metadata=target_metadata)
            with context.begin_transaction():
                context.run_migrations()
    finally:
        motor.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
