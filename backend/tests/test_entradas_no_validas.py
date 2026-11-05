"""Entradas de la petición que no deben terminar en un error interno.

Requisito «Formato de las respuestas de error de la API» de la spec `auth`: unos datos
que no cumplen el formato esperado responden 400 `datos_invalidos` y un recurso
inexistente responde 404, sin llegar a `error_interno`. Cubre los textos que PostgreSQL
no puede almacenar en las cuentas, los identificadores de ruta fuera del rango de la
columna, los cuerpos JSON con anidamiento extremo, los nombres de espacio que el índice
único no admite y las fechas que no se podrían leer en otra zona de la sesión.
"""

import random
from datetime import datetime, timezone

import pytest
from sqlalchemy import event, select, text

from backend.app.auth.errors import DatosInvalidos
from backend.app.extensions import db
from backend.app.models import Espacio, Reserva, Usuario
from backend.app.reservas.services import convertir_fecha

CONTRASENA = "contrasena-valida"

NUL_Y_SUSTITUTOS_EN_NOMBRE = {
    "nul": "Ana\x00Pérez",
    "solo_nul": "\x00",
    "sustituto_alto": "Ana\ud800Pérez",
    "sustituto_bajo": "\udc00",
}
NUL_Y_SUSTITUTOS_EN_CORREO = {
    "nul_en_la_parte_local": "ana\x00@example.com",
    "nul_en_el_dominio": "ana@exam\x00ple.com",
    "sustituto_alto_en_la_parte_local": "ana\ud800@example.com",
    "sustituto_bajo_en_el_dominio": "ana@exam\udc00ple.com",
}
# 254 caracteres que, al pasar a minúsculas, ocupan más que la columna `correo`.
CORREO_QUE_CRECE_EN_MINUSCULAS = "i@" + "İ" * 249 + ".co"
# Texto poco comprimible: supera el tamaño máximo de una entrada del índice único.
NOMBRE_QUE_NO_CABE_EN_EL_INDICE = "".join(
    chr(c) for c in random.Random(7).choices(range(0x4E00, 0xA000), k=40_000)
)

IDS_FUERA_DE_RANGO = ["2147483648", "9223372036854775808", "9" * 30]
JSON_CON_ANIDAMIENTO_EXTREMO = {"arreglos": b"[" * 200_000, "objetos": b'{"a":' * 200_000}


def _parametrizar(casos):
    return pytest.mark.parametrize("valor", list(casos.values()), ids=list(casos))


@pytest.fixture
def admin(crear_cuenta):
    return crear_cuenta("admin", correo="admin@example.com")


@pytest.fixture
def otra_cuenta(crear_cuenta):
    return crear_cuenta(
        "solicitante", correo="otra@example.com", nombre="Otra", contrasena=CONTRASENA
    )


@pytest.fixture
def parametros_sql(sesion):
    """Parámetros de todas las sentencias enviadas a la base durante la prueba."""
    enviados = []

    def _registrar(_conn, _cursor, _sentencia, parametros, _contexto, _varios):
        enviados.append(parametros)

    event.listen(db.engine, "before_cursor_execute", _registrar)
    yield enviados
    event.remove(db.engine, "before_cursor_execute", _registrar)


def _error(respuesta, http, codigo):
    assert respuesta.status_code == http
    assert respuesta.get_json()["error"]["codigo"] == codigo


def _alta_usuario(client, cabeceras, **campos):
    return client.post(
        "/api/usuarios",
        headers=cabeceras,
        json={
            "nombre": "Ana",
            "correo": "ana@example.com",
            "contrasena": CONTRASENA,
            "rol": "solicitante",
            **campos,
        },
    )


def _datos_de_cuenta(sesion, usuario_id):
    sesion.rollback()
    cuenta = sesion.get(Usuario, usuario_id)
    sesion.refresh(cuenta)
    return cuenta.nombre, cuenta.correo, cuenta.password_hash


def _cuentas(sesion):
    sesion.rollback()
    return sesion.execute(select(Usuario.correo).order_by(Usuario.id)).scalars().all()


# --- Cuentas: nombre y correo -----------------------------------------------


@_parametrizar(NUL_Y_SUSTITUTOS_EN_NOMBRE)
def test_alta_con_nombre_no_almacenable(client, sesion, cabecera, admin, parametros_sql, valor):
    _error(_alta_usuario(client, cabecera(admin), nombre=valor), 400, "datos_invalidos")
    assert _cuentas(sesion) == ["admin@example.com"]
    assert not any(valor in str(p) for p in parametros_sql)


@_parametrizar(NUL_Y_SUSTITUTOS_EN_CORREO)
def test_alta_con_correo_no_almacenable(client, sesion, cabecera, admin, parametros_sql, valor):
    _error(_alta_usuario(client, cabecera(admin), correo=valor), 400, "datos_invalidos")
    assert _cuentas(sesion) == ["admin@example.com"]
    assert not any(valor in str(p) for p in parametros_sql)


@_parametrizar(NUL_Y_SUSTITUTOS_EN_NOMBRE)
def test_edicion_con_nombre_no_almacenable(client, sesion, cabecera, admin, otra_cuenta,
                                           parametros_sql, valor):
    antes = _datos_de_cuenta(sesion, otra_cuenta)
    respuesta = client.patch(f"/api/usuarios/{otra_cuenta}", headers=cabecera(admin),
                             json={"nombre": valor})
    _error(respuesta, 400, "datos_invalidos")
    assert _datos_de_cuenta(sesion, otra_cuenta) == antes
    assert not any(valor in str(p) for p in parametros_sql)


@_parametrizar(NUL_Y_SUSTITUTOS_EN_CORREO)
def test_edicion_con_correo_no_almacenable(client, sesion, cabecera, admin, otra_cuenta,
                                           parametros_sql, valor):
    antes = _datos_de_cuenta(sesion, otra_cuenta)
    respuesta = client.patch(f"/api/usuarios/{otra_cuenta}", headers=cabecera(admin),
                             json={"correo": valor})
    _error(respuesta, 400, "datos_invalidos")
    assert _datos_de_cuenta(sesion, otra_cuenta) == antes
    assert not any(valor in str(p) for p in parametros_sql)


def test_alta_con_correo_que_excede_la_columna_al_pasar_a_minusculas(client, sesion, cabecera,
                                                                     admin):
    assert len(CORREO_QUE_CRECE_EN_MINUSCULAS) == 254
    respuesta = _alta_usuario(client, cabecera(admin), correo=CORREO_QUE_CRECE_EN_MINUSCULAS)
    _error(respuesta, 400, "datos_invalidos")
    assert _cuentas(sesion) == ["admin@example.com"]


def test_edicion_con_correo_que_excede_la_columna_al_pasar_a_minusculas(client, sesion, cabecera,
                                                                        admin, otra_cuenta):
    antes = _datos_de_cuenta(sesion, otra_cuenta)
    respuesta = client.patch(f"/api/usuarios/{otra_cuenta}", headers=cabecera(admin),
                             json={"correo": CORREO_QUE_CRECE_EN_MINUSCULAS})
    _error(respuesta, 400, "datos_invalidos")
    assert _datos_de_cuenta(sesion, otra_cuenta) == antes


# --- Cuentas: contraseña ----------------------------------------------------


@pytest.mark.parametrize(
    "contrasena",
    ["contrasena\ud800-larga", "\udc00" * 8, "a\ud800"],
    ids=["sustituto_alto", "solo_sustitutos", "sustituto_en_una_contrasena_corta"],
)
def test_alta_con_contrasena_con_sustitutos(client, sesion, cabecera, admin, contrasena):
    _error(_alta_usuario(client, cabecera(admin), contrasena=contrasena), 400, "datos_invalidos")
    assert _cuentas(sesion) == ["admin@example.com"]


@pytest.mark.parametrize(
    "contrasena",
    ["contrasena\ud800-larga", "\udc00" * 8, "a\ud800"],
    ids=["sustituto_alto", "solo_sustitutos", "sustituto_en_una_contrasena_corta"],
)
def test_restablecimiento_con_contrasena_con_sustitutos(client, sesion, cabecera, admin,
                                                        otra_cuenta, contrasena):
    antes = _datos_de_cuenta(sesion, otra_cuenta)
    respuesta = client.post(f"/api/usuarios/{otra_cuenta}/password", headers=cabecera(admin),
                            json={"contrasena": contrasena})
    _error(respuesta, 400, "datos_invalidos")
    assert _datos_de_cuenta(sesion, otra_cuenta) == antes


def test_una_contrasena_con_nul_se_hashea_como_cualquier_otra(client, sesion, cabecera, admin):
    """La contraseña no llega a la base: solo se guarda su hash."""
    contrasena = "contrasena\x00larga"
    assert _alta_usuario(client, cabecera(admin), contrasena=contrasena).status_code == 201

    credenciales = {"correo": "ana@example.com", "contrasena": contrasena}
    assert client.post("/api/auth/login", json=credenciales).status_code == 200


# --- Identificadores en la ruta ---------------------------------------------


@pytest.mark.parametrize("identificador", IDS_FUERA_DE_RANGO, ids=["int4", "int8", "30_digitos"])
@pytest.mark.parametrize(
    "metodo,plantilla,cuerpo",
    [
        ("GET", "/api/usuarios/{}", None),
        ("PATCH", "/api/usuarios/{}", {"nombre": "Otro"}),
        ("POST", "/api/usuarios/{}/password", {"contrasena": CONTRASENA}),
        ("POST", "/api/usuarios/{}/desactivar", None),
        ("POST", "/api/usuarios/{}/activar", None),
    ],
    ids=["detalle", "edicion", "contrasena", "desactivar", "activar"],
)
def test_usuario_con_identificador_fuera_de_rango(client, cabecera, admin, metodo, plantilla,
                                                  cuerpo, identificador):
    respuesta = client.open(plantilla.format(identificador), method=metodo,
                            headers=cabecera(admin), json=cuerpo)
    _error(respuesta, 404, "usuario_no_encontrado")


@pytest.mark.parametrize("identificador", IDS_FUERA_DE_RANGO, ids=["int4", "int8", "30_digitos"])
@pytest.mark.parametrize(
    "metodo,plantilla,cuerpo",
    [
        ("GET", "/api/espacios/{}", None),
        ("PATCH", "/api/espacios/{}", {"capacidad": 5}),
        ("POST", "/api/espacios/{}/desactivar", None),
        ("POST", "/api/espacios/{}/activar", None),
    ],
    ids=["detalle", "edicion", "desactivar", "activar"],
)
def test_espacio_con_identificador_fuera_de_rango(client, cabecera, admin, metodo, plantilla,
                                                  cuerpo, identificador):
    respuesta = client.open(plantilla.format(identificador), method=metodo,
                            headers=cabecera(admin), json=cuerpo)
    _error(respuesta, 404, "espacio_no_encontrado")


def test_el_ultimo_identificador_del_rango_se_consulta_en_la_base(client, cabecera, admin):
    autorizado = cabecera(admin)
    _error(client.get("/api/usuarios/2147483647", headers=autorizado), 404,
           "usuario_no_encontrado")
    _error(client.get("/api/espacios/2147483647", headers=autorizado), 404,
           "espacio_no_encontrado")


@pytest.mark.parametrize(
    "identificador",
    ["abc", "1.5", "-1", "%00", "1%00", "%FF", "9" * 5000],
    ids=["letras", "decimal", "negativo", "nul", "digito_y_nul", "byte_invalido", "5000_digitos"],
)
@pytest.mark.parametrize(
    "plantilla", ["/api/usuarios/{}", "/api/espacios/{}", "/api/reservas/{}"],
    ids=["usuarios", "espacios", "reservas"],
)
def test_identificador_no_numerico_es_una_ruta_inexistente(client, cabecera, admin, plantilla,
                                                           identificador):
    respuesta = client.get(plantilla.format(identificador), headers=cabecera(admin))
    _error(respuesta, 404, "ruta_no_encontrada")


# --- Cuerpos JSON -----------------------------------------------------------


@pytest.mark.parametrize(
    "cuerpo", list(JSON_CON_ANIDAMIENTO_EXTREMO.values()), ids=list(JSON_CON_ANIDAMIENTO_EXTREMO)
)
@pytest.mark.parametrize(
    "metodo,plantilla",
    [
        ("POST", "/api/auth/login"),
        ("POST", "/api/usuarios"),
        ("PATCH", "/api/usuarios/{cuenta}"),
        ("POST", "/api/usuarios/{cuenta}/password"),
        ("POST", "/api/espacios"),
        ("PATCH", "/api/espacios/{espacio}"),
        ("POST", "/api/reservas"),
        ("POST", "/api/reservas/{reserva}/rechazar"),
    ],
    ids=["login", "alta_usuario", "edicion_usuario", "contrasena", "alta_espacio",
         "edicion_espacio", "alta_reserva", "rechazo"],
)
def test_json_con_anidamiento_extremo(client, cabecera, admin, otra_cuenta, nuevo_espacio,
                                      sembrar_reserva, metodo, plantilla, cuerpo):
    espacio = nuevo_espacio()
    reserva = sembrar_reserva(espacio, otra_cuenta, datetime(2040, 1, 1, tzinfo=timezone.utc),
                              datetime(2040, 1, 2, tzinfo=timezone.utc), "pendiente")
    ruta = plantilla.format(cuenta=otra_cuenta, espacio=espacio, reserva=reserva)
    respuesta = client.open(ruta, method=metodo, headers=cabecera(admin), data=cuerpo,
                            content_type="application/json")
    _error(respuesta, 400, "datos_invalidos")


# --- Nombre de espacio demasiado grande para el índice único ------------------


def test_alta_de_espacio_con_nombre_que_no_cabe_en_el_indice(client, sesion, cabecera, admin):
    respuesta = client.post("/api/espacios", headers=cabecera(admin), json={
        "nombre": NOMBRE_QUE_NO_CABE_EN_EL_INDICE, "tipo": "laboratorio", "capacidad": 5,
    })
    _error(respuesta, 400, "datos_invalidos")
    sesion.rollback()
    assert sesion.execute(select(Espacio.id)).scalars().all() == []


def test_edicion_de_espacio_con_nombre_que_no_cabe_en_el_indice(client, sesion, cabecera, admin,
                                                                nuevo_espacio):
    espacio = nuevo_espacio("Laboratorio 1")
    respuesta = client.patch(f"/api/espacios/{espacio}", headers=cabecera(admin),
                             json={"nombre": NOMBRE_QUE_NO_CABE_EN_EL_INDICE})
    _error(respuesta, 400, "datos_invalidos")
    sesion.rollback()
    assert sesion.execute(select(Espacio.nombre)).scalars().all() == ["Laboratorio 1"]


def test_un_nombre_largo_que_cabe_en_el_indice_se_acepta(client, cabecera, admin):
    respuesta = client.post("/api/espacios", headers=cabecera(admin), json={
        "nombre": "L" * 5000, "tipo": "laboratorio", "capacidad": 5,
    })
    assert respuesta.status_code == 201


# --- Fechas que no se podrían leer en otra zona de la sesión ------------------


@pytest.mark.parametrize(
    "inicio,fin",
    [("9999-12-30T20:00:01Z", "9999-12-31T00:00:01Z"),
     ("9999-12-31T20:00:00Z", "9999-12-31T23:59:59Z"),
     ("9999-12-31T20:00:00Z", "9999-12-31T22:00:00-01:00")],
    ids=["un_segundo_despues_del_limite", "ultimo_segundo", "desfase_negativo"],
)
def test_solicitud_que_termina_despues_de_la_ultima_fecha_admitida(client, sesion, cabecera,
                                                                   otra_cuenta, nuevo_espacio,
                                                                   inicio, fin):
    respuesta = client.post("/api/reservas", headers=cabecera(otra_cuenta), json={
        "espacio_id": nuevo_espacio(), "inicio": inicio, "fin": fin,
    })
    _error(respuesta, 400, "datos_invalidos")
    sesion.rollback()
    assert sesion.execute(select(Reserva.id)).scalars().all() == []


def test_la_ultima_fecha_admitida_se_lee_en_la_zona_con_mayor_desfase(client, sesion, cabecera,
                                                                      otra_cuenta, admin,
                                                                      nuevo_espacio):
    def _zona_de_kiritimati(conexion_dbapi, _registro):
        cursor = conexion_dbapi.cursor()
        cursor.execute("SET TIME ZONE 'Pacific/Kiritimati'")
        cursor.close()
        conexion_dbapi.commit()

    espacio = nuevo_espacio()
    solicitante, aprobador = cabecera(otra_cuenta), cabecera(admin)
    sesion.close()
    event.listen(db.engine, "connect", _zona_de_kiritimati)
    db.engine.dispose()
    assert sesion.execute(text("SHOW TIME ZONE")).scalar_one() == "Pacific/Kiritimati"
    sesion.close()

    inicio, fin = "9999-12-30T20:00:00Z", "9999-12-31T00:00:00Z"
    creada = client.post("/api/reservas", headers=solicitante,
                         json={"espacio_id": espacio, "inicio": inicio, "fin": fin})
    assert creada.status_code == 201
    reserva = creada.get_json()["id"]

    assert client.post(f"/api/reservas/{reserva}/aprobar", headers=aprobador).status_code == 200
    detalle = client.get(f"/api/reservas/{reserva}", headers=solicitante)
    assert (detalle.get_json()["inicio"], detalle.get_json()["fin"]) == (inicio, fin)
    assert client.get("/api/reservas", headers=aprobador).status_code == 200
    disponibilidad = client.get(f"/api/espacios/{espacio}/disponibilidad",
                                headers=aprobador, query_string={"inicio": inicio, "fin": fin})
    assert disponibilidad.get_json() == [{"inicio": inicio, "fin": fin}]


# --- Fechas con caracteres de control o no ASCII ------------------------------

# `datetime.fromisoformat` acepta varias de estas cadenas: un NUL antes del desfase y
# cualquier carácter como separador entre la fecha y la hora.
FECHAS_CON_CARACTERES_NO_ADMITIDOS = {
    "nul_antes_del_desfase": "2030-01-01T00:00:00\x00+00:00",
    "nul_antes_de_la_z": "2030-01-01T00:00:00\x00Z",
    "nul_al_final": "2030-01-01T00:00:00+00:00\x00",
    "nul_como_separador": "2030-01-01\x0000:00:00+00:00",
    "tabulador_como_separador": "2030-01-01\t00:00:00+00:00",
    "salto_de_linea_al_final": "2030-01-01T00:00:00+00:00\n",
    "control_c0": "2030-01-01\x1f00:00:00+00:00",
    "supr": "2030-01-01\x7f00:00:00+00:00",
    "control_c1": "2030-01-01\x8500:00:00+00:00",
    "espacio_duro_como_separador": "2030-01-01 00:00:00+00:00",
    "letra_no_ascii_como_separador": "2030-01-01ñ00:00:00+00:00",
    "digitos_no_ascii": "٢٠٣٠-01-01T00:00:00+00:00",
    "signo_no_ascii": "2030-01-01T00:00:00＋00:00",
}
FECHAS_VALIDAS = {
    "2030-01-01T10:00:00Z": datetime(2030, 1, 1, 10, tzinfo=timezone.utc),
    "2030-01-01T10:00:00+00:00": datetime(2030, 1, 1, 10, tzinfo=timezone.utc),
    "2030-01-01T10:00:00+05:30": datetime(2030, 1, 1, 4, 30, tzinfo=timezone.utc),
    "2030-01-01T10:00:00-05:00": datetime(2030, 1, 1, 15, tzinfo=timezone.utc),
    "2030-01-01T10:00:00.250Z": datetime(2030, 1, 1, 10, 0, 0, 250000, tzinfo=timezone.utc),
    "2030-01-01T10:00:00.123456+05:30": datetime(2030, 1, 1, 4, 30, 0, 123456,
                                                 tzinfo=timezone.utc),
    "2030-01-01 10:00:00+00:00": datetime(2030, 1, 1, 10, tzinfo=timezone.utc),
}
ANTES = "2029-12-31T00:00:00Z"
DESPUES = "2030-01-02T00:00:00Z"


def _fecha_no_admitida(casos=FECHAS_CON_CARACTERES_NO_ADMITIDOS):
    return pytest.mark.parametrize("fecha", list(casos.values()), ids=list(casos))


def _rango_con(campo, fecha, nombres):
    """Rango válido salvo por `fecha`, en el extremo indicado (`inicio` o `fin`)."""
    primero, segundo = nombres
    return {primero: ANTES, segundo: DESPUES, (primero if campo == "inicio" else segundo): fecha}


@_fecha_no_admitida()
def test_convertir_fecha_rechaza_caracteres_de_control_o_no_ascii(fecha):
    with pytest.raises(DatosInvalidos):
        convertir_fecha(fecha)


@pytest.mark.parametrize("fecha,esperada", list(FECHAS_VALIDAS.items()), ids=list(FECHAS_VALIDAS))
def test_convertir_fecha_conserva_los_formatos_validos(fecha, esperada):
    assert convertir_fecha(fecha) == esperada


@_fecha_no_admitida()
@pytest.mark.parametrize("campo", ["inicio", "fin"])
def test_creacion_con_fecha_con_caracteres_no_admitidos(client, sesion, cabecera, otra_cuenta,
                                                        nuevo_espacio, campo, fecha):
    respuesta = client.post("/api/reservas", headers=cabecera(otra_cuenta), json={
        "espacio_id": nuevo_espacio(), **_rango_con(campo, fecha, ("inicio", "fin")),
    })
    _error(respuesta, 400, "datos_invalidos")
    sesion.rollback()
    assert sesion.execute(select(Reserva.id)).scalars().all() == []


@_fecha_no_admitida()
@pytest.mark.parametrize("campo", ["inicio", "fin"])
def test_disponibilidad_con_fecha_con_caracteres_no_admitidos(client, cabecera, otra_cuenta,
                                                              nuevo_espacio, campo, fecha):
    respuesta = client.get(f"/api/espacios/{nuevo_espacio()}/disponibilidad",
                           headers=cabecera(otra_cuenta),
                           query_string=_rango_con(campo, fecha, ("inicio", "fin")))
    _error(respuesta, 400, "datos_invalidos")


@_fecha_no_admitida()
@pytest.mark.parametrize("campo", ["inicio", "fin"], ids=["desde", "hasta"])
def test_historial_con_fecha_con_caracteres_no_admitidos(client, cabecera, otra_cuenta, campo,
                                                         fecha):
    respuesta = client.get("/api/historial", headers=cabecera(otra_cuenta),
                           query_string=_rango_con(campo, fecha, ("desde", "hasta")))
    _error(respuesta, 400, "datos_invalidos")


@pytest.mark.parametrize("fecha", ["2030-01-01T00:00:00\ud800+00:00", "\udc00"],
                         ids=["sustituto_alto", "sustituto_bajo"])
def test_creacion_con_fecha_con_sustitutos(client, cabecera, otra_cuenta, nuevo_espacio, fecha):
    respuesta = client.post("/api/reservas", headers=cabecera(otra_cuenta), json={
        "espacio_id": nuevo_espacio(), "inicio": fecha, "fin": DESPUES,
    })
    _error(respuesta, 400, "datos_invalidos")


@pytest.mark.parametrize("inicio,fin", [
    ("2030-01-01T10:00:00Z", "2030-01-01T11:00:00Z"),
    ("2030-01-01T10:00:00+05:30", "2030-01-01T11:00:00+05:30"),
    ("2030-01-01T10:00:00.250Z", "2030-01-01T10:00:00.750Z"),
], ids=["sufijo_z", "desfase", "fracciones"])
def test_los_formatos_validos_se_aceptan_en_los_tres_puntos(client, cabecera, otra_cuenta,
                                                            nuevo_espacio, inicio, fin):
    espacio, autorizado = nuevo_espacio(), cabecera(otra_cuenta)
    creada = client.post("/api/reservas", headers=autorizado,
                         json={"espacio_id": espacio, "inicio": inicio, "fin": fin})
    assert creada.status_code == 201
    assert client.get(f"/api/espacios/{espacio}/disponibilidad", headers=autorizado,
                      query_string={"inicio": inicio, "fin": fin}).status_code == 200
    assert client.get("/api/historial", headers=autorizado,
                      query_string={"desde": inicio, "hasta": fin}).status_code == 200
