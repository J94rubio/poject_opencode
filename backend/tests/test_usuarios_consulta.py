"""Pruebas del listado `GET /api/usuarios` y del detalle `GET /api/usuarios/{id}` (tarea 5.2).

Requisitos «Listado de cuentas de usuario», «Consulta del detalle de una
cuenta» y «Almacenamiento seguro de las contraseñas» (el detalle no expone
credenciales) de la spec `usuarios`.
"""

import pytest

from backend.app.usuarios import repositories


def _codigo(respuesta):
    return respuesta.get_json()["error"]["codigo"]


def _sin_credenciales(respuesta):
    texto = respuesta.get_data(as_text=True)
    return "contrasena-valida" not in texto and "password" not in texto and "hash" not in texto


# --- Listado ----------------------------------------------------------------


def test_listado_solicitado_por_el_administrador(client, crear_cuenta, cabecera):
    admin_id = crear_cuenta("admin", nombre="Admin")
    otro_id = crear_cuenta("aprobador", nombre="Aprobadora")

    respuesta = client.get("/api/usuarios", headers=cabecera(admin_id))

    assert respuesta.status_code == 200
    assert respuesta.get_json() == [
        {"id": admin_id, "nombre": "Admin", "correo": "admin@example.com", "rol": "admin",
         "activo": True},
        {"id": otro_id, "nombre": "Aprobadora", "correo": "aprobador@example.com",
         "rol": "aprobador", "activo": True},
    ]
    assert _sin_credenciales(respuesta)


def test_el_listado_incluye_cuentas_desactivadas(client, sesion, crear_cuenta, cabecera):
    admin_id = crear_cuenta("admin")
    inactiva_id = crear_cuenta("solicitante", nombre="Inactiva", activo=False)

    respuesta = client.get("/api/usuarios", headers=cabecera(admin_id))

    assert respuesta.status_code == 200
    inactiva = next(u for u in respuesta.get_json() if u["id"] == inactiva_id)
    assert inactiva == {
        "id": inactiva_id, "nombre": "Inactiva", "correo": "solicitante@example.com",
        "rol": "solicitante", "activo": False,
    }
    sesion.expire_all()
    assert repositories.obtener_usuario_por_id(inactiva_id).nombre == "Inactiva"


@pytest.mark.parametrize("rol", ["solicitante", "aprobador"])
def test_listado_solicitado_por_un_rol_sin_permiso(client, crear_cuenta, cabecera, rol):
    crear_cuenta("admin", nombre="Cuenta protegida")
    usuario_id = crear_cuenta(rol)

    respuesta = client.get("/api/usuarios", headers=cabecera(usuario_id))

    assert respuesta.status_code == 403
    assert _codigo(respuesta) == "permiso_insuficiente"
    texto = respuesta.get_data(as_text=True)
    assert "Cuenta protegida" not in texto and "admin@example.com" not in texto


# --- Detalle ----------------------------------------------------------------


def test_detalle_de_una_cuenta_existente(client, crear_cuenta, cabecera):
    admin_id = crear_cuenta("admin")
    objetivo_id = crear_cuenta("solicitante", nombre="Marta Ruiz", correo="marta@example.com")

    respuesta = client.get(f"/api/usuarios/{objetivo_id}", headers=cabecera(admin_id))

    assert respuesta.status_code == 200
    assert respuesta.get_json() == {
        "id": objetivo_id, "nombre": "Marta Ruiz", "correo": "marta@example.com",
        "rol": "solicitante", "activo": True,
    }


def test_el_detalle_de_usuario_no_expone_credenciales(client, crear_cuenta, cabecera):
    admin_id = crear_cuenta("admin")
    objetivo_id = crear_cuenta("solicitante")

    respuesta = client.get(f"/api/usuarios/{objetivo_id}", headers=cabecera(admin_id))

    assert respuesta.status_code == 200
    assert _sin_credenciales(respuesta)


def test_detalle_de_una_cuenta_inexistente(client, crear_cuenta, cabecera):
    admin_id = crear_cuenta("admin")

    respuesta = client.get("/api/usuarios/999999", headers=cabecera(admin_id))

    assert respuesta.status_code == 404
    assert _codigo(respuesta) == "usuario_no_encontrado"


@pytest.mark.parametrize("rol", ["solicitante", "aprobador"])
def test_detalle_solicitado_por_un_rol_sin_permiso(client, crear_cuenta, cabecera, rol):
    objetivo_id = crear_cuenta("admin", nombre="Cuenta protegida")
    usuario_id = crear_cuenta(rol)

    respuesta = client.get(f"/api/usuarios/{objetivo_id}", headers=cabecera(usuario_id))

    assert respuesta.status_code == 403
    assert _codigo(respuesta) == "permiso_insuficiente"
    assert "Cuenta protegida" not in respuesta.get_data(as_text=True)
