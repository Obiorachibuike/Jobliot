// @vitest-environment jsdom
import React from 'react'
import { render, screen, fireEvent } from '@testing-library/react'
import { ThemeProvider, applyTheme } from './lib/theme'
import { Btn, Badge, Empty } from './components/ui'
describe('theme', ()=>{
  it('applies dark class and persists preference helpers', ()=>{
    expect(applyTheme('dark')).toBe(true); expect(document.documentElement.classList.contains('dark')).toBe(true)
    expect(applyTheme('light')).toBe(false); expect(document.documentElement.classList.contains('dark')).toBe(false)
  })
})
describe('components', ()=>{
  it('renders buttons, badges and empty states accessibly', ()=>{
    render(<ThemeProvider><div><Btn>Go</Btn><Badge>Strong Match</Badge><Empty title="Nothing here" text="Add your first item"/></div></ThemeProvider>)
    expect(screen.getByRole('button',{name:'Go'})).toBeTruthy()
    expect(screen.getByText('Strong Match')).toBeTruthy()
    expect(screen.getByText('Nothing here')).toBeTruthy()
  })
  it('button click fires', ()=>{
    let n=0; render(<Btn onClick={()=>n++}>Hit</Btn>); fireEvent.click(screen.getByText('Hit')); expect(n).toBe(1)
  })
})
