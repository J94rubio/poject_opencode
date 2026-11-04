"""API del historial (tareas 5.2 y 5.3 de `cancelacion-historial`).

Requisitos «Consulta del historial según el rol», «Filtros del historial» e
«Inmutabilidad del historial» de la spec `historial`. Las entradas se siembran con
el repositorio y fechas fijas, sin depender de la fecha real.
"""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from backend.app.auth import errors
from backend.app.historial.repositories import registrar
from backend.app.models import EntradaHistorial
from backend.app.reservas import repositories as repositorio_reservas
from backend.app.usuarios import repositories as repositorio_usuarios

BASE = datetime(2030, 3, 1, 12, tzinfo=timezone.utc)
CAMPOS = {"id", "reserva_id", "espacio_id", "estado_anterior", "estado_nuevo", "actor_id",
          "fecha_utc"}


def _dia(numero):
    return BASE + timedelta(days=numero)


def _z(numero):
    return _dia(numero).isoformat().replace("+00:00", "Z")


@pytest.fixture
def mundo(sesion, crear_cuenta, nuevo_espacio):
    """Mismas entradas que en `test_repositorio_historial.py`:

    A (Sara, espacio 1): día 0 creación, día 2 aprobación.
    B (Sara, espacio 2): día 1 creación.
    C (Otro, espacio 1): día 3 creación, día 4 rechazo.
    """
    ids = {
        "sara": crear_cuenta("solicitante", correo="sara@example.com"),
        "otro": crear_cuenta("solicitante", correo="otro@example.com"),
        "sin_entradas": crear_cuenta("solicitante", correo="vacio@example.com"),
        "aprobador": crear_cuenta("aprobador"),
        "admin": crear_cuenta("admin"),
    }
    cuentas = {n: repositorio_usuarios.obtener_usuario_por_id(i) for n, i in ids.items()}
    espacios = {"uno": nuevo_espacio("Espacio uno"), "dos": nuevo_espacio("Espacio dos")}

    def _reserva(espacio, cuenta, desfase):
        inicio = _dia(100 + desfase)
        return repositorio_reservas.crear(espacios[espacio], ids[cuenta], inicio,
                                          inicio + timedelta(hours=1))

    a, b, c = _reserva("uno", "sara", 0), _reserva("dos", "sara", 1), _reserva("uno", "otro", 2)

    def _anotar(reserva, anterior, nuevo, actor, dia):
        return registrar(sesion, reserva, anterior, nuevo, cuentas[actor],
                         reloj=lambda: _dia(dia)).id

    entradas = {
        "a_creada": _anotar(a, None, "pendiente", "sara", 0),
        "b_creada": _anotar(b, None, "pendiente", "sara", 1),
        "a_aprobada": _anotar(a, "pendiente", "aprobada", "aprobador", 2),
        "c_creada": _anotar(c, None, "pendiente", "otro", 3),
        "c_rechazada": _anotar(c, "pendiente", "rechazada", "aprobador", 4),
    }
    sesion.commit()
    return {"ids": ids, "espacios": espacios, "entradas": entradas, "reservas": (a.id, b.id, c.id)}


def _consultar(client, cabecera, usuario_id, consulta=""):
    return client.get(f"/api/historial{consulta}", headers=cabecera(usuario_id))


def _ids_de(respuesta):
    assert respuesta.status_code == 200
    return [e["id"] for e in respuesta.get_json()]


def _esperadas(mundo, *nombres):
    return [mundo["entradas"][n] for n in nombres]


TODAS = ("a_creada", "b_creada", "a_aprobada", "c_creada", "c_rechazada")


# --- Consulta según el rol ---------------------------------------------------


def test_historial_de_un_solicitante(client, cabecera, mundo):
    respuesta = _consultar(client, cabecera, mundo["ids"]["sara"])
    assert _ids_de(respuesta) == _esperadas(mundo, "a_creada", "b_creada", "a_aprobada")
    assert mundo["ids"]["aprobador"] in {e["actor_id"] for e in respuesta.get_json()}


@pytest.mark.parametrize("rol", ["aprobador", "admin"])
def test_historial_de_un_aprobador_o_administrador(client, cabecera, mundo, rol):
    assert _ids_de(_consultar(client, cabecera, mundo["ids"][rol])) == _esperadas(mundo, *TODAS)


def test_contenido_de_cada_entrada(client, cabecera, mundo):
    entradas = _consultar(client, cabecera, mundo["ids"]["admin"]).get_json()

    assert isinstance(entradas, list)
    assert all(set(e) == CAMPOS for e in entradas)
    a, _, _ = mundo["reservas"]
    assert entradas[0] == {
        "id": mundo["entradas"]["a_creada"],
        "reserva_id": a,
        "espacio_id": mundo["espacios"]["uno"],
        "estado_anterior": None,
        "estado_nuevo": "pendiente",
        "actor_id": mundo["ids"]["sara"],
        "fecha_utc": "2030-03-01T12:00:00Z",
    }
    assert entradas[2]["estado_anterior"] == "pendiente"
    assert entradas[2]["estado_nuevo"] == "aprobada"
    assert entradas[2]["actor_id"] == mundo["ids"]["aprobador"]


def test_el_actor_se_expone_solo_por_identificador(client, cabecera, mundo):
    texto = _consultar(client, cabecera, mundo["ids"]["admin"]).get_data(as_text=True)
    assert "example.com" not in texto
    assert "Persona" not in texto


def test_orden_de_las_entradas(client, cabecera, mundo, sesion):
    """Se registran con fechas decrecientes y dos iguales: el orden es fecha y luego id."""
    a = repositorio_reservas.buscar_por_id(mundo["reservas"][0])
    sara = repositorio_usuarios.obtener_usuario_por_id(mundo["ids"]["sara"])
    ids = [
        registrar(sesion, a, "aprobada", "cancelada", sara, reloj=lambda: _dia(dia)).id
        for dia in (50, 40, 40)
    ]
    sesion.commit()

    consulta = f"?desde={_z(40)}&hasta={_z(51)}"
    assert _ids_de(_consultar(client, cabecera, mundo["ids"]["admin"], consulta)) == [
        ids[1], ids[2], ids[0]
    ]


def test_historial_vacio(client, cabecera, mundo):
    respuesta = _consultar(client, cabecera, mundo["ids"]["sin_entradas"])
    assert respuesta.status_code == 200
    assert respuesta.get_json() == []


def test_lista_vacia_con_filtros_que_no_coinciden(client, cabecera, mundo):
    respuesta = _consultar(client, cabecera, mundo["ids"]["admin"], "?estado=cancelada")
    assert respuesta.status_code == 200
    assert respuesta.get_json() == []


def test_consulta_sin_sesion(client, sesion):
    respuesta = client.get("/api/historial")
    assert respuesta.status_code == 401
    assert respuesta.get_json()["error"]["codigo"] == "token_ausente"


# --- Filtros -----------------------------------------------------------------


def test_filtro_por_espacio(client, cabecera, mundo):
    consulta = f"?espacio_id={mundo['espacios']['dos']}"
    assert _ids_de(_consultar(client, cabecera, mundo["ids"]["admin"], consulta)) == _esperadas(
        mundo, "b_creada")


def test_filtro_por_estado(client, cabecera, mundo):
    assert _ids_de(_consultar(client, cabecera, mundo["ids"]["admin"], "?estado=pendiente")) == (
        _esperadas(mundo, "a_creada", "b_creada", "c_creada"))


def test_filtro_por_rango_de_fechas(client, cabecera, mundo):
    consulta = f"?desde={_z(1)}&hasta={_z(3)}"
    assert _ids_de(_consultar(client, cabecera, mundo["ids"]["admin"], consulta)) == _esperadas(
        mundo, "b_creada", "a_aprobada")


def test_rango_con_desfase_codificado_en_la_url(client, cabecera, mundo):
    """El «+» del desfase viaja como %2B; 17:00+05:00 es 12:00 UTC del día 1."""
    consulta = "?desde=2030-03-02T17:00:00%2B05:00&hasta=2030-03-02T17:00:01%2B05:00"
    assert _ids_de(_consultar(client, cabecera, mundo["ids"]["admin"], consulta)) == _esperadas(
        mundo, "b_creada")


def test_rango_con_mas_sin_codificar_es_invalido(client, cabecera, mundo):
    consulta = "?desde=2030-03-02T17:00:00+05:00&hasta=2030-03-02T17:00:01+05:00"
    assert _consultar(client, cabecera, mundo["ids"]["admin"], consulta).status_code == 400


def test_filtros_combinados(client, cabecera, mundo):
    consulta = f"?espacio_id={mundo['espacios']['uno']}&estado=pendiente&desde={_z(0)}&hasta={_z(3)}"
    assert _ids_de(_consultar(client, cabecera, mundo["ids"]["admin"], consulta)) == _esperadas(
        mundo, "a_creada")


def test_filtros_y_visibilidad_del_solicitante(client, cabecera, mundo):
    consulta = f"?espacio_id={mundo['espacios']['uno']}"
    assert _ids_de(_consultar(client, cabecera, mundo["ids"]["sara"], consulta)) == _esperadas(
        mundo, "a_creada", "a_aprobada")
    assert _ids_de(_consultar(client, cabecera, mundo["ids"]["sara"], "?estado=rechazada")) == []


@pytest.mark.parametrize(
    "consulta",
    [
        "?estado=confirmada", "?estado=PENDIENTE", "?estado=",
        "?espacio_id=", "?espacio_id=abc", "?espacio_id=1.5", "?espacio_id=1_000",
        "?espacio_id=%2B1", "?espacio_id=%201", "?espacio_id=" + "9" * 5000,
        "?desde=", "?hasta=", "?desde=&hasta=",
        "?desde=2030-03-01T00:00:00Z", "?hasta=2030-03-01T00:00:00Z",
        "?desde=2030-03-01T00:00:00&hasta=2030-03-02T00:00:00Z",
        "?desde=2030-03-01T00:00:00Z&hasta=2030-03-02T00:00:00",
        "?desde=ayer&hasta=hoy",
        "?desde=2030-03-02T00:00:00Z&hasta=2030-03-02T00:00:00Z",
        "?desde=2030-03-03T00:00:00Z&hasta=2030-03-02T00:00:00Z",
        "?desde=0001-01-01T00:00:00%2B14:00&hasta=2030-03-02T00:00:00Z",
        "?desde=2030-03-01T00:00:00Z&hasta=9999-12-31T23:59:59-14:00",
    ],
)
def test_filtros_invalidos(client, cabecera, mundo, consulta):
    respuesta = _consultar(client, cabecera, mundo["ids"]["admin"], consulta)
    assert respuesta.status_code == 400
    assert respuesta.get_json() == {
        "error": {"codigo": "datos_invalidos", "mensaje": errors.DatosInvalidos.mensaje}
    }


@pytest.mark.parametrize("rol", ["sara", "aprobador"])
@pytest.mark.parametrize("espacio", ["999999", "0", "-1", "2147483648"])
def test_espacio_inexistente(client, cabecera, mundo, rol, espacio):
    respuesta = _consultar(client, cabecera, mundo["ids"][rol], f"?espacio_id={espacio}")
    assert respuesta.status_code == 404
    assert respuesta.get_json()["error"]["codigo"] == "espacio_no_encontrado"


def test_un_filtro_invalido_se_detecta_antes_que_el_espacio_inexistente(client, cabecera, mundo):
    respuesta = _consultar(client, cabecera, mundo["ids"]["admin"],
                           "?espacio_id=999999&estado=confirmada")
    assert respuesta.status_code == 400


def test_filtro_por_espacio_inactivo_procede(client, cabecera, mundo, nuevo_espacio):
    espacio = nuevo_espacio("Inactivo", estado="inactivo")
    assert _consultar(client, cabecera, mundo["ids"]["admin"],
                      f"?espacio_id={espacio}").get_json() == []


def test_los_parametros_desconocidos_se_ignoran_como_en_disponibilidad(client, cabecera, mundo):
    espacio = mundo["espacios"]["uno"]
    disponibilidad = client.get(
        f"/api/espacios/{espacio}/disponibilidad"
        f"?inicio={_z(0)}&fin={_z(1)}&desconocido=1",
        headers=cabecera(mundo["ids"]["admin"]),
    )
    assert disponibilidad.status_code == 200

    historial = _consultar(client, cabecera, mundo["ids"]["admin"], "?desconocido=1&usuario_id=2")
    assert _ids_de(historial) == _esperadas(mundo, *TODAS)


def test_un_parametro_desconocido_no_amplia_la_visibilidad(client, cabecera, mundo):
    consulta = f"?solicitante_id={mundo['ids']['otro']}&actor_id={mundo['ids']['otro']}"
    assert _ids_de(_consultar(client, cabecera, mundo["ids"]["sara"], consulta)) == _esperadas(
        mundo, "a_creada", "b_creada", "a_aprobada")


# --- 5.3 Sin escritura por la API --------------------------------------------


def _num_entradas(sesion):
    sesion.rollback()
    return len(sesion.execute(select(EntradaHistorial)).scalars().all())


@pytest.mark.parametrize("metodo", ["POST", "PUT", "PATCH", "DELETE"])
@pytest.mark.parametrize("ruta", ["/api/historial"])
def test_escritura_por_la_api(client, cabecera, mundo, sesion, metodo, ruta):
    antes = _num_entradas(sesion)

    respuesta = client.open(ruta, method=metodo, headers=cabecera(mundo["ids"]["admin"]),
                            json={"estado_nuevo": "cancelada"})

    assert respuesta.status_code == 405
    assert respuesta.get_json()["error"]["codigo"] == "metodo_no_permitido"
    assert _num_entradas(sesion) == antes


@pytest.mark.parametrize("metodo", ["POST", "PUT", "PATCH", "DELETE"])
def test_escritura_por_la_api_sin_token_tambien_responde_405(client, sesion, metodo):
    respuesta = client.open("/api/historial", method=metodo)
    assert respuesta.status_code == 405
    assert respuesta.get_json()["error"]["codigo"] == "metodo_no_permitido"


def test_no_existen_rutas_del_historial_por_entrada(client, cabecera, mundo):
    entrada = mundo["entradas"]["a_creada"]
    respuesta = client.delete(f"/api/historial/{entrada}", headers=cabecera(mundo["ids"]["admin"]))
    assert respuesta.status_code == 404
    assert respuesta.get_json()["error"]["codigo"] == "ruta_no_encontrada"
