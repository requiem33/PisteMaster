import { BrowserWindow, app } from 'electron'
import { join } from 'path'
import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'fs'

interface WindowState {
  x?: number
  y?: number
  width: number
  height: number
  isMaximized: boolean
}

const DEFAULT_STATE: WindowState = {
  width: 1400,
  height: 900,
  isMaximized: false,
}

function getStatePath(): string {
  const userDataPath = app.getPath('userData')
  if (!existsSync(userDataPath)) {
    mkdirSync(userDataPath, { recursive: true })
  }
  return join(userDataPath, 'window-state.json')
}

function loadState(): WindowState {
  const statePath = getStatePath()
  try {
    if (existsSync(statePath)) {
      const data = readFileSync(statePath, 'utf-8')
      const state = JSON.parse(data) as WindowState
      return { ...DEFAULT_STATE, ...state }
    }
  } catch (error) {
    console.error('Failed to load window state:', error)
  }
  return { ...DEFAULT_STATE }
}

function isValidPosition(x: number | undefined, y: number | undefined, width: number, height: number): boolean {
  if (x === undefined || y === undefined) return false
  
  const { screen } = require('electron')
  const displays = screen.getAllDisplays()
  
  return displays.some(display => {
    const { x: dx, y: dy, width: dw, height: dh } = display.bounds
    return x >= dx && x + width <= dx + dw && y >= dy && y + height <= dy + dh
  })
}

export function restoreWindowState(): WindowState {
  const state = loadState()
  
  if (!isValidPosition(state.x, state.y, state.width, state.height)) {
    state.x = undefined
    state.y = undefined
  }
  
  return state
}

export function saveWindowState(window: BrowserWindow): void {
  const statePath = getStatePath()
  
  const bounds = window.getBounds()
  const isMaximized = window.isMaximized()
  
  const state: WindowState = {
    x: bounds.x,
    y: bounds.y,
    width: bounds.width,
    height: bounds.height,
    isMaximized,
  }
  
  try {
    writeFileSync(statePath, JSON.stringify(state, null, 2))
  } catch (error) {
    console.error('Failed to save window state:', error)
  }
}