"""Configuración de la aplicación leída de variables de entorno.

`JWT_SECRET_KEY` es obligatoria en todos los entornos: no tiene valor por
defecto ni valor de desarrollo en el código (design.md, D4).
"""

import os

JWT_ACCESS_TOKEN_MINUTES_POR_DEFECTO = 60

# Política de contraseñas (design.md): mínimo de 8 caracteres, sin reglas de
# composición. Cambiar este valor exige actualizar la spec `usuarios`.
PASSWORD_MIN_LENGTH = 8


class ConfigError(RuntimeError):
    """La configuración del entorno es incompleta o inválida."""


def cargar_config(environ=None):
    """Construye la configuración a partir de las variables de entorno.

    Lanza `ConfigError` si `JWT_SECRET_KEY` no está definida o está vacía.
    Los mensajes de error nombran la variable pero nunca muestran su valor.
    """
    env = os.environ if environ is None else environ

    jwt_secret_key = env.get("JWT_SECRET_KEY", "")
    if not jwt_secret_key.strip():
        raise ConfigError(
            "La variable de entorno JWT_SECRET_KEY es obligatoria y no está "
            "definida o está vacía."
        )

    minutos = env.get("JWT_ACCESS_TOKEN_MINUTES")
    if minutos is None or minutos.strip() == "":
        jwt_access_token_minutes = JWT_ACCESS_TOKEN_MINUTES_POR_DEFECTO
    else:
        try:
            jwt_access_token_minutes = int(minutos)
        except ValueError:
            raise ConfigError(
                "La variable de entorno JWT_ACCESS_TOKEN_MINUTES debe ser un "
                "número entero de minutos."
            ) from None

    # Orígenes permitidos por CORS: lista separada por comas. Sin la variable,
    # no se permite ningún origen cruzado.
    cors_origins = [
        origen.strip()
        for origen in env.get("CORS_ORIGINS", "").split(",")
        if origen.strip()
    ]

    return {
        "JWT_SECRET_KEY": jwt_secret_key,
        "JWT_ACCESS_TOKEN_MINUTES": jwt_access_token_minutes,
        "PASSWORD_MIN_LENGTH": PASSWORD_MIN_LENGTH,
        "DATABASE_URL": env.get("DATABASE_URL"),
        "CORS_ORIGINS": cors_origins,
    }
