// @vitest-environment node
//
// Pruebas estáticas de los estilos (spec estilos-interfaz; design.md, D8). jsdom
// no calcula el diseño, así que aquí se comprueba lo que puede leerse en el CSS,
// incluido el contraste, que se calcula con los valores de las variables.

import { readdirSync, readFileSync } from 'node:fs'
import { join, resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const RAIZ = resolve(process.cwd(), 'src')
const DIRECTORIO = join(RAIZ, 'estilos')
const ESTADOS = ['pendiente', 'aprobada', 'rechazada', 'cancelada']

function leer(nombre) {
  return readFileSync(join(DIRECTORIO, nombre), 'utf8').replace(/\/\*[\s\S]*?\*\//g, '')
}

function archivosCss() {
  return readdirSync(DIRECTORIO).filter((nombre) => nombre.endsWith('.css'))
}

function todoElCss() {
  return archivosCss().map(leer).join('\n')
}

// Lista plana de reglas { selector, cuerpo, media }, con una sola capa de @media.
function reglas(css, media = null) {
  const resultado = []
  let i = 0
  while (i < css.length) {
    const apertura = css.indexOf('{', i)
    if (apertura === -1) break
    const selector = css
      .slice(i, apertura)
      .replace(/@import[^;]*;/g, '')
      .trim()
    let nivel = 1
    let j = apertura + 1
    while (j < css.length && nivel > 0) {
      if (css[j] === '{') nivel += 1
      if (css[j] === '}') nivel -= 1
      j += 1
    }
    const cuerpo = css.slice(apertura + 1, j - 1)
    if (selector.startsWith('@media')) {
      resultado.push(...reglas(cuerpo, selector))
    } else {
      resultado.push({ selector, cuerpo, media })
    }
    i = j
  }
  return resultado
}

// Cuerpos de las reglas fuera de @media cuyo selector incluye `fragmento`.
function cuerposDe(css, fragmento) {
  return reglas(css)
    .filter((regla) => regla.media === null && regla.selector.includes(fragmento))
    .map((regla) => regla.cuerpo)
    .join('\n')
}

function variablesDe(cuerpo) {
  const variables = {}
  for (const [, nombre, valor] of cuerpo.matchAll(/(--[\w-]+)\s*:\s*([^;]+);/g)) {
    variables[nombre] = valor.trim()
  }
  return variables
}

function modosDeColor() {
  const raices = reglas(leer('variables.css')).filter((regla) => regla.selector === ':root')
  const claro = variablesDe(raices.find((regla) => regla.media === null).cuerpo)
  const soloOscuro = variablesDe(
    raices.find((regla) => regla.media === '@media (prefers-color-scheme: dark)').cuerpo,
  )
  return { claro, oscuro: { ...claro, ...soloOscuro }, soloOscuro }
}

function nombresDeColor(variables) {
  return Object.keys(variables)
    .filter((nombre) => nombre.startsWith('--color-'))
    .sort()
}

// Relación de contraste de WCAG 2.1 entre dos colores #rrggbb.
function luminancia(hex) {
  const canales = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255)
  const [r, g, b] = canales.map((c) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4))
  return 0.2126 * r + 0.7152 * g + 0.0722 * b
}

function contraste(a, b) {
  const [claro, oscuro] = [luminancia(a), luminancia(b)].sort((x, y) => y - x)
  return (claro + 0.05) / (oscuro + 0.05)
}

const PARES_DE_TEXTO = [
  ['texto', 'fondo'],
  ['texto', 'superficie'],
  ['texto', 'fila-alterna'],
  ['texto-suave', 'fondo'],
  ['texto-suave', 'superficie'],
  ['texto-suave', 'fila-alterna'],
  ['enlace', 'fondo'],
  ['enlace', 'superficie'],
  ['primario-texto', 'primario'],
  ['primario-texto', 'primario-hover'],
  ['secundario-texto', 'secundario'],
  ['secundario-texto', 'secundario-hover'],
  ['peligro-texto', 'peligro'],
  ['peligro-texto', 'peligro-hover'],
  ['deshabilitado-texto', 'deshabilitado'],
  ['error-texto', 'error-fondo'],
  ['exito-texto', 'exito-fondo'],
  ...ESTADOS.flatMap((estado) => [
    [`${estado}-texto`, 'superficie'],
    [`${estado}-texto`, 'fila-alterna'],
  ]),
]

const PARES_NO_TEXTUALES = [
  ['foco', 'fondo'],
  ['foco', 'superficie'],
  ['borde-control', 'superficie'],
  ['error-borde', 'error-fondo'],
  ['exito-borde', 'exito-fondo'],
]

describe('Variables de diseño globales', () => {
  it('existe al menos una variable de cada familia', () => {
    const { claro } = modosDeColor()
    for (const familia of ['--color-', '--espacio-', '--radio-', '--sombra-', '--fuente-']) {
      expect(
        Object.keys(claro).some((nombre) => nombre.startsWith(familia)),
        familia,
      ).toBe(true)
    }
  })

  it('las variables citadas por el contraste existen con valor #rrggbb', () => {
    const { claro } = modosDeColor()
    for (const nombre of new Set([...PARES_DE_TEXTO, ...PARES_NO_TEXTUALES].flat())) {
      expect(claro[`--color-${nombre}`], nombre).toMatch(/^#[0-9a-f]{6}$/i)
    }
  })

  it('todos los valores de color son #rrggbb en ambos modos', () => {
    const { claro, oscuro } = modosDeColor()
    for (const variables of [claro, oscuro]) {
      for (const nombre of nombresDeColor(variables)) {
        expect(variables[nombre], nombre).toMatch(/^#[0-9a-f]{6}$/i)
      }
    }
  })

  it('la tipografía es una pila de fuentes del sistema', () => {
    expect(modosDeColor().claro['--fuente-sistema']).toMatch(/^system-ui,[\s\S]*sans-serif$/)
  })

  it('fuera de variables.css no hay colores literales', () => {
    for (const nombre of archivosCss().filter((n) => n !== 'variables.css')) {
      expect(leer(nombre), nombre).not.toMatch(/#[0-9a-f]{3,8}\b|\b(rgba?|hsla?)\(/i)
    }
  })

  it('no hay recursos externos ni @font-face', () => {
    const css = todoElCss()
    expect(css).not.toMatch(/url\(\s*['"]?(https?:)?\/\//i)
    expect(css).not.toMatch(/@font-face/i)
    expect(css).not.toMatch(/@import\s+['"]?(https?:)?\/\//i)
  })

  it('main.jsx importa el punto de entrada y este importa cada archivo', () => {
    expect(readFileSync(join(RAIZ, 'main.jsx'), 'utf8')).toContain("import './estilos/index.css'")
    const entrada = leer('index.css')
    for (const nombre of archivosCss().filter((n) => n !== 'index.css')) {
      expect(entrada, nombre).toContain(`@import './${nombre}';`)
    }
  })
})

describe('Modo claro y oscuro automático', () => {
  it('el modo oscuro redefine exactamente las mismas variables de color', () => {
    const { claro, soloOscuro } = modosDeColor()
    expect(nombresDeColor(soloOscuro)).toEqual(nombresDeColor(claro))
  })

  it('declara color-scheme: light dark', () => {
    expect(cuerposDe(leer('variables.css'), ':root')).toMatch(/color-scheme:\s*light dark\s*;/)
  })
})

describe('Foco visible y movimiento reducido', () => {
  it('la regla :focus-visible declara outline con --color-foco', () => {
    expect(cuerposDe(leer('base.css'), ':focus-visible')).toMatch(
      /outline:[^;]*var\(--color-foco\)/,
    )
  })

  it('ninguna regla suprime el contorno de foco', () => {
    expect(todoElCss()).not.toMatch(/outline(-style)?\s*:\s*(none|0)\b/i)
  })

  it('con movimiento reducido se desactivan las transiciones', () => {
    const regla = reglas(todoElCss()).find(
      (r) => r.media === '@media (prefers-reduced-motion: reduce)',
    )
    expect(regla.cuerpo).toMatch(/transition:\s*none/)
  })
})

describe('Composición de las pantallas', () => {
  it.each(['header', 'nav', 'main', 'main > section', 'main.pagina-acceso'])(
    'existe una regla para %s',
    (selector) => {
      expect(cuerposDe(leer('composicion.css'), selector)).not.toBe('')
    },
  )

  it('el contenedor principal declara un ancho máximo', () => {
    const main = reglas(leer('composicion.css')).find(
      (regla) => regla.selector === 'main' && regla.media === null,
    )
    expect(main.cuerpo).toMatch(/max-width:/)
  })
})

describe('Formularios y botones coherentes', () => {
  it.each(['.boton-primario', '.boton-peligro', '[type="submit"]', ':disabled'])(
    'existe una regla para %s',
    (selector) => {
      expect(cuerposDe(leer('botones.css'), selector)).not.toBe('')
    },
  )

  it('existe la regla del botón por defecto, que es la variante secundaria', () => {
    const boton = reglas(leer('botones.css')).find(
      (regla) => regla.selector === 'button' && regla.media === null,
    )
    expect(boton.cuerpo).toContain('var(--color-secundario)')
    expect(boton.cuerpo).toContain('var(--color-secundario-texto)')
  })

  it('el envío no supera en especificidad a .boton-peligro', () => {
    expect(leer('botones.css')).toContain('button:where([type="submit"])')
  })

  it('el botón deshabilitado cambia de cursor y de borde, no solo de color', () => {
    const deshabilitado = cuerposDe(leer('botones.css'), ':disabled')
    expect(deshabilitado).toMatch(/cursor:\s*not-allowed/)
    expect(deshabilitado).toMatch(/border:[^;]*dashed/)
  })

  it('los campos comparten una misma regla', () => {
    const campos = reglas(leer('formularios.css')).find(
      (regla) => /^input,\s*select,\s*textarea$/.test(regla.selector) && regla.media === null,
    )
    expect(campos.cuerpo).toContain('var(--color-borde-control)')
  })
})

describe('Composición de las pantallas: tablas', () => {
  it('existen reglas para th y para las filas alternas', () => {
    const css = leer('tablas.css')
    expect(cuerposDe(css, 'th')).not.toBe('')
    expect(cuerposDe(css, 'tbody tr:nth-child(even)')).toContain('var(--color-fila-alterna)')
  })

  it('.fecha no parte la línea y usa cifras tabulares', () => {
    const fecha = cuerposDe(leer('tablas.css'), '.fecha')
    expect(fecha).toMatch(/white-space:\s*nowrap/)
    expect(fecha).toMatch(/font-variant-numeric:\s*tabular-nums/)
  })

  it.each(['tablas.css', 'insignias.css'])('%s no declara display', (nombre) => {
    expect(leer(nombre)).not.toMatch(/(^|[\s;{])display\s*:/)
  })
})

describe('Insignias de estado de una solicitud', () => {
  it.each(ESTADOS)('.insignia-%s usa la variable de texto de su estado', (estado) => {
    expect(cuerposDe(leer('insignias.css'), `.insignia-${estado}`)).toContain(
      `var(--color-${estado}-texto)`,
    )
  })

  it('.insignia::before declara un punto decorativo', () => {
    expect(cuerposDe(leer('insignias.css'), '.insignia::before')).toMatch(
      /content:\s*"[^"]+"\s*\/\s*""\s*;/,
    )
  })

  it('las insignias no tienen fondo propio', () => {
    expect(leer('insignias.css')).not.toMatch(/background/)
  })
})

describe('Mensajes de error y de éxito distinguibles', () => {
  function reglaExacta(selector) {
    return reglas(leer('mensajes.css')).find((regla) => regla.selector === selector).cuerpo
  }

  it('cada rol usa sus propias variables', () => {
    expect(reglaExacta('[role="alert"]')).toMatch(/--color-error-texto[\s\S]*--color-error-fondo/)
    expect(reglaExacta('[role="status"]')).toMatch(/--color-exito-texto[\s\S]*--color-exito-fondo/)
  })

  it('los símbolos son distintos', () => {
    const simbolo = (selector) => reglaExacta(selector).match(/content:\s*"([^"]+)"/)[1]
    expect(simbolo('[role="alert"]::before')).not.toBe(simbolo('[role="status"]::before'))
  })

  it('toda declaración content con símbolo tiene un texto alternativo vacío', () => {
    const contenidos = [...todoElCss().matchAll(/content:\s*([^;]+);/g)].map(([, valor]) => valor)
    expect(contenidos.length).toBeGreaterThan(0)
    for (const valor of contenidos) {
      expect(valor).toMatch(/^"[^"]+"\s*\/\s*""$/)
    }
  })

  it('la sección de éxito usa el borde de éxito', () => {
    expect(cuerposDe(leer('mensajes.css'), '.tarjeta-exito')).toContain('var(--color-exito-borde)')
  })
})

describe('Adaptación a móvil', () => {
  const MOVIL = '@media (max-width: 640px)'

  it('el bloque móvil da a botones y campos una altura mínima de 44 px', () => {
    for (const [nombre, selector] of [
      ['botones.css', 'button'],
      ['formularios.css', 'input'],
    ]) {
      const regla = reglas(leer(nombre)).find(
        (r) => r.media === MOVIL && r.selector.includes(selector),
      )
      expect(regla.cuerpo, nombre).toMatch(/min-height:\s*44px/)
    }
  })

  it('el bloque móvil reorganiza la navegación', () => {
    const regla = reglas(leer('composicion.css')).find(
      (r) => r.media === MOVIL && r.selector === 'header > nav',
    )
    expect(regla.cuerpo).toMatch(/flex-basis:\s*100%/)
  })

  it('la tarjeta se desplaza dentro de sí misma', () => {
    const regla = reglas(leer('composicion.css')).find(
      (r) => r.media === null && r.selector === 'main > section',
    )
    expect(regla.cuerpo).toMatch(/overflow-x:\s*auto/)
  })
})

describe('Contraste suficiente', () => {
  describe.each(['claro', 'oscuro'])('modo %s', (modo) => {
    it.each(PARES_DE_TEXTO)('texto %s sobre %s alcanza 4,5:1', (primerPlano, fondo) => {
      const variables = modosDeColor()[modo]
      const relacion = contraste(variables[`--color-${primerPlano}`], variables[`--color-${fondo}`])
      expect(relacion).toBeGreaterThanOrEqual(4.5)
    })

    it.each(PARES_NO_TEXTUALES)('indicador %s sobre %s alcanza 3:1', (primerPlano, fondo) => {
      const variables = modosDeColor()[modo]
      const relacion = contraste(variables[`--color-${primerPlano}`], variables[`--color-${fondo}`])
      expect(relacion).toBeGreaterThanOrEqual(3)
    })
  })
})
