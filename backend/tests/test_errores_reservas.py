"""Códigos de error de reservas (tarea 3.1).

La ruta `/_prueba/reservas/error/...` se registra únicamente en estas pruebas
y lanza cada excepción de dominio a través del manejador de errores existente.
Requisitos «Creación de solicitudes de reserva», «Ocupación por reservas
aprobadas» y «Listado y detalle de solicitudes» de la spec `reservas`.
"""

import pytest
from flask import request

from backend.app.auth import errors

CATALOGO = [
    (errors.EspacioInactivo, 400, "espacio_inactivo"),
    (errors.ReservaSolapada, 409, "reserva_solapada"),
    (errors.SolicitudNoEncontrada, 404, "solicitud_no_encontrada"),
]


@pytest.fixture
def cliente_con_ruta_de_prueba(app):
    @app.post("/_prueba/reservas/error/<int:indice>")
    def _lanzar_error_de_reservas(indice):
        request.get_json()
        raise CATALOGO[indice][0]()

    return app.test_client()


@pytest.mark.parametrize("indice", range(len(CATALOGO)), ids=[c[2] for c in CATALOGO])
def test_cada_codigo_de_reservas_produce_su_http_y_su_codigo_de_error(
    cliente_con_ruta_de_prueba, indice
):
    excepcion, http, codigo = CATALOGO[indice]
    cuerpo_enviado = {"espacio_id": 4321, "inicio": "2031-05-06T07:08:09+02:00",
                      "fin": "2031-05-06T09:08:09+02:00"}

    respuesta = cliente_con_ruta_de_prueba.post(
        f"/_prueba/reservas/error/{indice}", json=cuerpo_enviado
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
def test_los_mensajes_de_reservas_son_textos_fijos(excepcion):
    assert issubclass(excepcion, errors.ErrorDeDominio)
    with pytest.raises(TypeError):
        excepcion("mensaje con datos de la petición")
