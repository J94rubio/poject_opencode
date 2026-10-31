"""Pruebas del repositorio de usuarios contra reservas_test (sección 2)."""

from datetime import datetime, timedelta, timezone

from backend.app.usuarios import repositories


def test_un_usuario_se_persiste_y_se_recupera_con_su_rol(sesion):
    antes = datetime.now(timezone.utc)
    rol = repositories.obtener_rol_por_nombre("aprobador")
    creado = repositories.crear_usuario("Ana Pérez", "ana@example.com", "hash-de-prueba", rol)
    sesion.commit()
    usuario_id = creado.id
    sesion.expunge_all()

    usuario = repositories.obtener_usuario_por_id(usuario_id)

    assert usuario is not None
    assert usuario.nombre == "Ana Pérez"
    assert usuario.correo == "ana@example.com"
    assert usuario.rol.nombre == "aprobador"
    assert usuario.activo is True
    # TIMESTAMP WITH TIME ZONE: el instante guardado es el de la marca en UTC.
    for marca in (usuario.creado_en, usuario.actualizado_en):
        assert marca.tzinfo is not None
        assert antes <= marca <= antes + timedelta(minutes=1)
