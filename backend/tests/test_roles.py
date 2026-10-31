"""Pruebas del catálogo de roles `GET /api/roles` (tarea 5.6).

Requisito «Catálogo de roles del sistema» de la spec `usuarios`.
"""

import pytest


def test_consulta_del_catalogo_por_el_administrador(client, crear_cuenta, cabecera):
    admin_id = crear_cuenta("admin")

    respuesta = client.get("/api/roles", headers=cabecera(admin_id))

    assert respuesta.status_code == 200
    roles = respuesta.get_json()
    assert sorted(r["nombre"] for r in roles) == ["admin", "aprobador", "solicitante"]
    assert all(set(r) == {"id", "nombre"} and isinstance(r["id"], int) for r in roles)
    assert len({r["id"] for r in roles}) == 3


@pytest.mark.parametrize("rol", ["solicitante", "aprobador"])
def test_consulta_del_catalogo_por_un_rol_sin_permiso(client, crear_cuenta, cabecera, rol):
    usuario_id = crear_cuenta(rol)

    respuesta = client.get("/api/roles", headers=cabecera(usuario_id))

    assert respuesta.status_code == 403
    assert respuesta.get_json()["error"]["codigo"] == "permiso_insuficiente"
    assert "solicitante" not in respuesta.get_data(as_text=True)


def test_consulta_del_catalogo_sin_token(client, sesion):
    respuesta = client.get("/api/roles")

    assert respuesta.status_code == 401
    assert respuesta.get_json()["error"]["codigo"] == "token_ausente"
