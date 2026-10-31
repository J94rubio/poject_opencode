"""Pruebas de la verificación del token (tareas 3.3 y 3.4).

Usan una ruta protegida de prueba registrada únicamente en estas pruebas,
porque la primera ruta protegida real llega con `GET /api/auth/me`.
"""

from datetime import datetime, timedelta, timezone

import jwt
import pytest
from flask import g

from backend.app.auth.services import generar_hash_password, requiere_autenticacion
from backend.app.auth.tokens import emitir_token
from backend.app.usuarios import repositories


@pytest.fixture
def cliente_protegido(app):
    @app.get("/_prueba/protegida")
    @requiere_autenticacion
    def _ruta_protegida():
        usuario = g.usuario_actual
        return {"usuario_id": usuario.id, "rol": usuario.rol.nombre}

    return app.test_client()


def _codigo(respuesta):
    return respuesta.get_json()["error"]["codigo"]


def _token(app, usuario_id=1, **kwargs):
    with app.app_context():
        return emitir_token(usuario_id, **kwargs)


def _crear_usuario(sesion, rol="solicitante", correo="persona@example.com"):
    usuario = repositories.crear_usuario(
        "Persona", correo, generar_hash_password("contrasena-valida"),
        repositories.obtener_rol_por_nombre(rol),
    )
    sesion.commit()
    return usuario.id


def _cabecera(token):
    return {"Authorization": f"Bearer {token}"}


# --- Tarea 3.3: validación del token ---------------------------------------


def test_peticion_sin_token(cliente_protegido):
    respuesta = cliente_protegido.get("/_prueba/protegida")

    assert respuesta.status_code == 401
    assert _codigo(respuesta) == "token_ausente"


@pytest.mark.parametrize(
    "cabecera",
    ["", "Bearer", "Bearer ", "Token {token}", "bearer {token}", "{token}", "Bearer {token} extra",
     "Bearer no-es-un-jwt"],
)
def test_cabecera_mal_formada(app, cliente_protegido, cabecera):
    valor = cabecera.format(token=_token(app))
    respuesta = cliente_protegido.get("/_prueba/protegida", headers={"Authorization": valor})

    assert respuesta.status_code == 401
    assert _codigo(respuesta) == "token_invalido"


def test_firma_invalida(cliente_protegido):
    ahora = datetime.now(timezone.utc)
    falsificado = jwt.encode(
        {"sub": "1", "iat": ahora, "exp": ahora + timedelta(minutes=60)},
        "otra-clave-distinta-de-la-de-la-aplicacion-0123456789",
        algorithm="HS256",
    )
    respuesta = cliente_protegido.get("/_prueba/protegida", headers=_cabecera(falsificado))

    assert respuesta.status_code == 401
    assert _codigo(respuesta) == "token_invalido"


def test_token_expirado(app, cliente_protegido):
    expirado = _token(app, ahora=datetime.now(timezone.utc) - timedelta(minutes=61))
    respuesta = cliente_protegido.get("/_prueba/protegida", headers=_cabecera(expirado))

    assert respuesta.status_code == 401
    assert _codigo(respuesta) == "token_expirado"
    assert expirado not in respuesta.get_data(as_text=True)


# --- Tarea 3.4: usuario y rol vigente cargados en cada petición -------------


def test_token_valido_ejecuta_la_peticion_con_la_identidad_del_usuario(
    app, sesion, cliente_protegido
):
    usuario_id = _crear_usuario(sesion, rol="aprobador")

    respuesta = cliente_protegido.get(
        "/_prueba/protegida", headers=_cabecera(_token(app, usuario_id))
    )

    assert respuesta.status_code == 200
    assert respuesta.get_json() == {"usuario_id": usuario_id, "rol": "aprobador"}


def test_el_rol_efectivo_cambia_en_la_siguiente_peticion_sin_reautenticarse(
    app, sesion, cliente_protegido
):
    usuario_id = _crear_usuario(sesion, rol="solicitante")
    cabecera = _cabecera(_token(app, usuario_id))

    antes = cliente_protegido.get("/_prueba/protegida", headers=cabecera)
    assert antes.get_json()["rol"] == "solicitante"

    usuario = repositories.obtener_usuario_por_id(usuario_id)
    usuario.rol = repositories.obtener_rol_por_nombre("admin")
    sesion.commit()

    despues = cliente_protegido.get("/_prueba/protegida", headers=cabecera)
    assert despues.status_code == 200
    assert despues.get_json()["rol"] == "admin"


def test_token_vigente_de_una_cuenta_desactivada(app, sesion, cliente_protegido):
    usuario_id = _crear_usuario(sesion)
    cabecera = _cabecera(_token(app, usuario_id))
    repositories.obtener_usuario_por_id(usuario_id).activo = False
    sesion.commit()

    respuesta = cliente_protegido.get("/_prueba/protegida", headers=cabecera)

    assert respuesta.status_code == 401
    assert _codigo(respuesta) == "usuario_desactivado"


def test_token_de_un_usuario_inexistente(app, sesion, cliente_protegido):
    respuesta = cliente_protegido.get("/_prueba/protegida", headers=_cabecera(_token(app, 999)))

    assert respuesta.status_code == 401
    assert _codigo(respuesta) == "token_invalido"
