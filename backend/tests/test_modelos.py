"""Pruebas de los metadatos de los modelos (tarea 2.1)."""

from sqlalchemy import DateTime, UniqueConstraint

from backend.app.extensions import Base
from backend.app.models import Rol, Usuario


def _columnas_unicas(tabla):
    return {
        tuple(columna.name for columna in restriccion.columns)
        for restriccion in tabla.constraints
        if isinstance(restriccion, UniqueConstraint)
    }


def test_los_metadatos_declaran_las_tablas_roles_y_usuarios():
    assert {"roles", "usuarios"} <= set(Base.metadata.tables)
    assert Rol.__table__.name == "roles"
    assert Usuario.__table__.name == "usuarios"


def test_usuarios_declara_la_clave_foranea_a_roles():
    claves = list(Usuario.__table__.c.rol_id.foreign_keys)
    assert len(claves) == 1
    assert claves[0].target_fullname == "roles.id"


def test_cada_usuario_tiene_un_unico_rol_obligatorio():
    assert Usuario.__table__.c.rol_id.nullable is False
    assert Usuario.rol.property.uselist is False


def test_el_nombre_del_rol_y_el_correo_son_unicos():
    assert ("nombre",) in _columnas_unicas(Rol.__table__)
    assert ("correo",) in _columnas_unicas(Usuario.__table__)


def test_usuarios_declara_el_estado_activo_y_marcas_de_tiempo_en_utc():
    tabla = Usuario.__table__
    assert tabla.c.activo.nullable is False
    for nombre in ("creado_en", "actualizado_en"):
        tipo = tabla.c[nombre].type
        assert isinstance(tipo, DateTime)
        assert tipo.timezone is True
