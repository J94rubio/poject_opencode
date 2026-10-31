"""Pruebas del guard de permisos (tarea 4.2).

Usan rutas de prueba registradas únicamente en estas pruebas, porque las rutas
reales de `usuarios` llegan en la sección 5.
"""

import pytest
from flask import g

from backend.app.auth.services import generar_hash_password, requiere_permiso
from backend.app.auth.tokens import emitir_token
from backend.app.extensions import db
from backend.app.usuarios import repositories


@pytest.fixture
def cliente_con_permisos(app):
    @app.get("/_prueba/lectura")
    @requiere_permiso("usuarios:ver")
    def _lectura():
        return {"datos": "protegidos", "rol": g.usuario_actual.rol.nombre}

    @app.post("/_prueba/escritura/<int:usuario_id>")
    @requiere_permiso("usuarios:editar")
    def _escritura(usuario_id):
        repositories.obtener_usuario_por_id(usuario_id).nombre = "Modificado"
        db.session.commit()
        return {"ok": True}

    @app.get("/_prueba/espacios")
    @requiere_permiso("espacios:crear")
    def _espacios():
        return {"ok": True}

    return app.test_client()


def _crear_usuario(sesion, rol, correo=None):
    usuario = repositories.crear_usuario(
        "Persona", correo or f"{rol}@example.com", generar_hash_password("contrasena-valida"),
        repositories.obtener_rol_por_nombre(rol),
    )
    sesion.commit()
    return usuario.id


def _cabecera(app, usuario_id):
    with app.app_context():
        return {"Authorization": f"Bearer {emitir_token(usuario_id)}"}


def _codigo(respuesta):
    return respuesta.get_json()["error"]["codigo"]


# --- Acceso permitido -------------------------------------------------------


def test_acceso_permitido_al_rol_con_el_permiso(app, sesion, cliente_con_permisos):
    admin_id = _crear_usuario(sesion, "admin")

    respuesta = cliente_con_permisos.get("/_prueba/lectura", headers=_cabecera(app, admin_id))

    assert respuesta.status_code == 200
    assert respuesta.get_json() == {"datos": "protegidos", "rol": "admin"}


@pytest.mark.parametrize("rol", ["aprobador", "admin"])
def test_acceso_permitido_por_jerarquia(app, sesion, cliente_con_permisos, rol):
    usuario_id = _crear_usuario(sesion, rol)

    respuesta = cliente_con_permisos.get("/_prueba/espacios", headers=_cabecera(app, usuario_id))

    assert respuesta.status_code == 200


def test_escritura_permitida_modifica_los_datos(app, sesion, cliente_con_permisos):
    admin_id = _crear_usuario(sesion, "admin")
    objetivo_id = _crear_usuario(sesion, "solicitante")

    respuesta = cliente_con_permisos.post(
        f"/_prueba/escritura/{objetivo_id}", headers=_cabecera(app, admin_id)
    )

    assert respuesta.status_code == 200
    sesion.expire_all()
    assert repositories.obtener_usuario_por_id(objetivo_id).nombre == "Modificado"


# --- Acceso denegado por rol ------------------------------------------------


@pytest.mark.parametrize("rol", ["solicitante", "aprobador"])
def test_lectura_denegada_por_rol(app, sesion, cliente_con_permisos, rol):
    usuario_id = _crear_usuario(sesion, rol)

    respuesta = cliente_con_permisos.get("/_prueba/lectura", headers=_cabecera(app, usuario_id))

    assert respuesta.status_code == 403
    assert _codigo(respuesta) == "permiso_insuficiente"
    assert "protegidos" not in respuesta.get_data(as_text=True)


@pytest.mark.parametrize("rol", ["solicitante", "aprobador"])
def test_escritura_denegada_por_rol_no_modifica_datos(app, sesion, cliente_con_permisos, rol):
    usuario_id = _crear_usuario(sesion, rol)
    objetivo_id = _crear_usuario(sesion, "solicitante", correo="objetivo@example.com")

    respuesta = cliente_con_permisos.post(
        f"/_prueba/escritura/{objetivo_id}", headers=_cabecera(app, usuario_id)
    )

    assert respuesta.status_code == 403
    assert _codigo(respuesta) == "permiso_insuficiente"
    sesion.expire_all()
    assert repositories.obtener_usuario_por_id(objetivo_id).nombre == "Persona"


def test_permiso_de_rol_superior_denegado_al_solicitante(app, sesion, cliente_con_permisos):
    usuario_id = _crear_usuario(sesion, "solicitante")

    respuesta = cliente_con_permisos.get("/_prueba/espacios", headers=_cabecera(app, usuario_id))

    assert respuesta.status_code == 403
    assert _codigo(respuesta) == "permiso_insuficiente"


def test_el_permiso_se_evalua_con_el_rol_vigente(app, sesion, cliente_con_permisos):
    usuario_id = _crear_usuario(sesion, "solicitante")
    cabecera = _cabecera(app, usuario_id)
    assert cliente_con_permisos.get("/_prueba/lectura", headers=cabecera).status_code == 403

    repositories.obtener_usuario_por_id(usuario_id).rol = repositories.obtener_rol_por_nombre(
        "admin"
    )
    sesion.commit()

    assert cliente_con_permisos.get("/_prueba/lectura", headers=cabecera).status_code == 200


# --- El guard autentica antes de comprobar el permiso -----------------------


def test_sin_token_responde_401_antes_que_403(cliente_con_permisos):
    respuesta = cliente_con_permisos.get("/_prueba/lectura")

    assert respuesta.status_code == 401
    assert _codigo(respuesta) == "token_ausente"


def test_permiso_no_declarado_en_la_matriz_es_error_de_desarrollo():
    with pytest.raises(ValueError):
        requiere_permiso("usuarios:borrar")
