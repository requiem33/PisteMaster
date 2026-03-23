import { app, BrowserWindow, shell, ipcMain } from 'electron'
import { join } from 'path'
import { electronApp, optimizer, is } from '@electron-toolkit/utils'
import { setupPythonServer, shutdownPythonServer } from './python-server'
import { setupIpcHandlers } from './ipc-handlers'
import { restoreWindowState, saveWindowState } from './window-state'

let mainWindow: BrowserWindow | null = null
let pythonProcess: ReturnType<typeof setupPythonServer> | null = null

async function createWindow(): Promise<BrowserWindow> {
  const windowState = restoreWindowState()

  const win = new BrowserWindow({
    width: windowState.width || 1400,
    height: windowState.height || 900,
    x: windowState.x,
    y: windowState.y,
    minWidth: 1024,
    minHeight: 768,
    show: false,
    autoHideMenuBar: true,
    webPreferences: {
      preload: join(__dirname, '../preload/index.js'),
      sandbox: false,
      contextIsolation: true,
      nodeIntegration: false,
    },
  })

  win.on('ready-to-show', () => {
    win.show()
    if (windowState.isMaximized) {
      win.maximize()
    }
  })

  win.webContents.setWindowOpenHandler((details) => {
    shell.openExternal(details.url)
    return { action: 'deny' }
  })

  win.on('close', () => {
    saveWindowState(win)
  })

  if (is.dev && process.env['ELECTRON_RENDERER_URL']) {
    await win.loadURL(process.env['ELECTRON_RENDERER_URL'])
  } else {
    const resourcesPath = process.resourcesPath || join(__dirname, '../../..')
    await win.loadFile(join(resourcesPath, 'app', 'index.html'))
  }

  return win
}

async function setupAutoUpdater(): Promise<void> {
  try {
    const { autoUpdater } = await import('electron-updater')
    
    autoUpdater.on('update-available', () => {
      console.log('Update available')
    })

    autoUpdater.on('update-downloaded', () => {
      mainWindow?.webContents.send('update-available')
    })

    setTimeout(() => {
      autoUpdater.checkForUpdatesAndNotify().catch((err) => {
        console.log('Update check failed:', err.message)
      })
    }, 3000)
  } catch (err) {
    console.log('Failed to setup auto-updater:', err)
  }
}

app.whenReady().then(async () => {
  electronApp.setAppUserModelId('com.pistemaster.app')

  app.on('browser-window-created', (_, window) => {
    optimizer.watchWindowShortcuts(window)
  })

  setupIpcHandlers(ipcMain)

  if (!is.dev) {
    pythonProcess = await setupPythonServer(false)
    await setupAutoUpdater()
  }

  mainWindow = await createWindow()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      mainWindow = createWindow()
    }
  })
})

app.on('before-quit', async () => {
  await shutdownPythonServer(pythonProcess)
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})