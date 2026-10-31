"""Pruebas del repositorio de espacios contra reservas_test (tarea 1.2)."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from backend.app.espacios import repositories
from backend.app.models import Espacio


def test_un_espacio_se_persiste_y_se_recupera(sesion):
    antes = datetime.now(timezone.utc)
    creado = repositories.crear_espacio("Laboratorio de Física", "laboratorio", 30)
    sesion.commit()
    espacio_id = creado.id
    sesion.expunge_all()

    espacio = repositories.obtener_espacio_por_id(espacio_id)

    assert espacio is not None
    assert espacio.nombre == "Laboratorio de Física"
    assert espacio.tipo == "laboratorio"
    assert espacio.capacidad == 30
    assert espacio.estado == "activo"
    for marca in (espacio.creado_en, espacio.actualizado_en):
        assert marca.tzinfo is not None
        assert antes <= marca <= antes + timedelta(minutes=1)


def test_obtener_un_identificador_inexistente_devuelve_none(sesion):
    assert repositories.obtener_espacio_por_id(999) is None


def test_el_nombre_se_guarda_sin_espacios_exteriores(sesion):
    creado = repositories.crear_espacio("  Auditorio Central  ", "auditorio", 200)
    sesion.commit()
    espacio_id = creado.id
    sesion.expunge_all()

    guardado = sesion.execute(select(Espacio.nombre).where(Espacio.id == espacio_id)).scalar_one()
    assert guardado == "Auditorio Central"

    repositories.actualizar_espacio(
        repositories.obtener_espacio_por_id(espacio_id), nombre="  Auditorio Norte "
    )
    sesion.commit()
    sesion.expunge_all()
    guardado = sesion.execute(select(Espacio.nombre).where(Espacio.id == espacio_id)).scalar_one()
    assert guardado == "Auditorio Norte"


def test_el_listado_incluye_los_espacios_inactivos(sesion):
    activo = repositories.crear_espacio("Sala 1", "sala_de_computo", 25)
    inactivo = repositories.crear_espacio("Sala 2", "sala_de_computo", 20)
    repositories.cambiar_estado(inactivo, "inactivo")
    sesion.commit()
    ids = (activo.id, inactivo.id)
    sesion.expunge_all()

    espacios = repositories.listar_espacios()

    assert [(e.id, e.estado) for e in espacios] == [
        (ids[0], "activo"),
        (ids[1], "inactivo"),
    ]


def test_el_listado_vacio_devuelve_una_lista_vacia(sesion):
    assert repositories.listar_espacios() == []


def test_la_actualizacion_cambia_solo_los_campos_indicados_y_conserva_el_estado(sesion):
    espacio = repositories.crear_espacio("Lab A", "laboratorio", 30)
    repositories.cambiar_estado(espacio, "inactivo")
    sesion.commit()
    espacio_id = espacio.id
    sesion.expunge_all()

    repositories.actualizar_espacio(repositories.obtener_espacio_por_id(espacio_id), capacidad=40)
    sesion.commit()
    sesion.expunge_all()

    espacio = repositories.obtener_espacio_por_id(espacio_id)
    assert (espacio.nombre, espacio.tipo, espacio.capacidad, espacio.estado) == (
        "Lab A", "laboratorio", 40, "inactivo",
    )

    repositories.actualizar_espacio(espacio, nombre="Lab B", tipo="auditorio", capacidad=50)
    sesion.commit()
    sesion.expunge_all()

    espacio = repositories.obtener_espacio_por_id(espacio_id)
    assert (espacio.nombre, espacio.tipo, espacio.capacidad, espacio.estado) == (
        "Lab B", "auditorio", 50, "inactivo",
    )


def test_los_cambios_de_estado_alternan_entre_activo_e_inactivo(sesion):
    espacio = repositories.crear_espacio("Lab C", "laboratorio", 15)
    sesion.commit()
    espacio_id = espacio.id

    for estado in ("inactivo", "activo", "inactivo"):
        repositories.cambiar_estado(repositories.obtener_espacio_por_id(espacio_id), estado)
        sesion.commit()
        sesion.expunge_all()
        espacio = repositories.obtener_espacio_por_id(espacio_id)
        assert espacio.estado == estado
        assert (espacio.nombre, espacio.tipo, espacio.capacidad) == ("Lab C", "laboratorio", 15)


@pytest.mark.parametrize(
    "segundo_nombre",
    ["LABORATORIO de química", "  Laboratorio de Química  ", " laboratorio DE QUÍMICA"],
)
def test_dos_altas_con_nombres_equivalentes_violan_el_indice_unico(sesion, segundo_nombre):
    repositories.crear_espacio("Laboratorio de Química", "laboratorio", 30)
    sesion.commit()

    with pytest.raises(IntegrityError) as error:
        repositories.crear_espacio(segundo_nombre, "laboratorio", 30)
        sesion.commit()

    assert "ux_espacios_nombre" in str(error.value.orig)


def test_la_base_rechaza_nombres_equivalentes_insertados_directamente(sesion):
    # Sin pasar por el repositorio (que normaliza): el índice sobre
    # lower(btrim(nombre)) rechaza el duplicado por sí mismo.
    sesion.add(Espacio(nombre="Sala Magna", tipo="auditorio", capacidad=100))
    sesion.commit()

    sesion.add(Espacio(nombre="  SALA MAGNA ", tipo="auditorio", capacidad=100))
    with pytest.raises(IntegrityError) as error:
        sesion.commit()

    assert "ux_espacios_nombre" in str(error.value.orig)


@pytest.mark.parametrize(
    "campos, restriccion",
    [
        ({"tipo": "aula", "capacidad": 10}, "ck_espacios_tipo"),
        ({"tipo": "laboratorio", "capacidad": 0}, "ck_espacios_capacidad"),
        ({"tipo": "laboratorio", "capacidad": -5}, "ck_espacios_capacidad"),
        ({"tipo": "laboratorio", "capacidad": 10, "estado": "borrado"}, "ck_espacios_estado"),
    ],
)
def test_la_base_rechaza_valores_fuera_de_los_check(sesion, campos, restriccion):
    sesion.add(Espacio(nombre="Espacio X", **campos))
    with pytest.raises(IntegrityError) as error:
        sesion.commit()

    assert restriccion in str(error.value.orig)
