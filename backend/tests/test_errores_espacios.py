"""Códigos de error del catálogo de espacios (tarea 2.1; design.md, D5).

La ruta `/_prueba/espacios/error/...` se registra únicamente en estas pruebas
y lanza cada excepción de dominio a través del manejador de errores existente.
"""

import pytest
from flask import request

from backend.app.auth import errors

NOMBRE_ENVIADO = "Sala Secreta 123"

CATALOGO = [
    (errors.TipoEspacioInvalido, 400, "tipo_espacio_invalido"),
    (errors.CapacidadInvalida, 400, "capacidad_invalida"),
    (errors.EspacioDuplicado, 409, "espacio_duplicado"),
    (errors.EspacioNoEncontrado, 404, "espacio_no_encontrado"),
    (errors.EspacioYaInactivo, 409, "espacio_ya_inactivo"),
    (errors.EspacioYaActivo, 409, "espacio_ya_activo"),
]


@pytest.fixture
def cliente_con_ruta_de_prueba(app):
    @app.post("/_prueba/espacios/error/<int:indice>")
    def _lanzar_error_de_espacios(indice):
        request.get_json()
        raise CATALOGO[indice][0]()

    return app.test_client()


@pytest.mark.parametrize("indice", range(len(CATALOGO)), ids=[c[2] for c in CATALOGO])
def test_cada_codigo_de_espacios_produce_su_http_y_su_codigo_de_error(
    cliente_con_ruta_de_prueba, indice
):
    excepcion, http, codigo = CATALOGO[indice]
    cuerpo_enviado = {"nombre": NOMBRE_ENVIADO, "tipo": "aula_magna", "capacidad": 98765}

    respuesta = cliente_con_ruta_de_prueba.post(
        f"/_prueba/espacios/error/{indice}", json=cuerpo_enviado
    )

    assert respuesta.status_code == http
    cuerpo = respuesta.get_json()
    assert set(cuerpo) == {"error"}
    assert set(cuerpo["error"]) == {"codigo", "mensaje"}
    assert cuerpo["error"]["codigo"] == codigo
    assert cuerpo["error"]["mensaje"] == excepcion.mensaje
    for valor in cuerpo_enviado.values():
        assert str(valor) not in cuerpo["error"]["mensaje"]


@pytest.mark.parametrize("excepcion", [c[0] for c in CATALOGO], ids=[c[2] for c in CATALOGO])
def test_los_mensajes_de_espacios_son_textos_fijos(excepcion):
    assert issubclass(excepcion, errors.ErrorDeDominio)
    with pytest.raises(TypeError):
        excepcion("mensaje con datos de la petición")
