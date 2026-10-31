import { afterEach, describe, expect, it } from 'vitest'
import { cleanup, render, screen } from '@testing-library/react'
import App from './App.jsx'

afterEach(cleanup)

describe('App', () => {
  it('renderiza la aplicación', () => {
    render(<App />)
    expect(
      screen.getByRole('heading', { name: 'Reservas de espacios académicos' }),
    ).toBeDefined()
  })
})
