"""Pruebas del contrato de errores de la API (tarea 3.1).

Las rutas `/_prueba/...` se registran únicamente en estas pruebas.
"""

import pytest
from flask import request

from backend.app.auth import errors

CORREO = "persona@example.com"
CONTRASENA = "secreto-123"

CATALOGO = [
    (errors.DatosInvalidos, 400, "datos_invalidos"),
    (errors.ContrasenaInvalida, 400, "contrasena_invalida"),
    (errors.RolInvalido, 400, "rol_invalido"),
    (errors.CredencialesInvalidas, 401, "credenciales_invalidas"),
    (errors.UsuarioDesactivado, 401, "usuario_desactivado"),
    (errors.TokenAusente, 401, "token_ausente"),
    (errors.TokenInvalido, 401, "token_invalido"),
    (errors.TokenExpirado, 401, "token_expirado"),
    (errors.PermisoInsuficiente, 403, "permiso_insuficiente"),
    (errors.UsuarioNoEncontrado, 404, "usuario_no_encontrado"),
    (errors.CorreoDuplicado, 409, "correo_duplicado"),
    (errors.OperacionNoPermitida, 409, "operacion_no_permitida"),
]


@pytest.fixture
def app_con_rutas_de_prueba(app):
    @app.post("/_prueba/error/<int:indice>")
    def _lanzar_error_de_dominio(indice):
        # La petición lleva correo y contraseña para comprobar que no se filtran.
        request.get_json()
        raise CATALOGO[indice][0]()

    @app.post("/_prueba/json")
    def _leer_json():
        return {"recibido": request.get_json()}

    @app.get("/_prueba/fallo")
    def _fallo_interno():
        raise RuntimeError(f"detalle técnico interno: conexión a {CORREO} con {CONTRASENA}")

    return app


def _cuerpo_error(respuesta):
    cuerpo = respuesta.get_json()
    assert set(cuerpo) == {"error"}
    assert set(cuerpo["error"]) == {"codigo", "mensaje"}
    return cuerpo["error"]


@pytest.mark.parametrize("indice", range(len(CATALOGO)), ids=[c[2] for c in CATALOGO])
def test_cada_excepcion_de_dominio_produce_su_codigo_http_y_su_codigo_de_error(
    app_con_rutas_de_prueba, indice
):
    excepcion, http, codigo = CATALOGO[indice]
    respuesta = app_con_rutas_de_prueba.test_client().post(
        f"/_prueba/error/{indice}", json={"correo": CORREO, "contrasena": CONTRASENA}
    )

    assert respuesta.status_code == http
    error = _cuerpo_error(respuesta)
    assert error["codigo"] == codigo
    assert error["mensaje"] == excepcion.mensaje
    assert CORREO not in error["mensaje"]
    assert CONTRASENA not in error["mensaje"]


def test_los_mensajes_del_catalogo_son_textos_fijos():
    for excepcion, _, _ in CATALOGO:
        with pytest.raises(TypeError):
            excepcion("mensaje con datos de la petición")


def test_ruta_inexistente(client):
    respuesta = client.get("/api/no-existe")

    assert respuesta.status_code == 404
    assert _cuerpo_error(respuesta)["codigo"] == "ruta_no_encontrada"


def test_metodo_no_permitido(app_con_rutas_de_prueba):
    respuesta = app_con_rutas_de_prueba.test_client().delete("/_prueba/json")

    assert respuesta.status_code == 405
    assert _cuerpo_error(respuesta)["codigo"] == "metodo_no_permitido"


def test_cuerpo_json_mal_formado(app_con_rutas_de_prueba):
    respuesta = app_con_rutas_de_prueba.test_client().post(
        "/_prueba/json",
        data='{"correo": "' + CORREO + '", ',
        content_type="application/json",
    )

    assert respuesta.status_code == 400
    error = _cuerpo_error(respuesta)
    assert error["codigo"] == "datos_invalidos"
    assert CORREO not in error["mensaje"]


def test_error_interno_no_controlado(app_con_rutas_de_prueba):
    respuesta = app_con_rutas_de_prueba.test_client().get("/_prueba/fallo")

    assert respuesta.status_code == 500
    error = _cuerpo_error(respuesta)
    assert error == {"codigo": "error_interno", "mensaje": errors.MENSAJE_ERROR_INTERNO}
    texto = respuesta.get_data(as_text=True)
    for filtrado in ("detalle técnico", "RuntimeError", "Traceback", CORREO, CONTRASENA):
        assert filtrado not in texto
