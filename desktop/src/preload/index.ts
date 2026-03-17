import { contextBridge, ipcRenderer } from 'electron'
import { electronAPI } from '@electron-toolkit/preload'

interface UpdateInfo {
  version: string
}

interface OpenFileDialogOptions {
  title?: string
  filters?: { name: string; extensions: string[] }[]
  multiSelections?: boolean
}

interface SaveFileDialogOptions {
  title?: string
  defaultPath?: string
  filters?: { name: string; extensions: string[] }[]
}

interface CheckUpdateResult {
  available: boolean
  version?: string
  error?: string
}

const api = {
  getAppVersion: (): Promise<string> => ipcRenderer.invoke('get-app-version'),
  getUserDataPath: (): Promise<string> => ipcRenderer.invoke('get-user-data-path'),
  getDatabasePath: (): Promise<string> => ipcRenderer.invoke('get-database-path'),
  getAppPath: (): Promise<string> => ipcRenderer.invoke('get-app-path'),

  openFileDialog: (options?: OpenFileDialogOptions): Promise<string[]> =>
    ipcRenderer.invoke('open-file-dialog', options),

  saveFileDialog: (options?: SaveFileDialogOptions): Promise<string | undefined> =>
    ipcRenderer.invoke('save-file-dialog', options),

  clearAppData: (): Promise<{ success: boolean; error?: string }> =>
    ipcRenderer.invoke('clear-app-data'),

  listDataFiles: (): Promise<string[]> => ipcRenderer.invoke('list-data-files'),

  quitAndInstall: (): void => ipcRenderer.send('quit-and-install'),

  checkForUpdates: (): Promise<CheckUpdateResult> => ipcRenderer.invoke('check-for-updates'),

  onUpdateAvailable: (callback: (info: UpdateInfo) => void): (() => void) => {
    const handler = (_event: Electron.IpcRendererEvent, info: UpdateInfo): void => {
      callback(info)
    }
    ipcRenderer.on('update-available', handler)
    return () => ipcRenderer.removeListener('update-available', handler)
  },
}

if (process.contextIsolated) {
  try {
    contextBridge.exposeInMainWorld('electron', {
      ...electronAPI,
      ...api,
    })
  } catch (error) {
    console.error('Failed to expose API:', error)
  }
} else {
  // @ts-expect-error - window.electron for non-isolated context
  window.electron = {
    ...electronAPI,
    ...api,
  }
}