"""Pruebas del almacenamiento seguro de contraseñas (tarea 2.3)."""

from backend.app.auth.services import generar_hash_password, verificar_password
from backend.app.usuarios import repositories

PASSWORD = "contrasena-de-prueba"


def _crear_cuenta(correo, password):
    rol = repositories.obtener_rol_por_nombre("solicitante")
    return repositories.crear_usuario("Usuario", correo, generar_hash_password(password), rol)


def test_el_valor_almacenado_difiere_de_la_contrasena_en_texto_plano(sesion):
    usuario = _crear_cuenta("uno@example.com", PASSWORD)
    sesion.commit()

    assert usuario.password_hash != PASSWORD
    assert PASSWORD not in usuario.password_hash


def test_la_verificacion_con_la_contrasena_correcta_resulta_exitosa(sesion):
    usuario = _crear_cuenta("uno@example.com", PASSWORD)
    sesion.commit()

    assert verificar_password(usuario.password_hash, PASSWORD) is True
    assert verificar_password(usuario.password_hash, "otra-contrasena") is False


def test_dos_cuentas_con_la_misma_contrasena_almacenan_valores_distintos(sesion):
    primera = _crear_cuenta("uno@example.com", PASSWORD)
    segunda = _crear_cuenta("dos@example.com", PASSWORD)
    sesion.commit()

    assert primera.password_hash != segunda.password_hash
    assert verificar_password(primera.password_hash, PASSWORD)
    assert verificar_password(segunda.password_hash, PASSWORD)
