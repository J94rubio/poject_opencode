"""Pruebas de la consulta del usuario autenticado `GET /api/auth/me` (tarea 3.6)."""

from datetime import datetime, timedelta, timezone

import pytest

from backend.app.auth.services import generar_hash_password
from backend.app.auth.tokens import emitir_token
from backend.app.usuarios import repositories

CONTRASENA = "contrasena-correcta"


@pytest.fixture
def usuario_id(sesion):
    usuario = repositories.crear_usuario(
        "Ana Pérez", "ana@example.com", generar_hash_password(CONTRASENA),
        repositories.obtener_rol_por_nombre("solicitante"),
    )
    sesion.commit()
    return usuario.id


def _token(app, usuario_id, **kwargs):
    with app.app_context():
        return emitir_token(usuario_id, **kwargs)


def test_consulta_con_token_valido(app, client, usuario_id):
    respuesta = client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {_token(app, usuario_id)}"}
    )

    assert respuesta.status_code == 200
    assert respuesta.get_json() == {
        "id": usuario_id,
        "nombre": "Ana Pérez",
        "correo": "ana@example.com",
        "rol": "solicitante",
        "activo": True,
    }
    texto = respuesta.get_data(as_text=True)
    assert CONTRASENA not in texto
    assert "hash" not in texto


def test_consulta_con_el_token_emitido_por_el_login(client, usuario_id):
    login = client.post(
        "/api/auth/login", json={"correo": "ana@example.com", "contrasena": CONTRASENA}
    )
    token = login.get_json()["token"]

    respuesta = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert respuesta.status_code == 200
    assert respuesta.get_json()["id"] == usuario_id


def test_consulta_sin_token(client):
    respuesta = client.get("/api/auth/me")

    assert respuesta.status_code == 401
    assert respuesta.get_json()["error"]["codigo"] == "token_ausente"


def test_consulta_con_token_expirado(app, client, usuario_id):
    expirado = _token(app, usuario_id, ahora=datetime.now(timezone.utc) - timedelta(minutes=61))

    respuesta = client.get("/api/auth/me", headers={"Authorization": f"Bearer {expirado}"})

    assert respuesta.status_code == 401
    assert respuesta.get_json()["error"]["codigo"] == "token_expirado"
