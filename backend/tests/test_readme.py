"""Coherencia de `backend/README.md` con la implementación.

Tarea 5.7 de `usuarios-roles-auth`, generalizada en la tarea 3.6 de
`espacios` a todos los módulos documentados y ampliada en la tarea 4.2 de
`reservas-disponibilidad` con el módulo `reservas`. Comprueba que los endpoints y
los ejemplos del documento corresponden a rutas registradas y protegidas con
el permiso indicado, que toda ruta protegida por permiso está documentada y
que el catálogo de códigos de error coincide con los códigos y los HTTP
implementados.
"""

import re
from pathlib import Path

import pytest

from backend.app.auth import errors
from backend.app.auth.permissions import PERMISOS_POR_ROL

README = (Path(__file__).resolve().parent.parent / "README.md").read_text(encoding="utf-8")

_FILA_ENDPOINT = re.compile(r"^\| `(GET|POST|PATCH)` \| `(/api/[^`]+)` \| `([^`]+)` \|", re.M)
_FILA_ERROR = re.compile(r"^\| `([a-z_]+)` \| (\d{3}) \|", re.M)
_EJEMPLO_HTTP = re.compile(r"^(GET|POST|PATCH) (/api/\S+)$", re.M)

ENDPOINTS = _FILA_ENDPOINT.findall(README)
ERRORES = {codigo: int(http) for codigo, http in _FILA_ERROR.findall(README)}
EJEMPLOS = _EJEMPLO_HTTP.findall(README)

ERRORES_DEL_FRAMEWORK = {"ruta_no_encontrada": 404, "metodo_no_permitido": 405, "error_interno": 500}

# Roles de menor a mayor privilegio (jerarquía de la matriz).
ROLES = ["solicitante", "aprobador", "admin"]

# Endpoints documentados por módulo.
ENDPOINTS_POR_MODULO = {"usuarios": 8, "espacios": 6, "reservas": 4}

# Blueprints cuyas rutas no exigen un permiso de la matriz (login y sesión).
BLUEPRINTS_SIN_PERMISO = {"auth"}

_METODOS_DOCUMENTABLES = {"GET", "POST", "PATCH", "PUT", "DELETE"}


def _errores_implementados():
    dominio = {
        clase.codigo: clase.http
        for clase in errors.ErrorDeDominio.__subclasses__()
    }
    return {**dominio, **ERRORES_DEL_FRAMEWORK}


def _normalizar_regla(regla):
    """`/api/x/<int:cualquier_nombre>` → `/api/x/{id}`, para cualquier parámetro."""
    return re.sub(r"<[^>]+>", "{id}", regla)


def _rutas_registradas(app):
    return {
        (_normalizar_regla(regla.rule), metodo)
        for regla in app.url_map.iter_rules()
        for metodo in regla.methods
    }


def _rutas_con_permiso(app):
    """Rutas `/api` de los módulos protegidos por permiso, con sus métodos."""
    return {
        (metodo, _normalizar_regla(regla.rule))
        for regla in app.url_map.iter_rules()
        if regla.rule.startswith("/api/")
        and regla.endpoint.split(".")[0] not in BLUEPRINTS_SIN_PERMISO
        for metodo in regla.methods & _METODOS_DOCUMENTABLES
    }


def _modulo(ruta):
    """Módulo de una ruta documentada; coincide con el blueprint que la registra.

    La disponibilidad (`/api/espacios/{id}/disponibilidad`) cuelga del recurso
    espacio, pero pertenece al módulo `reservas`.
    """
    if ruta.endswith("/disponibilidad"):
        return "reservas"
    segmento = ruta.split("/")[2]
    return "usuarios" if segmento in {"usuarios", "roles"} else segmento


def _blueprint_de(app, metodo, ruta):
    return next(
        regla.endpoint.split(".")[0]
        for regla in app.url_map.iter_rules()
        if _normalizar_regla(regla.rule) == ruta and metodo in regla.methods
    )


def test_el_documento_lista_los_endpoints_de_cada_modulo():
    por_modulo = {}
    for _, ruta, _ in ENDPOINTS:
        por_modulo[_modulo(ruta)] = por_modulo.get(_modulo(ruta), 0) + 1
    assert por_modulo == ENDPOINTS_POR_MODULO
    assert len(ENDPOINTS) == len(set(ENDPOINTS)) == sum(ENDPOINTS_POR_MODULO.values())
    assert len(EJEMPLOS) >= len(ENDPOINTS)


def test_cada_ruta_implementada_con_permiso_esta_documentada(app):
    documentadas = {(metodo, ruta) for metodo, ruta, _ in ENDPOINTS}
    assert _rutas_con_permiso(app) == documentadas


@pytest.mark.parametrize("metodo,ruta,permiso", ENDPOINTS)
def test_cada_endpoint_documentado_pertenece_a_su_modulo(app, metodo, ruta, permiso):
    assert _blueprint_de(app, metodo, ruta) == _modulo(ruta)


@pytest.mark.parametrize("metodo,ruta,permiso", ENDPOINTS)
def test_cada_endpoint_documentado_existe_y_exige_su_permiso(
    app, client, crear_cuenta, cabecera, metodo, ruta, permiso
):
    assert (ruta, metodo) in _rutas_registradas(app)
    # El permiso documentado es de la matriz (el `admin` los posee todos).
    assert permiso in PERMISOS_POR_ROL["admin"]

    url = ruta.replace("{id}", "1")
    assert client.open(url, method=metodo).get_json()["error"]["codigo"] == "token_ausente"

    sin_permiso = [rol for rol in ROLES if permiso not in PERMISOS_POR_ROL[rol]]
    con_permiso = [rol for rol in ROLES if permiso in PERMISOS_POR_ROL[rol]]

    # El rol de mayor privilegio que carece del permiso recibe 403. Si todos
    # los roles lo poseen (por ejemplo, `espacios:ver`), no hay a quién negarlo.
    if sin_permiso:
        denegado = cabecera(crear_cuenta(sin_permiso[-1]))
        respuesta = client.open(url, method=metodo, headers=denegado, json={})
        assert respuesta.get_json()["error"]["codigo"] == "permiso_insuficiente"

    # El rol de menor privilegio que posee el permiso supera el guard.
    permitido = cabecera(crear_cuenta(con_permiso[0], correo=f"{con_permiso[0]}.ok@example.com"))
    respuesta = client.open(url, method=metodo, headers=permitido, json={})
    assert respuesta.status_code not in (401, 403)


@pytest.mark.parametrize(
    "permiso", sorted({p for _, ruta, p in ENDPOINTS if _modulo(ruta) == "usuarios"})
)
def test_los_permisos_del_modulo_usuarios_son_solo_del_admin(permiso):
    # El documento afirma que la gestión de usuarios y roles es exclusiva del `admin`.
    assert [rol for rol in ROLES if permiso in PERMISOS_POR_ROL[rol]] == ["admin"]


@pytest.mark.parametrize("metodo,ruta", EJEMPLOS)
def test_cada_ejemplo_corresponde_a_una_ruta_registrada(app, metodo, ruta):
    # La cadena de consulta (`?inicio=...&fin=...`) no forma parte de la ruta.
    regla = re.sub(r"/\d+(?=/|$)", "/{id}", ruta.split("?")[0])
    assert (regla, metodo) in _rutas_registradas(app)


def test_el_catalogo_de_errores_coincide_con_el_implementado():
    assert ERRORES == _errores_implementados()


def test_el_ejemplo_de_error_usa_el_mensaje_del_catalogo():
    assert (
        '{"error": {"codigo": "permiso_insuficiente", "mensaje": "'
        f'{errors.PermisoInsuficiente.mensaje}"}}}}'
    ) in README


def test_errores_del_framework_documentados(client):
    assert client.get("/api/no-existe").status_code == ERRORES["ruta_no_encontrada"]
    assert client.delete("/api/roles").status_code == ERRORES["metodo_no_permitido"]
