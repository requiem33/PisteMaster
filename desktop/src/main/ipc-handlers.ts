import { ipcMain, dialog, app, IpcMain } from 'electron'
import { join } from 'path'
import { existsSync } from 'fs'
import { readdir, unlink, mkdir } from 'fs/promises'

export function setupIpcHandlers(_ipcMain: IpcMain): void {
  ipcMain.handle('get-app-version', () => {
    return app.getVersion()
  })

  ipcMain.handle('get-user-data-path', () => {
    return app.getPath('userData')
  })

  ipcMain.handle('get-database-path', () => {
    return join(app.getPath('userData'), 'data', 'pistemaster.db')
  })

  ipcMain.handle('get-app-path', () => {
    return app.getAppPath()
  })

  ipcMain.handle('open-file-dialog', async (_event, options?: {
    title?: string
    filters?: { name: string; extensions: string[] }[]
    multiSelections?: boolean
  }) => {
    const result = await dialog.showOpenDialog({
      title: options?.title || 'Select File',
      filters: options?.filters || [{ name: 'All Files', extensions: ['*'] }],
      properties: [
        'openFile',
        ...(options?.multiSelections ? ['multiSelections'] as const : [])
      ],
    })
    return result.filePaths
  })

  ipcMain.handle('save-file-dialog', async (_event, options?: {
    title?: string
    defaultPath?: string
    filters?: { name: string; extensions: string[] }[]
  }) => {
    const result = await dialog.showSaveDialog({
      title: options?.title || 'Save File',
      defaultPath: options?.defaultPath,
      filters: options?.filters || [{ name: 'All Files', extensions: ['*'] }],
    })
    return result.filePath
  })

  ipcMain.handle('clear-app-data', async () => {
    const userDataPath = app.getPath('userData')
    const dataDir = join(userDataPath, 'data')
    const dbPath = join(dataDir, 'pistemaster.db')

    try {
      if (existsSync(dbPath)) {
        await unlink(dbPath)
      }
      return { success: true }
    } catch (error) {
      console.error('Failed to clear app data:', error)
      return { success: false, error: String(error) }
    }
  })

  ipcMain.handle('list-data-files', async () => {
    const userDataPath = app.getPath('userData')
    const dataDir = join(userDataPath, 'data')

    try {
      if (!existsSync(dataDir)) {
        return []
      }
      const files = await readdir(dataDir)
      return files.map(f => join(dataDir, f))
    } catch (error) {
      console.error('Failed to list data files:', error)
      return []
    }
  })

  ipcMain.on('quit-and-install', () => {
    const { autoUpdater } = require('electron-updater')
    autoUpdater.quitAndInstall()
  })

  ipcMain.handle('check-for-updates', async () => {
    const { autoUpdater } = require('electron-updater')
    try {
      const result = await autoUpdater.checkForUpdates()
      return {
        available: result?.updateInfo?.version !== app.getVersion(),
        version: result?.updateInfo?.version,
      }
    } catch (error) {
      console.error('Failed to check for updates:', error)
      return { available: false, error: String(error) }
    }
  })
}