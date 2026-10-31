// Catálogo cerrado de tipos de espacio (spec `espacios`) y textos visibles de
// tipo y estado. La validación del tipo la hace el servidor
// (`tipo_espacio_invalido`); aquí solo se ofrecen las opciones del catálogo.

export const TIPOS_DE_ESPACIO = [
  { valor: 'laboratorio', texto: 'Laboratorio' },
  { valor: 'auditorio', texto: 'Auditorio' },
  { valor: 'sala_de_computo', texto: 'Sala de cómputo' },
]

export function textoDeTipo(tipo) {
  return TIPOS_DE_ESPACIO.find((t) => t.valor === tipo)?.texto ?? tipo
}

const TEXTO_DE_ESTADO = { activo: 'Activo', inactivo: 'Inactivo' }

export function textoDeEstado(estado) {
  return TEXTO_DE_ESTADO[estado] ?? estado
}
