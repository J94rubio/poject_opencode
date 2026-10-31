"""Matriz de permisos por rol (design.md, D1 y D2; spec `auth`).

La matriz es un dato declarativo: cada rol declara solo los permisos que añade
sobre el rol del que hereda, y la jerarquía `admin` ⊇ `aprobador` ⊇
`solicitante` se resuelve a partir de la propia tabla. Un permiso nuevo se
añade en una sola fila y se propaga a los roles superiores por la herencia.
"""

# Rol del que hereda cada rol (None: base de la jerarquía).
HERENCIA = {
    "solicitante": None,
    "aprobador": "solicitante",
    "admin": "aprobador",
}

# Permisos que cada rol añade sobre los del rol del que hereda.
PERMISOS_PROPIOS = {
    "solicitante": frozenset({
        "espacios:ver",
        "reservas:crear",
        "reservas:ver_propias",
        "reservas:cancelar_propia",
        "historial:ver_propio",
    }),
    "aprobador": frozenset({
        "espacios:crear",
        "espacios:editar",
        "espacios:desactivar",
        "espacios:activar",
        "reservas:ver_todas",
        "aprobaciones:aprobar",
        "aprobaciones:rechazar",
        "historial:ver_todos",
    }),
    "admin": frozenset({
        "usuarios:ver",
        "usuarios:crear",
        "usuarios:editar",
        "usuarios:desactivar",
        "usuarios:activar",
        "usuarios:resetear_password",
        "roles:ver",
    }),
}

# Permisos que no se aplican a las solicitudes creadas por el propio usuario
# (D1 y D2). Su comportamiento se implementa en el change `aprobacion-reservas`.
EXCLUYEN_SOLICITUDES_PROPIAS = frozenset({
    "aprobaciones:aprobar",
    "aprobaciones:rechazar",
})


def _permisos_efectivos(rol):
    permisos = set()
    while rol is not None:
        permisos |= PERMISOS_PROPIOS[rol]
        rol = HERENCIA[rol]
    return frozenset(permisos)


# Permisos efectivos de cada rol, con la herencia ya resuelta.
PERMISOS_POR_ROL = {rol: _permisos_efectivos(rol) for rol in HERENCIA}

# Catálogo de todos los permisos declarados.
PERMISOS = frozenset().union(*PERMISOS_PROPIOS.values())


def tiene_permiso(rol, permiso):
    """Indica si el rol posee el permiso según la matriz."""
    return permiso in PERMISOS_POR_ROL.get(rol, frozenset())
