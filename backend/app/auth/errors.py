"""Excepciones de dominio y su traducción al contrato de errores (design.md, D7).

Formato de respuesta: {"error": {"codigo": "...", "mensaje": "..."}}.
El catálogo de excepciones concretas se completa en la tarea 3.1.
"""

from flask import jsonify


class ErrorDeDominio(Exception):
    """Base de las excepciones de dominio que se traducen a una respuesta de error."""

    http = 400
    codigo = "datos_invalidos"
    mensaje = "Los datos enviados no son válidos."

    def __init__(self, mensaje=None):
        super().__init__(mensaje or self.mensaje)
        if mensaje is not None:
            self.mensaje = mensaje


def respuesta_error(codigo, mensaje, http):
    return jsonify({"error": {"codigo": codigo, "mensaje": mensaje}}), http


def registrar_manejadores_errores(app):
    @app.errorhandler(ErrorDeDominio)
    def _manejar_error_de_dominio(error):
        return respuesta_error(error.codigo, error.mensaje, error.http)
