"""Excepciones de dominio y su traducción al contrato de errores (design.md, D7).

Formato de respuesta: {"error": {"codigo": "...", "mensaje": "..."}}.

Los mensajes son textos fijos del catálogo: las excepciones no aceptan un
mensaje propio, de modo que ninguna respuesta puede incluir datos de la
petición (correo, contraseña, token) ni detalle técnico del fallo.
"""

from flask import jsonify
from werkzeug.exceptions import BadRequest, HTTPException, MethodNotAllowed, NotFound


class ErrorDeDominio(Exception):
    """Base de las excepciones de dominio que se traducen a una respuesta de error."""

    http = 400
    codigo = "datos_invalidos"
    mensaje = "Los datos enviados no son válidos."

    def __init__(self):
        super().__init__(self.codigo)


class DatosInvalidos(ErrorDeDominio):
    http = 400
    codigo = "datos_invalidos"
    mensaje = "Los datos enviados no son válidos."


class ContrasenaInvalida(ErrorDeDominio):
    http = 400
    codigo = "contrasena_invalida"
    mensaje = "La contraseña debe tener al menos 8 caracteres."


class RolInvalido(ErrorDeDominio):
    http = 400
    codigo = "rol_invalido"
    mensaje = "El rol indicado no pertenece al catálogo de roles."


class CredencialesInvalidas(ErrorDeDominio):
    http = 401
    codigo = "credenciales_invalidas"
    mensaje = "El correo o la contraseña no son correctos."


class UsuarioDesactivado(ErrorDeDominio):
    http = 401
    codigo = "usuario_desactivado"
    mensaje = "La cuenta está desactivada."


class TokenAusente(ErrorDeDominio):
    http = 401
    codigo = "token_ausente"
    mensaje = "Se requiere un token de acceso."


class TokenInvalido(ErrorDeDominio):
    http = 401
    codigo = "token_invalido"
    mensaje = "El token de acceso no es válido."


class TokenExpirado(ErrorDeDominio):
    http = 401
    codigo = "token_expirado"
    mensaje = "El token de acceso ha expirado."


class PermisoInsuficiente(ErrorDeDominio):
    http = 403
    codigo = "permiso_insuficiente"
    mensaje = "No tiene permiso para realizar esta operación."


class UsuarioNoEncontrado(ErrorDeDominio):
    http = 404
    codigo = "usuario_no_encontrado"
    mensaje = "El usuario solicitado no existe."


class CorreoDuplicado(ErrorDeDominio):
    http = 409
    codigo = "correo_duplicado"
    mensaje = "El correo ya está registrado."


class OperacionNoPermitida(ErrorDeDominio):
    http = 409
    codigo = "operacion_no_permitida"
    mensaje = "La operación no está permitida sobre la propia cuenta."


# --- Espacios (change `espacios`, design.md D5) ------------------------------


class TipoEspacioInvalido(ErrorDeDominio):
    http = 400
    codigo = "tipo_espacio_invalido"
    mensaje = "El tipo de espacio no pertenece al catálogo de tipos."


class CapacidadInvalida(ErrorDeDominio):
    http = 400
    codigo = "capacidad_invalida"
    mensaje = "La capacidad debe ser un número entero mayor que cero."


class EspacioDuplicado(ErrorDeDominio):
    http = 409
    codigo = "espacio_duplicado"
    mensaje = "Ya existe un espacio con ese nombre."


class EspacioNoEncontrado(ErrorDeDominio):
    http = 404
    codigo = "espacio_no_encontrado"
    mensaje = "El espacio solicitado no existe."


class EspacioYaInactivo(ErrorDeDominio):
    http = 409
    codigo = "espacio_ya_inactivo"
    mensaje = "El espacio ya está inactivo."


class EspacioYaActivo(ErrorDeDominio):
    http = 409
    codigo = "espacio_ya_activo"
    mensaje = "El espacio ya está activo."



# --- Reservas (change `reservas-disponibilidad`) ----------------------------


class EspacioInactivo(ErrorDeDominio):
    http = 400
    codigo = "espacio_inactivo"
    mensaje = "El espacio está inactivo y no admite solicitudes."


class ReservaSolapada(ErrorDeDominio):
    http = 409
    codigo = "reserva_solapada"
    mensaje = "El rango se solapa con una reserva aprobada del espacio."


class SolicitudNoEncontrada(ErrorDeDominio):
    http = 404
    codigo = "solicitud_no_encontrada"
    mensaje = "La solicitud de reserva no existe."


MENSAJE_RUTA_NO_ENCONTRADA ="La ruta solicitada no existe."
MENSAJE_METODO_NO_PERMITIDO = "El método HTTP no está permitido en esta ruta."
MENSAJE_ERROR_INTERNO = "Se produjo un error interno."


def respuesta_error(codigo, mensaje, http):
    return jsonify({"error": {"codigo": codigo, "mensaje": mensaje}}), http


def registrar_manejadores_errores(app):
    @app.errorhandler(ErrorDeDominio)
    def _manejar_error_de_dominio(error):
        return respuesta_error(error.codigo, error.mensaje, error.http)

    @app.errorhandler(NotFound)
    def _manejar_ruta_no_encontrada(_error):
        return respuesta_error("ruta_no_encontrada", MENSAJE_RUTA_NO_ENCONTRADA, 404)

    @app.errorhandler(MethodNotAllowed)
    def _manejar_metodo_no_permitido(_error):
        return respuesta_error("metodo_no_permitido", MENSAJE_METODO_NO_PERMITIDO, 405)

    @app.errorhandler(BadRequest)
    def _manejar_peticion_mal_formada(_error):
        # Incluye el cuerpo JSON mal formado (`request.get_json()`).
        return respuesta_error(DatosInvalidos.codigo, DatosInvalidos.mensaje, 400)

    @app.errorhandler(Exception)
    def _manejar_error_interno(error):
        if isinstance(error, HTTPException):
            # Otros errores HTTP fuera del contrato conservan su respuesta.
            return error
        app.logger.exception("Error interno no controlado")
        return respuesta_error("error_interno", MENSAJE_ERROR_INTERNO, 500)
