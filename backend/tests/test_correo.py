"""Pruebas de la normalización y unicidad del correo (tareas 2.4 y 2.5)."""

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from backend.app.models import Usuario
from backend.app.usuarios import repositories


def test_el_correo_se_guarda_en_minusculas(sesion):
    rol = repositories.obtener_rol_por_nombre("solicitante")
    creado = repositories.crear_usuario("Ana", "Ana.Perez@Example.COM", "hash-de-prueba", rol)
    sesion.commit()
    usuario_id = creado.id
    sesion.expunge_all()

    guardado = sesion.execute(select(Usuario.correo).where(Usuario.id == usuario_id)).scalar_one()

    assert guardado == "ana.perez@example.com"


def test_la_base_rechaza_dos_cuentas_con_el_mismo_correo_en_distinto_caso(sesion):
    # Se inserta directamente con el ORM, sin pasar por el repositorio, para
    # comprobar que es el índice único sobre lower(correo) quien lo rechaza.
    rol = repositories.obtener_rol_por_nombre("solicitante")
    sesion.add(Usuario(nombre="Ana", correo="ana@example.com", password_hash="h", rol=rol))
    sesion.commit()

    sesion.add(Usuario(nombre="Ana", correo="ANA@Example.com", password_hash="h", rol=rol))
    with pytest.raises(IntegrityError) as error:
        sesion.commit()

    assert "uq_usuarios_correo_lower" in str(error.value.orig)
