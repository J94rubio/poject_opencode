"""Pruebas del inicio de sesión `POST /api/auth/login` (tarea 3.5)."""

import jwt
import pytest

from backend.app.auth.services import generar_hash_password
from backend.app.usuarios import repositories

CORREO = "ana.perez@example.com"
CONTRASENA = "contrasena-correcta"


@pytest.fixture
def usuario_id(sesion):
    usuario = repositories.crear_usuario(
        "Ana Pérez", CORREO, generar_hash_password(CONTRASENA),
        repositories.obtener_rol_por_nombre("aprobador"),
    )
    sesion.commit()
    return usuario.id


def _login(client, **cuerpo):
    return client.post("/api/auth/login", json=cuerpo)


def _error(respuesta):
    return respuesta.get_json()["error"]


def _sin_datos_sensibles(respuesta):
    texto = respuesta.get_data(as_text=True)
    return CONTRASENA not in texto and CORREO not in texto and "token" not in respuesta.get_json()


def test_credenciales_validas_de_una_cuenta_activa(client, usuario_id, jwt_secret_key_de_prueba):
    respuesta = _login(client, correo=CORREO, contrasena=CONTRASENA)

    assert respuesta.status_code == 200
    cuerpo = respuesta.get_json()
    assert set(cuerpo) == {"token", "tipo_token", "expira_en", "usuario"}
    assert cuerpo["tipo_token"] == "Bearer"
    assert cuerpo["expira_en"] == 60 * 60
    assert cuerpo["usuario"] == {
        "id": usuario_id, "nombre": "Ana Pérez", "correo": CORREO, "rol": "aprobador",
    }
    claims = jwt.decode(cuerpo["token"], jwt_secret_key_de_prueba, algorithms=["HS256"])
    assert set(claims) == {"sub", "iat", "exp"}
    assert claims["sub"] == str(usuario_id)
    texto = respuesta.get_data(as_text=True)
    assert CONTRASENA not in texto
    assert "password" not in texto and "hash" not in texto


def test_login_con_el_correo_en_mayusculas(client, usuario_id):
    respuesta = _login(client, correo=CORREO.upper(), contrasena=CONTRASENA)

    assert respuesta.status_code == 200
    assert respuesta.get_json()["usuario"]["id"] == usuario_id


def test_contrasena_incorrecta(client, usuario_id):
    respuesta = _login(client, correo=CORREO, contrasena="otra-contrasena")

    assert respuesta.status_code == 401
    assert _error(respuesta)["codigo"] == "credenciales_invalidas"
    assert _sin_datos_sensibles(respuesta)


def test_correo_inexistente_con_el_mismo_mensaje_que_la_contrasena_incorrecta(
    client, usuario_id
):
    inexistente = _login(client, correo="nadie@example.com", contrasena=CONTRASENA)
    incorrecta = _login(client, correo=CORREO, contrasena="otra-contrasena")

    assert inexistente.status_code == 401
    assert _error(inexistente) == _error(incorrecta)
    assert "nadie@example.com" not in inexistente.get_data(as_text=True)
    assert "token" not in inexistente.get_json()


def test_cuenta_desactivada(client, sesion, usuario_id):
    repositories.obtener_usuario_por_id(usuario_id).activo = False
    sesion.commit()

    respuesta = _login(client, correo=CORREO, contrasena=CONTRASENA)

    assert respuesta.status_code == 401
    assert _error(respuesta)["codigo"] == "usuario_desactivado"
    assert _sin_datos_sensibles(respuesta)


def test_cuenta_desactivada_con_contrasena_incorrecta_no_revela_el_estado(
    client, sesion, usuario_id
):
    repositories.obtener_usuario_por_id(usuario_id).activo = False
    sesion.commit()

    respuesta = _login(client, correo=CORREO, contrasena="otra-contrasena")

    assert respuesta.status_code == 401
    assert _error(respuesta)["codigo"] == "credenciales_invalidas"


@pytest.mark.parametrize(
    "cuerpo",
    [
        {"contrasena": CONTRASENA},
        {"correo": CORREO},
        {"correo": "", "contrasena": CONTRASENA},
        {"correo": CORREO, "contrasena": ""},
        {"correo": 123, "contrasena": CONTRASENA},
        {},
    ],
    ids=["sin_correo", "sin_contrasena", "correo_vacio", "contrasena_vacia", "correo_no_texto",
         "vacio"],
)
def test_datos_de_acceso_incompletos(client, usuario_id, cuerpo):
    respuesta = _login(client, **cuerpo)

    assert respuesta.status_code == 400
    assert _error(respuesta)["codigo"] == "datos_invalidos"
    assert _sin_datos_sensibles(respuesta)


def test_login_sin_cuerpo_json(client, usuario_id):
    respuesta = client.post("/api/auth/login", data="no es json", content_type="text/plain")

    assert respuesta.status_code == 400
    assert _error(respuesta)["codigo"] == "datos_invalidos"
