const { app, BrowserWindow, globalShortcut, screen } = require('electron');
const { spawn } = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');

// Windows occlusion hesaplamasını kapat — transparent overlay yanlışlıkla
// "occluded" algılanıp rendering pause edilebilir; game overlay için şart
app.commandLine.appendSwitch('disable-features', 'CalculateNativeWinOcclusion');

const isDev = !app.isPackaged;

let overlayWin = null;
let backendProcess = null;

function startBackend() {
  if (isDev) {
    // Dev modda kullanıcı backend'i kendi terminalinde manuel başlatır
    return;
  }
  const backendPath = path.join(process.resourcesPath, 'f1-leaderboard-backend.exe');
  if (!fs.existsSync(backendPath)) {
    console.error('[backend] exe bulunamadı:', backendPath);
    return;
  }
  try {
    backendProcess = spawn(backendPath, [], {
      cwd: path.dirname(backendPath),
      windowsHide: true,
      stdio: 'ignore',
      detached: false,
    });
    backendProcess.on('error', (err) => console.error('[backend] error:', err));
    backendProcess.on('exit', (code) => {
      console.log('[backend] exit code=', code);
      backendProcess = null;
    });
  } catch (err) {
    console.error('[backend] spawn failed:', err);
  }
}

function stopBackend() {
  if (backendProcess && !backendProcess.killed) {
    try {
      backendProcess.kill();
    } catch (err) {
      console.error('[backend] kill failed:', err);
    }
    backendProcess = null;
  }
}

function createOverlay() {
  const primary = screen.getPrimaryDisplay();
  const { width: sw, height: sh } = primary.workAreaSize;

  overlayWin = new BrowserWindow({
    width: 325,
    height: Math.min(680, sh - 40),
    x: 40,
    y: 155,
    frame: false,
    transparent: true,
    backgroundColor: '#00000000',
    resizable: false,
    movable: true,
    hasShadow: false,
    thickFrame: false,
    skipTaskbar: true,
    focusable: false,
    show: false,
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      contextIsolation: true,
      nodeIntegration: false,
      backgroundThrottling: false,
      enableBlinkFeatures: '',
      spellcheck: false,
    },
  });

  overlayWin.setAlwaysOnTop(true, 'screen-saver');
  overlayWin.setVisibleOnAllWorkspaces(true, { visibleOnFullScreen: true });
  overlayWin.setIgnoreMouseEvents(true, { forward: true });
  overlayWin.setMenuBarVisibility(false);

  if (isDev) {
    overlayWin.loadURL('http://localhost:5173');
  } else {
    overlayWin.loadFile(path.join(__dirname, '..', 'dist', 'index.html'));
  }

  overlayWin.once('ready-to-show', () => overlayWin.show());
}

function registerShortcuts() {
  globalShortcut.register('Control+Shift+F1', () => {
    if (!overlayWin) return;
    if (overlayWin.isVisible()) overlayWin.hide();
    else overlayWin.show();
  });
  globalShortcut.register('Control+Shift+Q', () => app.quit());
  if (isDev) {
    globalShortcut.register('Control+Shift+I', () => {
      if (overlayWin) overlayWin.webContents.openDevTools({ mode: 'detach' });
    });
  }
}

app.whenReady().then(() => {
  startBackend();
  createOverlay();
  registerShortcuts();
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createOverlay();
  });
});

app.on('will-quit', () => {
  globalShortcut.unregisterAll();
  stopBackend();
});

app.on('window-all-closed', () => {
  stopBackend();
  if (process.platform !== 'darwin') app.quit();
});
