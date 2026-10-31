"""Pruebas del alta de usuarios `POST /api/usuarios` (tarea 5.1).

Requisitos «Alta de usuarios por el administrador» y «Normalización y unicidad
del correo» de la spec `usuarios`.
"""

import pytest
from sqlalchemy import func, select

from backend.app.auth.services import verificar_password
from backend.app.models import Usuario
from backend.app.usuarios import repositories

CONTRASENA = "contrasena-nueva"


@pytest.fixture
def admin(crear_cuenta, cabecera):
    return cabecera(crear_cuenta("admin"))


def _cuerpo(**cambios):
    cuerpo = {
        "nombre": "Luis Gómez",
        "correo": "luis.gomez@example.com",
        "contrasena": CONTRASENA,
        "rol": "solicitante",
    }
    cuerpo.update(cambios)
    return {k: v for k, v in cuerpo.items() if v is not None}


def _alta(client, cabecera, **cambios):
    return client.post("/api/usuarios", json=_cuerpo(**cambios), headers=cabecera)


def _codigo(respuesta):
    return respuesta.get_json()["error"]["codigo"]


def _numero_de_cuentas(sesion):
    sesion.expire_all()
    return sesion.execute(select(func.count(Usuario.id))).scalar_one()


def test_alta_valida(client, sesion, admin):
    respuesta = _alta(client, admin)

    assert respuesta.status_code == 201
    cuerpo = respuesta.get_json()
    assert set(cuerpo) == {"id", "nombre", "correo", "rol", "activo"}
    assert cuerpo["nombre"] == "Luis Gómez"
    assert cuerpo["correo"] == "luis.gomez@example.com"
    assert cuerpo["rol"] == "solicitante"
    assert cuerpo["activo"] is True
    texto = respuesta.get_data(as_text=True)
    assert CONTRASENA not in texto
    assert "password" not in texto and "hash" not in texto

    sesion.expire_all()
    usuario = repositories.obtener_usuario_por_id(cuerpo["id"])
    assert usuario.activo is True
    assert usuario.password_hash != CONTRASENA
    assert verificar_password(usuario.password_hash, CONTRASENA)


def test_alta_valida_permite_iniciar_sesion(client, admin):
    _alta(client, admin)

    respuesta = client.post(
        "/api/auth/login", json={"correo": "luis.gomez@example.com", "contrasena": CONTRASENA}
    )

    assert respuesta.status_code == 200


def test_alta_guarda_el_correo_en_minusculas(client, admin):
    respuesta = _alta(client, admin, correo="Luis.Gomez@Example.COM")

    assert respuesta.status_code == 201
    assert respuesta.get_json()["correo"] == "luis.gomez@example.com"


@pytest.mark.parametrize("rol", ["solicitante", "aprobador", "admin"])
def test_alta_con_cada_rol_del_catalogo(client, admin, rol):
    respuesta = _alta(client, admin, rol=rol)

    assert respuesta.status_code == 201
    assert respuesta.get_json()["rol"] == rol


def test_alta_con_correo_ya_registrado(client, sesion, admin):
    _alta(client, admin)
    antes = _numero_de_cuentas(sesion)

    respuesta = _alta(client, admin, nombre="Otra persona")

    assert respuesta.status_code == 409
    assert _codigo(respuesta) == "correo_duplicado"
    assert _numero_de_cuentas(sesion) == antes


def test_duplicado_que_solo_difiere_en_mayusculas(client, sesion, admin):
    _alta(client, admin)
    antes = _numero_de_cuentas(sesion)

    respuesta = _alta(client, admin, correo="LUIS.GOMEZ@EXAMPLE.COM")

    assert respuesta.status_code == 409
    assert _codigo(respuesta) == "correo_duplicado"
    assert _numero_de_cuentas(sesion) == antes


@pytest.mark.parametrize(
    "correo",
    ["sin-arroba.example.com", "dos@@example.com", "sin-dominio@", "@example.com",
     "con espacio@example.com", "sin-punto@example", ""],
)
def test_alta_con_correo_de_formato_invalido(client, sesion, admin, correo):
    antes = _numero_de_cuentas(sesion)

    respuesta = _alta(client, admin, correo=correo)

    assert respuesta.status_code == 400
    assert _codigo(respuesta) == "datos_invalidos"
    assert _numero_de_cuentas(sesion) == antes


@pytest.mark.parametrize("campo", ["nombre", "correo", "contrasena"])
def test_alta_con_campos_obligatorios_faltantes(client, sesion, admin, campo):
    antes = _numero_de_cuentas(sesion)
    cuerpo = _cuerpo()
    del cuerpo[campo]

    respuesta = client.post("/api/usuarios", json=cuerpo, headers=admin)

    assert respuesta.status_code == 400
    assert _codigo(respuesta) == "datos_invalidos"
    assert _numero_de_cuentas(sesion) == antes


def test_alta_con_nombre_vacio(client, sesion, admin):
    antes = _numero_de_cuentas(sesion)

    respuesta = _alta(client, admin, nombre="   ")

    assert respuesta.status_code == 400
    assert _codigo(respuesta) == "datos_invalidos"
    assert _numero_de_cuentas(sesion) == antes


def test_alta_sin_cuerpo_json(client, sesion, admin):
    antes = _numero_de_cuentas(sesion)

    respuesta = client.post(
        "/api/usuarios", data="no es json", content_type="text/plain", headers=admin
    )

    assert respuesta.status_code == 400
    assert _codigo(respuesta) == "datos_invalidos"
    assert _numero_de_cuentas(sesion) == antes


@pytest.mark.parametrize("rol", ["superusuario", "Admin", 3])
def test_alta_con_rol_fuera_del_catalogo(client, sesion, admin, rol):
    antes = _numero_de_cuentas(sesion)

    respuesta = _alta(client, admin, rol=rol)

    assert respuesta.status_code == 400
    assert _codigo(respuesta) == "rol_invalido"
    assert _numero_de_cuentas(sesion) == antes


@pytest.mark.parametrize("contrasena", ["corta", "1234567"])
def test_alta_con_contrasena_de_menos_de_8_caracteres(client, sesion, admin, contrasena):
    antes = _numero_de_cuentas(sesion)

    respuesta = _alta(client, admin, contrasena=contrasena)

    assert respuesta.status_code == 400
    assert _codigo(respuesta) == "contrasena_invalida"
    assert contrasena not in respuesta.get_data(as_text=True)
    assert _numero_de_cuentas(sesion) == antes


def test_alta_con_contrasena_que_solo_cumple_el_minimo(client, sesion, admin):
    respuesta = _alta(client, admin, contrasena="abcdefgh")

    assert respuesta.status_code == 201
    sesion.expire_all()
    assert repositories.obtener_usuario_por_id(respuesta.get_json()["id"]) is not None


@pytest.mark.parametrize("rol", ["solicitante", "aprobador"])
def test_alta_solicitada_por_un_rol_sin_permiso(client, sesion, crear_cuenta, cabecera, rol):
    usuario_id = crear_cuenta(rol)
    antes = _numero_de_cuentas(sesion)

    respuesta = _alta(client, cabecera(usuario_id))

    assert respuesta.status_code == 403
    assert _codigo(respuesta) == "permiso_insuficiente"
    assert _numero_de_cuentas(sesion) == antes


def test_alta_sin_autenticacion(client, sesion):
    antes = _numero_de_cuentas(sesion)

    respuesta = client.post("/api/usuarios", json=_cuerpo())

    assert respuesta.status_code == 401
    assert _codigo(respuesta) == "token_ausente"
    assert _numero_de_cuentas(sesion) == antes
