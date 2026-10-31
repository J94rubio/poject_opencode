"""Servicios de autenticación.

Hash de contraseñas (design.md, D6): utilidades de Werkzeug con su algoritmo
por defecto, sin indicarlo en el código. El valor generado incluye algoritmo,
parámetros y sal, y la verificación lee el algoritmo del propio hash guardado.
"""

from werkzeug.security import check_password_hash, generate_password_hash


def generar_hash_password(password):
    return generate_password_hash(password)


def verificar_password(password_hash, password):
    return check_password_hash(password_hash, password)
