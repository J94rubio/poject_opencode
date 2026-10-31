"""Extensiones de la aplicación: acceso a la base de datos con SQLAlchemy.

El esquema y las migraciones se gestionan con Alembic (`backend/migrations`).
"""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import scoped_session, sessionmaker


class BaseDeDatos:
    """Motor y sesión de SQLAlchemy ligados a la app Flask."""

    def __init__(self):
        self.engine = None
        self.session = scoped_session(sessionmaker())

    def init_app(self, app):
        url = app.config.get("DATABASE_URL")
        if url:
            self.engine = create_engine(url, pool_pre_ping=True)
            self.session.configure(bind=self.engine)
        app.extensions["db"] = self

        @app.teardown_appcontext
        def _cerrar_sesion(_exc):
            self.session.remove()

    def comprobar_conexion(self):
        """Ejecuta una consulta de comprobación y devuelve su resultado."""
        if self.engine is None:
            raise RuntimeError("La base de datos no está configurada (DATABASE_URL).")
        with self.engine.connect() as conexion:
            return conexion.execute(text("SELECT 1")).scalar_one()


db = BaseDeDatos()
