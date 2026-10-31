"""Comando `flask create-admin` (spec `usuarios`, requisito «Creación del primer
administrador por línea de comandos»; design.md, D9).

Todas las credenciales de estas pruebas son valores ficticios.
"""

import pytest
from sqlalchemy import func, select

from backend.app import commands
from backend.app.auth.services import verificar_password
from backend.app.models import Usuario

CORREO = "primer.admin@example.com"
CONTRASENA = "contrasena-de-prueba"


@pytest.fixture(autouse=True)
def sin_variables_admin(monkeypatch):
    """Aísla las pruebas de las variables que pudiera tener la terminal."""
    monkeypatch.delenv(commands.VARIABLE_CORREO, raising=False)
    monkeypatch.delenv(commands.VARIABLE_CONTRASENA, raising=False)


@pytest.fixture
def ejecutar(app, sesion):
    runner = app.test_cli_runner()

    def _ejecutar(*args, env=None, input=None):
        return runner.invoke(args=["create-admin", *args], env=env, input=input)

    return _ejecutar


def _contar(sesion):
    sesion.expire_all()
    return sesion.execute(select(func.count(Usuario.id))).scalar_one()


def _admin(sesion, correo=CORREO):
    sesion.expire_all()
    return sesion.execute(select(Usuario).where(Usuario.correo == correo)).scalar_one_or_none()


def _sin_credenciales_en_salida(resultado, *valores):
    for valor in valores:
        assert valor not in resultado.output


# --- Creación correcta -------------------------------------------------------


def test_creacion_del_primer_admin_con_opcion_y_variable(sesion, ejecutar):
    resultado = ejecutar("--correo", CORREO, env={"ADMIN_CONTRASENA": CONTRASENA})

    assert resultado.exit_code == 0, resultado.output
    usuario = _admin(sesion)
    assert usuario.rol.nombre == "admin"
    assert usuario.activo is True
    assert usuario.nombre == "Administrador"
    assert usuario.password_hash != CONTRASENA
    assert verificar_password(usuario.password_hash, CONTRASENA)
    _sin_credenciales_en_salida(resultado, CONTRASENA, CORREO)


def test_creacion_con_correo_desde_la_variable(sesion, ejecutar):
    resultado = ejecutar(env={"ADMIN_CORREO": CORREO, "ADMIN_CONTRASENA": CONTRASENA})

    assert resultado.exit_code == 0, resultado.output
    assert _admin(sesion).rol.nombre == "admin"


def test_la_opcion_correo_tiene_prioridad_sobre_la_variable(sesion, ejecutar):
    resultado = ejecutar(
        "--correo", CORREO,
        env={"ADMIN_CORREO": "variable@example.com", "ADMIN_CONTRASENA": CONTRASENA},
    )

    assert resultado.exit_code == 0, resultado.output
    assert _admin(sesion) is not None
    assert _admin(sesion, "variable@example.com") is None


def test_el_correo_se_guarda_en_minusculas(sesion, ejecutar):
    resultado = ejecutar("--correo", "Primer.Admin@Example.com", env={"ADMIN_CONTRASENA": CONTRASENA})

    assert resultado.exit_code == 0, resultado.output
    assert _admin(sesion) is not None


def test_creacion_si_solo_hay_un_admin_desactivado(sesion, crear_cuenta, ejecutar):
    crear_cuenta("admin", correo="antiguo@example.com", activo=False)

    resultado = ejecutar("--correo", CORREO, env={"ADMIN_CONTRASENA": CONTRASENA})

    assert resultado.exit_code == 0, resultado.output
    assert _admin(sesion).activo is True


def test_contrasena_pedida_de_forma_oculta_con_confirmacion(sesion, ejecutar, monkeypatch):
    monkeypatch.setattr(commands, "_hay_terminal", lambda: True)

    resultado = ejecutar("--correo", CORREO, input=f"{CONTRASENA}\n{CONTRASENA}\n")

    assert resultado.exit_code == 0, resultado.output
    assert verificar_password(_admin(sesion).password_hash, CONTRASENA)
    _sin_credenciales_en_salida(resultado, CONTRASENA)


# --- Fallos sin crear ninguna cuenta ----------------------------------------


def test_falla_si_ya_existe_un_admin_activo(sesion, crear_cuenta, ejecutar):
    crear_cuenta("admin", correo="existente@example.com")

    resultado = ejecutar("--correo", CORREO, env={"ADMIN_CONTRASENA": CONTRASENA})

    assert resultado.exit_code != 0
    assert "Ya existe un administrador activo" in resultado.output
    assert _contar(sesion) == 1
    assert _admin(sesion) is None


@pytest.mark.parametrize("contrasena", ["corta", "1234567"])
def test_falla_con_contrasena_de_menos_de_8_caracteres(sesion, ejecutar, contrasena):
    resultado = ejecutar("--correo", CORREO, env={"ADMIN_CONTRASENA": contrasena})

    assert resultado.exit_code != 0
    assert "al menos 8 caracteres" in resultado.output
    assert _contar(sesion) == 0
    _sin_credenciales_en_salida(resultado, contrasena)


def test_contrasena_de_8_caracteres_sin_reglas_de_composicion(sesion, ejecutar):
    resultado = ejecutar("--correo", CORREO, env={"ADMIN_CONTRASENA": "abcdefgh"})

    assert resultado.exit_code == 0, resultado.output
    assert _contar(sesion) == 1


@pytest.mark.parametrize("correo", ["sin-arroba", "a@b", "con espacio@example.com"])
def test_falla_con_correo_de_formato_invalido(sesion, ejecutar, correo):
    resultado = ejecutar("--correo", correo, env={"ADMIN_CONTRASENA": CONTRASENA})

    assert resultado.exit_code != 0
    assert "formato válido" in resultado.output
    assert _contar(sesion) == 0


def test_falla_con_correo_duplicado(sesion, crear_cuenta, ejecutar):
    crear_cuenta("solicitante", correo=CORREO)

    resultado = ejecutar("--correo", CORREO.upper(), env={"ADMIN_CONTRASENA": CONTRASENA})

    assert resultado.exit_code != 0
    assert "ya está registrado" in resultado.output
    assert _contar(sesion) == 1
    assert _admin(sesion).rol.nombre == "solicitante"


def test_falla_sin_correo(sesion, ejecutar):
    resultado = ejecutar(env={"ADMIN_CONTRASENA": CONTRASENA})

    assert resultado.exit_code != 0
    assert "--correo" in resultado.output and "ADMIN_CORREO" in resultado.output
    assert _contar(sesion) == 0


def test_falla_sin_contrasena_ni_terminal(sesion, ejecutar, monkeypatch):
    monkeypatch.setattr(commands, "_hay_terminal", lambda: False)

    resultado = ejecutar("--correo", CORREO)

    assert resultado.exit_code != 0
    assert "ADMIN_CONTRASENA" in resultado.output
    assert _contar(sesion) == 0


def test_falla_si_la_confirmacion_no_coincide(sesion, ejecutar, monkeypatch):
    monkeypatch.setattr(commands, "_hay_terminal", lambda: True)

    resultado = ejecutar("--correo", CORREO, input=f"{CONTRASENA}\notra-contrasena\n")

    assert resultado.exit_code != 0
    assert _contar(sesion) == 0
    _sin_credenciales_en_salida(resultado, CONTRASENA, "otra-contrasena")


def test_no_existe_opcion_de_contrasena(sesion, ejecutar):
    resultado = ejecutar("--correo", CORREO, "--contrasena", CONTRASENA)

    assert resultado.exit_code != 0
    assert _contar(sesion) == 0


def test_el_comando_esta_registrado(app):
    assert "create-admin" in app.cli.commands
