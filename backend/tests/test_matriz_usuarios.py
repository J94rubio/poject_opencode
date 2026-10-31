"""Pruebas de la matriz de permisos sobre la gestión de usuarios (tarea 5.8).

Requisito «Jerarquía y matriz de permisos por rol» de la spec `auth`:
escenarios «La matriz respeta la jerarquía de roles», «Gestión de usuarios
denegada al solicitante», «Gestión de usuarios denegada al aprobador» y
«Gestión de usuarios permitida al administrador»; y requisito «Denegación de
acceso sin permiso» (los datos quedan intactos tras cada denegación).
"""

import pytest
from sqlalchemy import select

from backend.app.auth.permissions import PERMISOS, PERMISOS_POR_ROL
from backend.app.models import Usuario

ROLES_EN_ORDEN = ("solicitante", "aprobador", "admin")


# --- Jerarquía --------------------------------------------------------------


@pytest.mark.parametrize("permiso", sorted(PERMISOS))
def test_la_matriz_respeta_la_jerarquia_de_roles(permiso):
    """Si un rol posee un permiso, todos los roles superiores también lo poseen."""
    poseen = [permiso in PERMISOS_POR_ROL[rol] for rol in ROLES_EN_ORDEN]

    assert poseen == sorted(poseen)


def test_cada_rol_incluye_los_permisos_del_anterior():
    assert PERMISOS_POR_ROL["solicitante"] <= PERMISOS_POR_ROL["aprobador"]
    assert PERMISOS_POR_ROL["aprobador"] <= PERMISOS_POR_ROL["admin"]


# --- Denegación al solicitante y al aprobador -------------------------------


def _foto_de_cuentas(sesion):
    """Estado completo de todas las cuentas, para comprobar que nada cambia."""
    sesion.expire_all()
    return [
        (u.id, u.nombre, u.correo, u.rol_id, u.activo, u.password_hash, u.actualizado_en)
        for u in sesion.execute(select(Usuario).order_by(Usuario.id)).scalars()
    ]


OPERACIONES = {
    "listar": lambda c, h, objetivo: c.get("/api/usuarios", headers=h),
    "crear": lambda c, h, objetivo: c.post(
        "/api/usuarios",
        json={"nombre": "Nueva", "correo": "nueva@example.com", "contrasena": "contrasena-nueva",
              "rol": "admin"},
        headers=h,
    ),
    "editar": lambda c, h, objetivo: c.patch(
        f"/api/usuarios/{objetivo}", json={"nombre": "Modificado", "rol": "admin"}, headers=h
    ),
    "desactivar": lambda c, h, objetivo: c.post(f"/api/usuarios/{objetivo}/desactivar", headers=h),
}


@pytest.mark.parametrize("operacion", sorted(OPERACIONES))
@pytest.mark.parametrize("rol", ["solicitante", "aprobador"])
def test_gestion_de_usuarios_denegada(client, sesion, crear_cuenta, cabecera, rol, operacion):
    crear_cuenta("admin", nombre="Cuenta protegida")
    objetivo_id = crear_cuenta("solicitante", correo="objetivo@example.com")
    actor_id = crear_cuenta(rol, correo=f"{rol}-actor@example.com")
    antes = _foto_de_cuentas(sesion)

    respuesta = OPERACIONES[operacion](client, cabecera(actor_id), objetivo_id)

    assert respuesta.status_code == 403
    assert respuesta.get_json() == {
        "error": {"codigo": "permiso_insuficiente",
                  "mensaje": respuesta.get_json()["error"]["mensaje"]},
    }
    assert "Cuenta protegida" not in respuesta.get_data(as_text=True)
    assert _foto_de_cuentas(sesion) == antes


# --- Permitida al administrador ---------------------------------------------


def test_gestion_de_usuarios_permitida_al_administrador(client, sesion, crear_cuenta, cabecera):
    admin_id = crear_cuenta("admin")
    antes = len(_foto_de_cuentas(sesion))

    respuesta = OPERACIONES["crear"](client, cabecera(admin_id), None)

    assert respuesta.status_code == 201
    assert respuesta.get_json()["correo"] == "nueva@example.com"
    assert len(_foto_de_cuentas(sesion)) == antes + 1
