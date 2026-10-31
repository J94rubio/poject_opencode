"""Servicio de listado y detalle de solicitudes (tarea 3.6).

Requisito «Listado y detalle de solicitudes» de la spec `reservas`: con
`reservas:ver_propias` el solicitante ve solo las suyas y con
`reservas:ver_todas` el aprobador y el admin ven todas.
"""

from datetime import datetime, timezone

import pytest

from backend.app.auth.errors import PermisoInsuficiente, SolicitudNoEncontrada
from backend.app.reservas import services
from backend.app.usuarios import repositories as repositorio_usuarios


def _h(hora):
    return datetime(2026, 11, 3, hora, tzinfo=timezone.utc)


@pytest.fixture
def cuentas(crear_cuenta):
    """Un usuario de cada rol más un segundo solicitante."""
    ids = {
        "ana": crear_cuenta("solicitante", correo="ana@example.com"),
        "luis": crear_cuenta("solicitante", correo="luis@example.com"),
        "aprobador": crear_cuenta("aprobador"),
        "admin": crear_cuenta("admin"),
    }
    return {nombre: repositorio_usuarios.obtener_usuario_por_id(i) for nombre, i in ids.items()}


@pytest.fixture
def solicitudes(sesion, nuevo_espacio, cuentas, sembrar_reserva):
    """Solicitudes de varios usuarios y estados, insertadas fuera de orden."""
    espacio = nuevo_espacio()
    return {
        "luis_15": sembrar_reserva(espacio, cuentas["luis"].id, _h(15), _h(16), "pendiente"),
        "ana_11": sembrar_reserva(espacio, cuentas["ana"].id, _h(11), _h(12), "aprobada"),
        "aprobador_9": sembrar_reserva(espacio, cuentas["aprobador"].id, _h(9), _h(10),
                                       "pendiente"),
        "ana_9": sembrar_reserva(espacio, cuentas["ana"].id, _h(9), _h(11), "rechazada"),
    }


def _ids(reservas):
    return [r.id for r in reservas]


def test_solicitante_ve_solo_sus_solicitudes_en_orden(sesion, cuentas, solicitudes):
    assert _ids(services.listar_solicitudes(cuentas["ana"])) == [
        solicitudes["ana_9"], solicitudes["ana_11"]]
    assert _ids(services.listar_solicitudes(cuentas["luis"])) == [solicitudes["luis_15"]]


@pytest.mark.parametrize("rol", ["aprobador", "admin"])
def test_aprobador_y_admin_ven_todas_en_orden(sesion, cuentas, solicitudes, rol):
    # A igual inicio (09:00), por identificador: `aprobador_9` se insertó antes.
    assert _ids(services.listar_solicitudes(cuentas[rol])) == [
        solicitudes["aprobador_9"], solicitudes["ana_9"], solicitudes["ana_11"],
        solicitudes["luis_15"]]


@pytest.mark.parametrize("nombre", ["ana", "aprobador", "admin"])
def test_listado_sin_solicitudes_visibles(sesion, cuentas, nombre):
    assert services.listar_solicitudes(cuentas[nombre]) == []


def test_solicitante_sin_solicitudes_propias_aunque_existan_ajenas(sesion, crear_cuenta,
                                                                     solicitudes):
    eva = repositorio_usuarios.obtener_usuario_por_id(
        crear_cuenta("solicitante", correo="eva@example.com"))
    assert services.listar_solicitudes(eva) == []


def test_detalle_de_una_solicitud_propia(sesion, cuentas, solicitudes):
    reserva = services.obtener_solicitud(solicitudes["ana_11"], cuentas["ana"])
    assert (reserva.id, reserva.solicitante_id) == (solicitudes["ana_11"], cuentas["ana"].id)


def test_detalle_ajeno_por_un_solicitante(sesion, cuentas, solicitudes):
    with pytest.raises(PermisoInsuficiente) as error:
        services.obtener_solicitud(solicitudes["luis_15"], cuentas["ana"])
    assert (error.value.http, error.value.codigo) == (403, "permiso_insuficiente")


@pytest.mark.parametrize("rol", ["aprobador", "admin"])
def test_detalle_ajeno_por_aprobador_o_admin(sesion, cuentas, solicitudes, rol):
    reserva = services.obtener_solicitud(solicitudes["luis_15"], cuentas[rol])
    assert reserva.solicitante_id == cuentas["luis"].id


@pytest.mark.parametrize("nombre", ["ana", "aprobador", "admin"])
@pytest.mark.parametrize("reserva_id", [999_999, 2_147_483_648])
def test_detalle_de_una_solicitud_inexistente(sesion, cuentas, solicitudes, nombre, reserva_id):
    with pytest.raises(SolicitudNoEncontrada) as error:
        services.obtener_solicitud(reserva_id, cuentas[nombre])
    assert (error.value.http, error.value.codigo) == (404, "solicitud_no_encontrada")
