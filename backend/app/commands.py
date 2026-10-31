"""Comando `flask create-admin`: crea la primera cuenta administradora (design.md, D9).

El correo se toma de `--correo` o, si no se indica, de `ADMIN_CORREO`. La
contraseña nunca se acepta como argumento (quedaría en el historial del shell
y en la lista de procesos): se lee de `ADMIN_CONTRASENA` o, si falta y hay una
terminal interactiva, se pide oculta con confirmación. Ningún mensaje del
comando incluye la contraseña ni el correo.
"""

import os
import sys

import click
from flask.cli import with_appcontext

from .auth.errors import ContrasenaInvalida, CorreoDuplicado, DatosInvalidos
from .usuarios import services

VARIABLE_CORREO = "ADMIN_CORREO"
VARIABLE_CONTRASENA = "ADMIN_CONTRASENA"


def _hay_terminal():
    return sys.stdin.isatty()


def _leer_correo(correo):
    correo = correo or os.environ.get(VARIABLE_CORREO)
    if not correo:
        raise click.ClickException(
            f"Falta el correo: indíquelo con --correo o con la variable {VARIABLE_CORREO}."
        )
    return correo


def _leer_contrasena():
    contrasena = os.environ.get(VARIABLE_CONTRASENA)
    if contrasena:
        return contrasena
    if not _hay_terminal():
        raise click.ClickException(
            f"Falta la contraseña: defina la variable {VARIABLE_CONTRASENA} o ejecute "
            "el comando en una terminal interactiva para introducirla de forma oculta."
        )
    return click.prompt(
        "Contraseña", hide_input=True, confirmation_prompt="Repita la contraseña"
    )


@click.command("create-admin")
@click.option("--correo", default=None, help=f"Correo del administrador (o {VARIABLE_CORREO}).")
@with_appcontext
def create_admin(correo):
    """Crea la cuenta administradora inicial si no hay ningún administrador activo."""
    correo = _leer_correo(correo)
    contrasena = _leer_contrasena()
    try:
        usuario = services.crear_primer_admin(correo, contrasena)
    except services.YaExisteAdministradorActivo:
        raise click.ClickException(
            "Ya existe un administrador activo; no se ha creado ninguna cuenta."
        ) from None
    except ContrasenaInvalida:
        raise click.ClickException(
            "La contraseña debe tener al menos 8 caracteres; no se ha creado ninguna cuenta."
        ) from None
    except CorreoDuplicado:
        raise click.ClickException(
            "El correo ya está registrado; no se ha creado ninguna cuenta."
        ) from None
    except DatosInvalidos:
        raise click.ClickException(
            "El correo no tiene un formato válido; no se ha creado ninguna cuenta."
        ) from None
    click.echo(f"Cuenta administradora creada (id {usuario.id}).")


def registrar_comandos(app):
    app.cli.add_command(create_admin)
