import { app, BrowserWindow, shell, ipcMain, dialog } from 'electron'
import { join } from 'path'
import { electronApp, optimizer, is } from '@electron-toolkit/utils'
import { setupPythonServer, shutdownPythonServer } from './python-server'
import { setupIpcHandlers } from './ipc-handlers'
import { setupClusterIpcHandlers, setClusterState, updateLastHeartbeat } from './ipc/cluster-handlers'
import { restoreWindowState, saveWindowState } from './window-state'
import { loadClusterConfig } from './config/cluster'
import { udpBroadcastService } from './services/udp'

let mainWindow: BrowserWindow | null = null
let pythonProcess: ReturnType<typeof setupPythonServer> | null = null
let clusterInitialized = false

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

async function initializeCluster(): Promise<void> {
  if (clusterInitialized) {
    return
  }

  try {
    const config = loadClusterConfig()
    
    if (config.mode === 'cluster') {
      console.log('[Cluster] Initializing cluster mode...')
      
      await udpBroadcastService.start(config)
      
      udpBroadcastService.on('heartbeat', (_message, _remoteIp) => {
        updateLastHeartbeat()
      })
      
      udpBroadcastService.on('master_announce', (message, remoteIp) => {
        const masterUrl = `http://${message.ip || remoteIp}:${message.port || config.apiPort}`
        setClusterState(false, masterUrl, message.nodeId)
        console.log(`[Cluster] Master announced: ${message.nodeId} at ${masterUrl}`)
      })

      udpBroadcastService.on('peer_discovered', (peer) => {
        console.log(`[Cluster] Peer discovered: ${peer.nodeId} at ${peer.ip}:${peer.port}`)
      })

      udpBroadcastService.on('peer_left', (nodeId, reason) => {
        console.log(`[Cluster] Peer left: ${nodeId}, reason: ${reason || 'unknown'}`)
      })
      
      clusterInitialized = true
      console.log('[Cluster] Cluster mode initialized')
    } else {
      console.log('[Cluster] Running in single-node mode')
      clusterInitialized = true
    }
  } catch (error) {
    console.error('[Cluster] Failed to initialize cluster:', error)
  }
}

async function shutdownCluster(): Promise<void> {
  if (!clusterInitialized) {
    return
  }

  try {
    const config = loadClusterConfig()
    
    if (config.mode === 'cluster') {
      console.log('[Cluster] Shutting down cluster services...')
      await udpBroadcastService.stop()
      console.log('[Cluster] Cluster services stopped')
    }
  } catch (error) {
    console.error('[Cluster] Failed to shutdown cluster:', error)
  }
}

app.whenReady().then(async () => {
  electronApp.setAppUserModelId('com.pistemaster.app')

  app.on('browser-window-created', (_, window) => {
    optimizer.watchWindowShortcuts(window)
  })

  setupIpcHandlers(ipcMain)
  setupClusterIpcHandlers(ipcMain)

  mainWindow = await createWindow()

  if (!is.dev) {
    setupPythonServer(false)
      .then((proc) => {
        pythonProcess = proc
        setupAutoUpdater()
        initializeCluster()
      })
      .catch((err) => {
        console.error('Failed to start Python server:', err)
        dialog.showErrorBox(
          'Backend Error',
          'Failed to start the backend server. The application may not function correctly.'
        )
      })
  } else {
    initializeCluster()
  }

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      mainWindow = createWindow()
    }
  })
})

app.on('before-quit', async () => {
  await shutdownCluster()
  await shutdownPythonServer(pythonProcess)
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})