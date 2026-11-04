"""Código de error nuevo de cancelaciones (tarea 4.1 de `cancelacion-historial`).

La ruta `/_prueba/cancelaciones/error` se registra únicamente en estas pruebas y
lanza la excepción a través del manejador de errores existente. Requisito
«Condiciones de la cancelación» de la spec `cancelaciones`.
"""

import pytest

from backend.app.auth import errors


def test_reserva_iniciada_produce_su_http_y_el_formato_de_error(app):
    @app.post("/_prueba/cancelaciones/error")
    def _lanzar_reserva_iniciada():
        raise errors.ReservaIniciada()

    respuesta = app.test_client().post("/_prueba/cancelaciones/error")

    assert respuesta.status_code == 409
    assert respuesta.get_json() == {
        "error": {"codigo": "reserva_iniciada", "mensaje": errors.ReservaIniciada.mensaje}
    }


def test_el_mensaje_es_un_texto_fijo():
    assert issubclass(errors.ReservaIniciada, errors.ErrorDeDominio)
    with pytest.raises(TypeError):
        errors.ReservaIniciada("mensaje con datos de la petición")
