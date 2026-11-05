"""Comprobaciones técnicas de los datos de una petición, comunes a todos los módulos.

Evitan que un valor que la base o el hash de contraseñas no pueden procesar termine
en un error interno. Son límites técnicos, no reglas de negocio.
"""

from flask import request

# Máximo del tipo INTEGER de PostgreSQL (claves `id`). Un identificador fuera de ese
# rango no puede existir; se responde como inexistente sin consultar la base, que de
# otro modo fallaría con un error interno.
ID_MAXIMO = 2_147_483_647


def es_unicode_valido(texto):
    """Indica si el texto se puede codificar en UTF-8 (sin sustitutos UTF-16 sueltos)."""
    try:
        texto.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return True


def es_almacenable(texto):
    """Indica si PostgreSQL puede almacenar el texto (UTF-8 válido y sin NUL)."""
    return "\x00" not in texto and es_unicode_valido(texto)


def objeto_json_de_la_peticion():
    """Cuerpo de la petición si es un objeto JSON; `None` en cualquier otro caso.

    El anidamiento extremo es JSON sintácticamente válido, pero agota la recursión del
    decodificador con un error que `get_json(silent=True)` no controla.
    """
    try:
        datos = request.get_json(silent=True)
    except RecursionError:
        return None
    return datos if isinstance(datos, dict) else None
