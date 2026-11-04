"""Códigos de error nuevos de aprobaciones (tarea 2.1 de `aprobacion-reservas`).

La ruta `/_prueba/aprobaciones/error/...` se registra únicamente en estas
pruebas y lanza cada excepción a través del manejador de errores existente.
Requisitos «Transiciones permitidas desde el estado pendiente» y «Aprobación de
solicitudes pendientes» de la spec `aprobaciones`.
"""

import pytest

from backend.app.auth import errors

CATALOGO = [
    (errors.TransicionInvalida, 409, "transicion_invalida"),
    (errors.SolicitudVencida, 409, "solicitud_vencida"),
]


@pytest.fixture
def cliente_con_ruta_de_prueba(app):
    @app.post("/_prueba/aprobaciones/error/<int:indice>")
    def _lanzar_error_de_aprobaciones(indice):
        raise CATALOGO[indice][0]()

    return app.test_client()


@pytest.mark.parametrize("indice", range(len(CATALOGO)), ids=[c[2] for c in CATALOGO])
def test_cada_codigo_produce_su_http_y_el_formato_de_error(cliente_con_ruta_de_prueba, indice):
    excepcion, http, codigo = CATALOGO[indice]

    respuesta = cliente_con_ruta_de_prueba.post(f"/_prueba/aprobaciones/error/{indice}")

    assert respuesta.status_code == http
    assert respuesta.get_json() == {"error": {"codigo": codigo, "mensaje": excepcion.mensaje}}


@pytest.mark.parametrize("excepcion", [c[0] for c in CATALOGO], ids=[c[2] for c in CATALOGO])
def test_los_mensajes_son_textos_fijos(excepcion):
    assert issubclass(excepcion, errors.ErrorDeDominio)
    with pytest.raises(TypeError):
        excepcion("mensaje con datos de la petición")
