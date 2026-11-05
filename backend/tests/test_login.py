"""Pruebas del inicio de sesión `POST /api/auth/login` (tarea 3.5)."""

import jwt
import pytest

from backend.app.auth.services import generar_hash_password
from backend.app.models import Usuario
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


@pytest.fixture
def vigencia_de_5_minutos(monkeypatch):
    """Fija la vigencia antes de que se cree la app de la prueba."""
    monkeypatch.setenv("JWT_ACCESS_TOKEN_MINUTES", "5")


def test_vigencia_configurada_en_el_login(vigencia_de_5_minutos, client, usuario_id):
    """Escenario «Vigencia configurada» de la spec `auth` a través del login."""
    respuesta = _login(client, correo=CORREO, contrasena=CONTRASENA)

    assert respuesta.status_code == 200
    assert respuesta.get_json()["expira_en"] == 300


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


# --- Correo o contraseña con NUL o sustitutos UTF-16 sueltos -------------------

TEXTOS_NO_ALMACENABLES = ["ana\x00@example.com", "\x00", "ana\ud800@example.com", "\udc00"]
IDS_TEXTOS = ["nul", "solo_nul", "sustituto_alto", "sustituto_bajo"]


def _misma_respuesta_que_una_cuenta_inexistente(client, respuesta):
    inexistente = _login(client, correo="nadie@example.com", contrasena=CONTRASENA)
    assert inexistente.status_code == 401
    assert _error(inexistente)["codigo"] == "credenciales_invalidas"
    assert respuesta.status_code == inexistente.status_code
    assert respuesta.data == inexistente.data
    assert respuesta.content_type == inexistente.content_type


@pytest.mark.parametrize("correo", TEXTOS_NO_ALMACENABLES, ids=IDS_TEXTOS)
def test_correo_no_almacenable_responde_como_una_cuenta_inexistente(client, usuario_id, correo):
    respuesta = _login(client, correo=correo, contrasena=CONTRASENA)

    _misma_respuesta_que_una_cuenta_inexistente(client, respuesta)


@pytest.mark.parametrize(
    "contrasena",
    ["contrasena\x00correcta", "\x00", "contrasena\ud800correcta", "\udc00"],
    ids=IDS_TEXTOS,
)
@pytest.mark.parametrize("correo", [CORREO, "nadie@example.com"], ids=["existente", "inexistente"])
def test_contrasena_con_nul_o_sustitutos_responde_como_credenciales_incorrectas(
    client, usuario_id, correo, contrasena
):
    respuesta = _login(client, correo=correo, contrasena=contrasena)

    _misma_respuesta_que_una_cuenta_inexistente(client, respuesta)
    incorrecta = _login(client, correo=CORREO, contrasena="otra-contrasena")
    assert respuesta.data == incorrecta.data


def test_contrasena_con_sustitutos_no_revela_una_cuenta_desactivada(client, sesion, usuario_id):
    sesion.get(Usuario, usuario_id).activo = False
    sesion.commit()

    respuesta = _login(client, correo=CORREO, contrasena="contrasena\ud800correcta")

    _misma_respuesta_que_una_cuenta_inexistente(client, respuesta)
