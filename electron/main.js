'use strict'
/**
 * electron/main.js
 * Electron main process — manages backend.exe lifecycle and BrowserWindow.
 */

const { app, BrowserWindow, dialog } = require('electron')
const { spawn } = require('child_process')
const path = require('path')
const readline = require('readline')
const { findFreePort, parseListeningPort } = require('./utils')

// ─────────────────────────────────────────────────────────────────
// Constants
// ─────────────────────────────────────────────────────────────────
const HEALTH_POLL_INTERVAL_MS = 250
const HEALTH_POLL_TIMEOUT_MS = 30_000
const WINDOW_WIDTH = 1100
const WINDOW_HEIGHT = 760

// ─────────────────────────────────────────────────────────────────
// Backend executable path
//   frozen (packaged): resources/backend/backend.exe  (electron-builder extraResources)
//   dev:               dist/backend/backend.exe        (PyInstaller output)
// ─────────────────────────────────────────────────────────────────
function getBackendExePath() {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, 'backend', 'backend.exe')
  }
  return path.join(__dirname, '..', 'dist', 'backend', 'backend.exe')
}

// ─────────────────────────────────────────────────────────────────
// Health polling
// ─────────────────────────────────────────────────────────────────
function pollUntilHealthy(port) {
  return new Promise((resolve, reject) => {
    const url = `http://127.0.0.1:${port}/health`
    const deadline = Date.now() + HEALTH_POLL_TIMEOUT_MS

    function attempt() {
      if (Date.now() >= deadline) {
        reject(new Error(`Health check timed out after ${HEALTH_POLL_TIMEOUT_MS / 1000}s`))
        return
      }
      fetch(url)
        .then((res) => {
          if (res.ok) resolve()
          else setTimeout(attempt, HEALTH_POLL_INTERVAL_MS)
        })
        .catch(() => setTimeout(attempt, HEALTH_POLL_INTERVAL_MS))
    }

    attempt()
  })
}

// ─────────────────────────────────────────────────────────────────
// Main
// ─────────────────────────────────────────────────────────────────
let mainWindow = null
let backendProc = null

function killBackend() {
  if (backendProc) {
    try {
      backendProc.kill()
    } catch (_) {
      // process may already be gone
    }
    backendProc = null
  }
}

async function launchApp() {
  let port
  try {
    port = await findFreePort()
  } catch (err) {
    dialog.showErrorBox('ShortsGak', `포트 탐색 실패:\n${err.message}`)
    app.quit()
    return
  }

  const exePath = getBackendExePath()
  backendProc = spawn(exePath, ['--port', String(port)], {
    stdio: ['ignore', 'pipe', 'pipe'],
  })

  backendProc.stderr.on('data', (data) => {
    const text = data.toString()
    if (text.startsWith('ERROR:')) {
      console.error('[backend stderr]', text.trim())
    }
  })

  // Wait for LISTENING_PORT=N on stdout, then poll /health.
  // 'error' (ENOENT / EACCES) and 'exit' are both funnelled into the same
  // rejection path so we never show two dialogs or call app.quit() twice.
  const rl = readline.createInterface({ input: backendProc.stdout })
  let portConfirmed = false

  const portPromise = new Promise((resolve, reject) => {
    const timeout = setTimeout(() => {
      rl.close()
      reject(new Error('Timed out waiting for LISTENING_PORT signal'))
    }, HEALTH_POLL_TIMEOUT_MS)

    function fail(err) {
      if (portConfirmed) return
      clearTimeout(timeout)
      rl.close()
      reject(err)
    }

    rl.on('line', (line) => {
      if (portConfirmed) return
      const parsed = parseListeningPort(line)
      if (parsed !== null) {
        portConfirmed = true
        clearTimeout(timeout)
        rl.close()
        resolve(parsed)
      }
    })

    backendProc.on('error', (err) => {
      fail(new Error(`backend.exe 실행 실패: ${err.message}\n경로: ${exePath}`))
    })

    backendProc.on('exit', (code) => {
      if (!portConfirmed) {
        fail(new Error(`backend.exe 조기 종료 (exit code ${code})`))
      }
    })
  })

  let confirmedPort
  try {
    confirmedPort = await portPromise
  } catch (err) {
    dialog.showErrorBox('ShortsGak', `서버 시작 실패:\n${err.message}`)
    killBackend()
    app.quit()
    return
  }

  try {
    await pollUntilHealthy(confirmedPort)
  } catch (err) {
    dialog.showErrorBox('ShortsGak', `서버 응답 없음:\n${err.message}`)
    killBackend()
    app.quit()
    return
  }

  // Server ready — open window
  mainWindow = new BrowserWindow({
    width: WINDOW_WIDTH,
    height: WINDOW_HEIGHT,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
    },
  })

  mainWindow.loadURL(`http://127.0.0.1:${confirmedPort}`)

  mainWindow.on('closed', () => {
    mainWindow = null
  })
}

app.whenReady().then(launchApp)

app.on('window-all-closed', () => {
  killBackend()
  app.quit()
})

app.on('before-quit', () => {
  killBackend()
})
