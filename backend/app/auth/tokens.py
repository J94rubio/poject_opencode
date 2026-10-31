"""Emisión y verificación del token de acceso JWT (design.md, D4).

HS256 con PyJWT. Claims: únicamente `sub` (id de usuario), `iat` y `exp`; el
token no transporta el rol (D5). La clave se lee de la configuración de la app
(`JWT_SECRET_KEY`, obligatoria y tomada del entorno) y la vigencia de
`JWT_ACCESS_TOKEN_MINUTES` (60 minutos por defecto).
"""

from datetime import datetime, timedelta, timezone

import jwt
from flask import current_app

from .errors import TokenExpirado, TokenInvalido

ALGORITMO = "HS256"
TIPO_TOKEN = "Bearer"


def vigencia_en_segundos():
    return int(current_app.config["JWT_ACCESS_TOKEN_MINUTES"]) * 60


def emitir_token(usuario_id, ahora=None):
    """Devuelve el token de acceso del usuario.

    `ahora` permite fijar la fecha de emisión de forma determinista en las
    pruebas; por defecto es el instante actual en UTC.
    """
    emitido = ahora or datetime.now(timezone.utc)
    claims = {
        "sub": str(usuario_id),
        "iat": emitido,
        "exp": emitido + timedelta(seconds=vigencia_en_segundos()),
    }
    return jwt.encode(claims, current_app.config["JWT_SECRET_KEY"], algorithm=ALGORITMO)


def verificar_token(token):
    """Valida firma y expiración y devuelve el id de usuario del token.

    Lanza `TokenExpirado` si `exp` ya pasó y `TokenInvalido` si el token está
    mal formado, su firma no corresponde o le faltan los claims esperados.
    """
    try:
        claims = jwt.decode(
            token,
            current_app.config["JWT_SECRET_KEY"],
            algorithms=[ALGORITMO],
            options={"require": ["sub", "iat", "exp"]},
        )
    except jwt.ExpiredSignatureError:
        raise TokenExpirado() from None
    except jwt.InvalidTokenError:
        raise TokenInvalido() from None

    try:
        return int(claims["sub"])
    except (TypeError, ValueError):
        raise TokenInvalido() from None
