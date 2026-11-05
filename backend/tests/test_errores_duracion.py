"""Código de error de la duración máxima (tarea 2.1 de `limite-duracion-reserva`).

La ruta `/_prueba/duracion/error` se registra únicamente en estas pruebas y lanza
la excepción a través del manejador de errores existente. Requisitos «Creación de
solicitudes de reserva» y «Alcance de la duración máxima» de la spec `reservas`.
"""

import pytest

from backend.app.auth import errors


def test_duracion_excedida_produce_su_http_y_el_formato_de_error(app):
    @app.post("/_prueba/duracion/error")
    def _lanzar_duracion_excedida():
        raise errors.DuracionExcedida()

    respuesta = app.test_client().post("/_prueba/duracion/error")

    assert respuesta.status_code == 400
    assert respuesta.get_json() == {
        "error": {
            "codigo": "duracion_excedida",
            "mensaje": "La duración máxima de una reserva es de 4 horas.",
        }
    }


def test_el_mensaje_es_un_texto_fijo():
    assert errors.DuracionExcedida.__bases__ == (errors.ErrorDeDominio,)
    with pytest.raises(TypeError):
        errors.DuracionExcedida("mensaje con datos de la petición")
