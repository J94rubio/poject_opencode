"""Coherencia de `backend/README.md` con la implementación (tarea 5.7).

Comprueba que los endpoints y los ejemplos del documento corresponden a rutas
registradas y protegidas con el permiso indicado, y que el catálogo de códigos
de error coincide con los códigos y los HTTP implementados.
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


def _errores_implementados():
    dominio = {
        clase.codigo: clase.http
        for clase in errors.ErrorDeDominio.__subclasses__()
    }
    return {**dominio, **ERRORES_DEL_FRAMEWORK}


def _a_regla_flask(ruta):
    return ruta.replace("{id}", "<int:usuario_id>")


def _rutas_registradas(app):
    return {(regla.rule, metodo) for regla in app.url_map.iter_rules() for metodo in regla.methods}


def test_el_documento_lista_los_endpoints_del_modulo_usuarios():
    assert len(ENDPOINTS) == 8
    assert len(EJEMPLOS) >= 8


@pytest.mark.parametrize("metodo,ruta,permiso", ENDPOINTS)
def test_cada_endpoint_documentado_existe_y_exige_su_permiso(
    app, client, crear_cuenta, cabecera, metodo, ruta, permiso
):
    assert (_a_regla_flask(ruta), metodo) in _rutas_registradas(app)
    # El permiso documentado es de la matriz y solo lo posee el `admin`.
    assert permiso in PERMISOS_POR_ROL["admin"]
    assert permiso not in PERMISOS_POR_ROL["aprobador"]

    url = ruta.replace("{id}", "1")
    assert client.open(url, method=metodo).get_json()["error"]["codigo"] == "token_ausente"
    aprobador = cabecera(crear_cuenta("aprobador"))
    respuesta = client.open(url, method=metodo, headers=aprobador, json={})
    assert respuesta.get_json()["error"]["codigo"] == "permiso_insuficiente"


@pytest.mark.parametrize("metodo,ruta", EJEMPLOS)
def test_cada_ejemplo_corresponde_a_una_ruta_registrada(app, metodo, ruta):
    regla = re.sub(r"/\d+(?=/|$)", "/<int:usuario_id>", ruta)
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
