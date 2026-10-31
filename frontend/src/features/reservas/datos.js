// Conversión de los campos de los formularios de reservas antes de enviarlos
// (spec interfaz-web, requisitos «Creación de solicitudes en la interfaz» y
// «Consulta de disponibilidad en la interfaz»; design.md de
// `reservas-disponibilidad`, «Almacenamiento de fechas»).
//
// No valida en el navegador: lo que no puede convertirse se envía tal como se
// escribió y el servidor decide (`datos_invalidos`). Un campo vacío se omite,
// de modo que el servidor lo trata como ausente.

// Valor de un campo `datetime-local` (hora local, sin zona) → ISO 8601 en UTC
// con zona horaria explícita (sufijo `Z`).
export function fechaConZona(valor) {
  if (valor === '') return undefined
  const fecha = new Date(valor)
  return Number.isNaN(fecha.getTime()) ? valor : fecha.toISOString()
}

// Identificador del espacio: número cuando el texto es numérico y, si no, el
// texto tal como se escribió.
export function espacioParaEnviar(texto) {
  if (texto.trim() === '') return undefined
  const numero = Number(texto)
  return Number.isNaN(numero) ? texto : numero
}
