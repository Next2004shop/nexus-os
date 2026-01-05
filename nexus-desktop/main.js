const { app, BrowserWindow, Menu, Tray, shell, ipcMain } = require('electron');
const { autoUpdater } = require('electron-updater');
const path = require('path');

// Configuration
const BACKEND_URL = 'https://nexus-core-29008535318.us-central1.run.app';
// const FRONTEND_URL = 'https://nexus-frontend-5fyoxvonna-uc.a.run.app'; // Production
const FRONTEND_URL = 'http://localhost:5173'; // Local Development (Capital Warfare UI)

let mainWindow;
let tray;

// Single instance lock
const gotTheLock = app.requestSingleInstanceLock();

if (!gotTheLock) {
    app.quit();
} else {
    app.on('second-instance', () => {
        if (mainWindow) {
            if (mainWindow.isMinimized()) mainWindow.restore();
            mainWindow.focus();
        }
    });
}

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 1400,
        height: 900,
        minWidth: 1024,
        minHeight: 768,
        title: 'NEXUS Terminal',
        icon: path.join(__dirname, 'assets', 'icon.png'),
        backgroundColor: '#0A0A0F',
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')
        },
        autoHideMenuBar: true,
        frame: true,
        show: false
    });

    // Load the frontend
    // mainWindow.loadURL(FRONTEND_URL);
    mainWindow.loadFile(path.join(__dirname, 'app_renderer', 'index.html'));

    // Show when ready
    mainWindow.once('ready-to-show', () => {
        mainWindow.webContents.openDevTools();
        mainWindow.show();
    });

    // Handle external links
    mainWindow.webContents.setWindowOpenHandler(({ url }) => {
        shell.openExternal(url);
        return { action: 'deny' };
    });

    // Minimize to tray
    mainWindow.on('close', (event) => {
        if (!app.isQuitting) {
            event.preventDefault();
            mainWindow.hide();
        }
    });
}

function createTray() {
    try {
        const iconPath = path.join(__dirname, 'assets', 'tray-icon.png');
        tray = new Tray(iconPath);

        const contextMenu = Menu.buildFromTemplate([
            { label: 'Open NEXUS', click: () => mainWindow.show() },
            { type: 'separator' },
            { label: 'System Status', click: () => checkSystemStatus() },
            { label: 'Emergency Kill', click: () => emergencyKill() },
            { type: 'separator' },
            {
                label: 'Quit', click: () => {
                    app.isQuitting = true;
                    app.quit();
                }
            }
        ]);

        tray.setToolTip('NEXUS Terminal - Trading Active');
        tray.setContextMenu(contextMenu);

        tray.on('click', () => {
            mainWindow.show();
        });
    } catch (e) {
        console.warn('[NEXUS] System Tray init failed (Icon missing). Running in detached mode.');
    }
}

async function checkSystemStatus() {
    try {
        const response = await fetch(`${BACKEND_URL}/health`);
        const data = await response.json();
        mainWindow.webContents.send('system-status', data);
    } catch (error) {
        console.error('Status check failed:', error);
    }
}

async function emergencyKill() {
    try {
        const response = await fetch(`${BACKEND_URL}/kill`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await response.json();
        mainWindow.webContents.send('kill-executed', data);
    } catch (error) {
        console.error('Emergency kill failed:', error);
    }
}

// App lifecycle
app.whenReady().then(() => {
    createWindow();
    try {
        createTray();
    } catch (e) {
        console.warn("[NEXUS] Tray icon failed to load (Non-Critical):", e);
    }

    // Check for updates (Safe Mode)
    try {
        // autoUpdater.checkForUpdatesAndNotify();
        console.log('[NEXUS] Updater disabled for stability.');
    } catch (err) {
        console.error('[NEXUS] Updater error:', err);
    }
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        // Don't quit on Windows/Linux - stay in tray
    }
});

app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
        createWindow();
    } else {
        mainWindow.show();
    }
});

// Global Error Handlers (Prevents "Crushing")
process.on('uncaughtException', (error) => {
    console.error('[NEXUS] CRITICAL ERROR:', error);
    // Prevent app quit
});

process.on('unhandledRejection', (reason, promise) => {
    console.error('[NEXUS] UNHANDLED REJECTION:', reason);
    // Prevent app quit
});

// Auto-updater events (Listeners preserved but inactive)
/* 
autoUpdater.on('update-available', () => {
    mainWindow.webContents.send('update-available');
});
 
autoUpdater.on('update-downloaded', () => {
    mainWindow.webContents.send('update-downloaded');
});
*/
/* ipcMain handlers remain... */
ipcMain.handle('get-backend-url', () => BACKEND_URL);
ipcMain.handle('get-app-version', () => app.getVersion());
