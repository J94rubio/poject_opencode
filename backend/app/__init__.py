"""Creación de la aplicación Flask (app factory)."""

from flask import Flask
from flask_cors import CORS

from .auth.errors import registrar_manejadores_errores
from .auth.routes import bp as auth_bp
from .config import cargar_config
from .extensions import db
from .usuarios.routes import bp as usuarios_bp


def create_app(config=None):
    """Crea la app con la configuración del entorno.

    `config` permite sobrescribir valores ya cargados (por ejemplo, la URL de
    la base de pruebas); la configuración del entorno se valida siempre.
    """
    app = Flask(__name__)
    app.config.from_mapping(cargar_config())
    if config:
        app.config.from_mapping(config)

    db.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})

    app.register_blueprint(auth_bp)
    app.register_blueprint(usuarios_bp)

    registrar_manejadores_errores(app)

    return app
