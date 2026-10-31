"""Servicios de autenticación.

Hash de contraseñas (design.md, D6): utilidades de Werkzeug con su algoritmo
por defecto, sin indicarlo en el código. El valor generado incluye algoritmo,
parámetros y sal, y la verificación lee el algoritmo del propio hash guardado.
"""

from functools import wraps

from flask import g, request
from werkzeug.security import check_password_hash, generate_password_hash

from ..usuarios import repositories as repositorio_usuarios
from .errors import (
    CredencialesInvalidas,
    DatosInvalidos,
    PermisoInsuficiente,
    TokenAusente,
    TokenInvalido,
    UsuarioDesactivado,
)
from .permissions import PERMISOS, tiene_permiso
from .tokens import TIPO_TOKEN, verificar_token


def generar_hash_password(password):
    return generate_password_hash(password)


def verificar_password(password_hash, password):
    return check_password_hash(password_hash, password)


def autenticar(correo, contrasena):
    """Valida las credenciales y devuelve el usuario autenticado.

    Correo inexistente y contraseña incorrecta producen el mismo error
    (`credenciales_invalidas`); la cuenta desactivada solo se distingue cuando
    las credenciales son correctas (design.md, D7).
    """
    if not _texto_no_vacio(correo) or not _texto_no_vacio(contrasena):
        raise DatosInvalidos()
    usuario = repositorio_usuarios.obtener_usuario_por_correo(correo)
    if usuario is None or not verificar_password(usuario.password_hash, contrasena):
        raise CredencialesInvalidas()
    if not usuario.activo:
        raise UsuarioDesactivado()
    return usuario


def _texto_no_vacio(valor):
    return isinstance(valor, str) and valor.strip() != ""


def token_de_la_cabecera():
    """Extrae el token de la cabecera `Authorization: Bearer <token>`."""
    cabecera = request.headers.get("Authorization")
    if cabecera is None:
        raise TokenAusente()
    partes = cabecera.split(" ")
    if len(partes) != 2 or partes[0] != TIPO_TOKEN or not partes[1]:
        raise TokenInvalido()
    return partes[1]


def usuario_del_token(token):
    """Carga el usuario del token con su rol vigente (design.md, D5).

    El rol se lee siempre de la base de datos, en una única consulta que une
    usuario y rol, así que un cambio de rol surte efecto en la petición
    siguiente y una cuenta desactivada pierde el acceso de inmediato.
    """
    usuario = repositorio_usuarios.obtener_usuario_por_id(verificar_token(token))
    if usuario is None:
        raise TokenInvalido()
    if not usuario.activo:
        raise UsuarioDesactivado()
    return usuario


def requiere_autenticacion(vista):
    """Guard de las rutas protegidas: valida el token y la cuenta antes de la lógica de negocio.

    Deja el usuario autenticado, con su rol vigente, en `g.usuario_actual`.
    """

    @wraps(vista)
    def _vista_protegida(*args, **kwargs):
        g.usuario_actual = usuario_del_token(token_de_la_cabecera())
        return vista(*args, **kwargs)

    return _vista_protegida


def requiere_permiso(permiso):
    """Guard que exige un permiso de la matriz (design.md, D1 y D8).

    Autentica la petición como `requiere_autenticacion` y, con el rol vigente
    del usuario, comprueba el permiso antes de ejecutar la lógica de negocio;
    si el rol no lo posee responde 403 con `permiso_insuficiente`. Declarar un
    permiso que no está en la matriz es un error de desarrollo y falla al
    definir la ruta.
    """
    if permiso not in PERMISOS:
        raise ValueError(f"Permiso no declarado en la matriz: {permiso!r}")

    def _decorador(vista):
        @wraps(vista)
        def _vista_con_permiso(*args, **kwargs):
            if not tiene_permiso(g.usuario_actual.rol.nombre, permiso):
                raise PermisoInsuficiente()
            return vista(*args, **kwargs)

        return requiere_autenticacion(_vista_con_permiso)

    return _decorador
