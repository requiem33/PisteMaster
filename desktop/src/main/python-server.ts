import { spawn, ChildProcess } from 'child_process'
import { join } from 'path'
import { app } from 'electron'
import { is } from '@electron-toolkit/utils'

const PORT = 8000
const STARTUP_TIMEOUT = 15000

export function setupPythonServer(dev: boolean): Promise<ChildProcess> {
  return new Promise((resolve, reject) => {
    let backendPath: string
    let pythonPath: string
    let args: string[]

    if (dev) {
      backendPath = join(__dirname, '../../../../backend')
      pythonPath = 'python'
      args = ['manage.py', 'runserver', `127.0.0.1:${PORT}`]
    } else {
      backendPath = join(process.resourcesPath, 'python')
      pythonPath = join(backendPath, 'pistemaster-backend.exe')
      args = []
    }

    const env = {
      ...process.env,
      DJANGO_SETTINGS_MODULE: 'PisteMaster.settings.desktop',
      PYTHONUNBUFFERED: '1',
    }

    console.log(`Starting Python server from: ${backendPath}`)
    console.log(`Python path: ${pythonPath}`)
    console.log(`Args: ${args.join(' ')}`)

    const process_ = spawn(pythonPath, args, {
      cwd: dev ? backendPath : backendPath,
      env,
      stdio: ['pipe', 'pipe', 'pipe'],
    })

    const startupTimer = setTimeout(() => {
      if (process_.pid) {
        console.log('Python server startup timeout, assuming started')
        resolve(process_)
      } else {
        reject(new Error('Python server startup timeout'))
      }
    }, STARTUP_TIMEOUT)

    process_.stdout?.on('data', (data) => {
      const output = data.toString()
      console.log(`[Python] ${output}`)
      if (output.includes('Starting development server') || output.includes('Quit the server')) {
        clearTimeout(startupTimer)
        resolve(process_)
      }
    })

    process_.stderr?.on('data', (data) => {
      console.error(`[Python Error] ${data}`)
    })

    process_.on('error', (err) => {
      clearTimeout(startupTimer)
      console.error('Failed to start Python server:', err)
      reject(err)
    })

    process_.on('exit', (code) => {
      clearTimeout(startupTimer)
      if (code !== 0 && code !== null) {
        console.error(`Python server exited with code ${code}`)
      }
    })
  })
}

export async function shutdownPythonServer(process: ChildProcess | null): Promise<void> {
  if (!process) return

  return new Promise((resolve) => {
    const timeout = setTimeout(() => {
      if (process.pid) {
        process.kill('SIGKILL')
      }
      resolve()
    }, 5000)

    process.on('exit', () => {
      clearTimeout(timeout)
      resolve()
    })

    if (process.pid) {
      if (process.platform === 'win32') {
        spawn('taskkill', ['/pid', process.pid.toString(), '/f', '/t'])
      } else {
        process.kill('SIGTERM')
      }
    }
  })
}