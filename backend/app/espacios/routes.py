"""Rutas del catálogo de espacios (`/api/espacios`; design.md, D3 y D6).

Cada ruta declara su permiso de la matriz; el guard `requiere_permiso`
autentica la petición y lo comprueba antes de la lógica. Las validaciones y
las transiciones de estado viven en la capa de servicios (D4).
"""

from flask import Blueprint, jsonify

from ..auth.services import requiere_permiso
from ..usuarios.routes import _cuerpo_json
from . import services

bp = Blueprint("espacios", __name__, url_prefix="/api")


def datos_de_espacio(espacio):
    """Representación de un espacio: exactamente id, nombre, tipo, capacidad y estado (D6)."""
    return {
        "id": espacio.id,
        "nombre": espacio.nombre,
        "tipo": espacio.tipo,
        "capacidad": espacio.capacidad,
        "estado": espacio.estado,
    }


@bp.get("/espacios")
@requiere_permiso("espacios:ver")
def listar_espacios():
    return jsonify([datos_de_espacio(e) for e in services.listar_espacios()])


@bp.post("/espacios")
@requiere_permiso("espacios:crear")
def crear_espacio():
    espacio = services.crear_espacio(_cuerpo_json())
    return datos_de_espacio(espacio), 201


@bp.get("/espacios/<int:espacio_id>")
@requiere_permiso("espacios:ver")
def obtener_espacio(espacio_id):
    return datos_de_espacio(services.obtener_espacio(espacio_id))


@bp.patch("/espacios/<int:espacio_id>")
@requiere_permiso("espacios:editar")
def editar_espacio(espacio_id):
    return datos_de_espacio(services.editar_espacio(espacio_id, _cuerpo_json()))


@bp.post("/espacios/<int:espacio_id>/desactivar")
@requiere_permiso("espacios:desactivar")
def desactivar_espacio(espacio_id):
    return datos_de_espacio(services.desactivar_espacio(espacio_id))


@bp.post("/espacios/<int:espacio_id>/activar")
@requiere_permiso("espacios:activar")
def activar_espacio(espacio_id):
    return datos_de_espacio(services.activar_espacio(espacio_id))
