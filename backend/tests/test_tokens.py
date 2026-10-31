"""Pruebas de la emisión del token de acceso (tarea 3.2)."""

from datetime import datetime, timedelta, timezone

import jwt
import pytest

from backend.app import create_app
from backend.app.auth.errors import TokenExpirado
from backend.app.auth.tokens import emitir_token, verificar_token


def _decodificar(token, clave):
    return jwt.decode(token, clave, algorithms=["HS256"], options={"verify_exp": False})


def test_el_token_contiene_unicamente_sub_iat_y_exp(app, jwt_secret_key_de_prueba):
    with app.app_context():
        token = emitir_token(42)

    claims = _decodificar(token, jwt_secret_key_de_prueba)

    assert set(claims) == {"sub", "iat", "exp"}
    assert claims["sub"] == "42"


def test_vigencia_por_defecto_de_60_minutos(app, jwt_secret_key_de_prueba):
    with app.app_context():
        token = emitir_token(1)

    claims = _decodificar(token, jwt_secret_key_de_prueba)

    assert claims["exp"] - claims["iat"] == 60 * 60


def test_vigencia_configurada(jwt_secret_key_de_prueba, monkeypatch):
    monkeypatch.setenv("JWT_ACCESS_TOKEN_MINUTES", "5")
    app = create_app({"TESTING": True})
    with app.app_context():
        token = emitir_token(1)

    claims = _decodificar(token, jwt_secret_key_de_prueba)

    assert claims["exp"] - claims["iat"] == 5 * 60


def test_el_token_expira_al_cumplirse_la_vigencia(app):
    with app.app_context():
        vigente = emitir_token(7, ahora=datetime.now(timezone.utc) - timedelta(minutes=59))
        expirado = emitir_token(7, ahora=datetime.now(timezone.utc) - timedelta(minutes=61))

        assert verificar_token(vigente) == 7
        with pytest.raises(TokenExpirado):
            verificar_token(expirado)
