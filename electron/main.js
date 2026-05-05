const { app, BrowserWindow, ipcMain, shell, Tray, Menu, nativeImage } = require('electron');
const path = require('path');
const fs = require('fs');
const http = require('http');
const { spawn } = require('child_process');

const BACKEND_PORT = process.env.JARVIS_BACKEND_PORT || '8765';
const BACKEND_URL = `http://127.0.0.1:${BACKEND_PORT}`;

let backendProcess = null;
let mainWindow = null;
let splashWindow = null;
let tray = null;
let isQuitting = false;

function userDataFile(name) {
  return path.join(app.getPath('userData'), name);
}

function readWindowState() {
  try {
    const raw = fs.readFileSync(userDataFile('window-state.json'), 'utf8');
    return JSON.parse(raw);
  } catch {
    return { width: 1220, height: 760 };
  }
}

function saveWindowState(win) {
  if (!win || win.isDestroyed()) return;
  const bounds = win.getBounds();
  fs.mkdirSync(app.getPath('userData'), { recursive: true });
  fs.writeFileSync(userDataFile('window-state.json'), JSON.stringify(bounds, null, 2));
}

function resolvePythonCommand() {
  if (process.env.JARVIS_PYTHON) return process.env.JARVIS_PYTHON;
  const projectRoot = path.join(__dirname, '..');
  const localPython = process.platform === 'win32'
    ? path.join(projectRoot, '.venv', 'Scripts', 'python.exe')
    : path.join(projectRoot, '.venv', 'bin', 'python');
  if (fs.existsSync(localPython)) return localPython;
  return process.platform === 'win32' ? 'python' : 'python3';
}

function startBackend() {
  if (backendProcess) return;
  const python = resolvePythonCommand();
  const args = ['-m', 'uvicorn', 'backend.app.main:app', '--host', '127.0.0.1', '--port', BACKEND_PORT];

  backendProcess = spawn(python, args, {
    cwd: path.join(__dirname, '..'),
    env: {
      ...process.env,
      JARVIS_DATA_DIR: path.join(app.getPath('userData'), 'data'),
      JARVIS_PLUGIN_DIR: path.join(__dirname, '..', 'plugins')
    },
    stdio: ['ignore', 'pipe', 'pipe'],
    windowsHide: true
  });

  backendProcess.stdout.on('data', chunk => console.log(`[backend] ${chunk}`.trim()));
  backendProcess.stderr.on('data', chunk => console.error(`[backend] ${chunk}`.trim()));
  backendProcess.on('exit', code => {
    backendProcess = null;
    if (!isQuitting && code !== 0) {
      setTimeout(startBackend, 1000);
    }
  });
}

function waitForBackend(timeoutMs = 15000) {
  const started = Date.now();
  return new Promise((resolve, reject) => {
    const check = () => {
      const req = http.get(`${BACKEND_URL}/health`, res => {
        res.resume();
        if (res.statusCode === 200) resolve();
        else retry();
      });
      req.on('error', retry);
      req.setTimeout(1000, () => {
        req.destroy();
        retry();
      });
    };
    const retry = () => {
      if (Date.now() - started > timeoutMs) reject(new Error('Backend did not start in time'));
      else setTimeout(check, 300);
    };
    check();
  });
}

function isBackendAlive(timeoutMs = 1500) {
  return new Promise(resolve => {
    const req = http.get(`${BACKEND_URL}/health`, res => {
      res.resume();
      resolve(res.statusCode === 200);
    });
    req.on('error', () => resolve(false));
    req.setTimeout(timeoutMs, () => {
      req.destroy();
      resolve(false);
    });
  });
}

function createSplashWindow() {
  splashWindow = new BrowserWindow({
    width: 420,
    height: 280,
    frame: false,
    resizable: false,
    show: false,
    backgroundColor: '#0d1117',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true
    }
  });
  splashWindow.loadFile(path.join(__dirname, '..', 'renderer', 'splash.html'));
  splashWindow.once('ready-to-show', () => splashWindow.show());
}

function createMainWindow() {
  const state = readWindowState();
  const iconPath = path.join(__dirname, '..', 'renderer', 'assets', 'jarvis-logo.svg');
  mainWindow = new BrowserWindow({
    width: state.width || 1220,
    height: state.height || 760,
    x: state.x,
    y: state.y,
    minWidth: 920,
    minHeight: 620,
    title: 'J.A.R.V.I.S',
    icon: iconPath,
    backgroundColor: '#0d1117',
    show: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  mainWindow.loadFile(path.join(__dirname, '..', 'renderer', 'index.html'));
  mainWindow.once('ready-to-show', () => {
    if (splashWindow && !splashWindow.isDestroyed()) splashWindow.close();
    mainWindow.show();
  });
  mainWindow.on('close', () => saveWindowState(mainWindow));
}

function createTray() {
  const iconPath = path.join(__dirname, '..', 'renderer', 'assets', 'jarvis-logo.svg');
  const icon = nativeImage.createFromPath(iconPath);
  tray = new Tray(icon);
  tray.setToolTip('J.A.R.V.I.S');
  tray.setContextMenu(Menu.buildFromTemplate([
    { label: 'Open', click: () => mainWindow && mainWindow.show() },
    { type: 'separator' },
    {
      label: 'Exit',
      click: () => {
        isQuitting = true;
        app.quit();
      }
    }
  ]));
}

ipcMain.handle('app:openExternal', async (_event, url) => {
  const allowed = [
    'https://mkr-infinity.github.io/',
    'https://github.com/mkr-infinity/jarvis',
    'https://github.com/mkr-infinity/jarvis/issues',
    'https://buymeacoffee.com/mkr_infinity'
  ];
  if (allowed.includes(url)) await shell.openExternal(url);
});

ipcMain.handle('app:backendUrl', () => BACKEND_URL.replace('http', 'ws'));

app.whenReady().then(async () => {
  app.setName('J.A.R.V.I.S');
  createSplashWindow();
  if (!(await isBackendAlive())) startBackend();
  try {
    await waitForBackend();
  } catch (error) {
    console.error(error);
  }
  createMainWindow();
  createTray();
});

app.on('before-quit', () => {
  isQuitting = true;
  if (mainWindow) saveWindowState(mainWindow);
  if (backendProcess) backendProcess.kill();
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) createMainWindow();
});
