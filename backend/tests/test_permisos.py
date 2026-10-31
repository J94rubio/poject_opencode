"""Pruebas unitarias de la matriz de permisos (tarea 4.1).

La matriz esperada se transcribe de la spec `auth` (requisito «Jerarquía y
matriz de permisos por rol») y de design.md, D2.
"""

import pytest

from backend.app.auth.permissions import PERMISOS, PERMISOS_POR_ROL, tiene_permiso

ROLES = ("solicitante", "aprobador", "admin")

# Permiso: (solicitante, aprobador, admin)
MATRIZ_DE_LA_SPEC = {
    "espacios:ver": (True, True, True),
    "espacios:crear": (False, True, True),
    "espacios:editar": (False, True, True),
    "espacios:desactivar": (False, True, True),
    "espacios:activar": (False, True, True),
    "reservas:crear": (True, True, True),
    "reservas:ver_propias": (True, True, True),
    "reservas:cancelar_propia": (True, True, True),
    "reservas:ver_todas": (False, True, True),
    "aprobaciones:aprobar": (False, True, True),
    "aprobaciones:rechazar": (False, True, True),
    "historial:ver_propio": (True, True, True),
    "historial:ver_todos": (False, True, True),
    "usuarios:ver": (False, False, True),
    "usuarios:crear": (False, False, True),
    "usuarios:editar": (False, False, True),
    "usuarios:desactivar": (False, False, True),
    "usuarios:activar": (False, False, True),
    "usuarios:resetear_password": (False, False, True),
    "roles:ver": (False, False, True),
}


def _permisos_esperados(rol):
    indice = ROLES.index(rol)
    return {permiso for permiso, roles in MATRIZ_DE_LA_SPEC.items() if roles[indice]}


def test_la_matriz_declara_exactamente_los_roles_del_catalogo():
    assert set(PERMISOS_POR_ROL) == set(ROLES)


def test_el_catalogo_de_permisos_coincide_con_la_spec():
    assert PERMISOS == set(MATRIZ_DE_LA_SPEC)


@pytest.mark.parametrize("rol", ROLES)
def test_cada_rol_tiene_exactamente_los_permisos_de_la_matriz(rol):
    assert PERMISOS_POR_ROL[rol] == _permisos_esperados(rol)


@pytest.mark.parametrize("rol", ROLES)
@pytest.mark.parametrize("permiso", sorted(MATRIZ_DE_LA_SPEC))
def test_tiene_permiso_coincide_con_cada_celda_de_la_matriz(rol, permiso):
    assert tiene_permiso(rol, permiso) is MATRIZ_DE_LA_SPEC[permiso][ROLES.index(rol)]


def test_la_matriz_respeta_la_jerarquia_de_roles():
    assert PERMISOS_POR_ROL["solicitante"] <= PERMISOS_POR_ROL["aprobador"]
    assert PERMISOS_POR_ROL["aprobador"] <= PERMISOS_POR_ROL["admin"]


@pytest.mark.parametrize("permiso", sorted(MATRIZ_DE_LA_SPEC))
def test_los_roles_que_poseen_cada_permiso_respetan_la_jerarquia(permiso):
    solicitante, aprobador, admin = (tiene_permiso(rol, permiso) for rol in ROLES)

    assert not solicitante or aprobador
    assert not aprobador or admin


def test_un_rol_fuera_del_catalogo_no_tiene_permisos():
    assert not tiene_permiso("invitado", "espacios:ver")


def test_un_permiso_no_declarado_no_lo_tiene_ningun_rol():
    assert not any(tiene_permiso(rol, "usuarios:borrar") for rol in ROLES)
