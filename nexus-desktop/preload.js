const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods to the renderer process
contextBridge.exposeInMainWorld('nexusDesktop', {
    // Get backend URL
    getBackendUrl: () => ipcRenderer.invoke('get-backend-url'),

    // Get app version
    getAppVersion: () => ipcRenderer.invoke('get-app-version'),

    // Listen for system status updates
    onSystemStatus: (callback) => {
        ipcRenderer.on('system-status', (event, data) => callback(data));
    },

    // Listen for kill confirmation
    onKillExecuted: (callback) => {
        ipcRenderer.on('kill-executed', (event, data) => callback(data));
    },

    // Listen for update events
    onUpdateAvailable: (callback) => {
        ipcRenderer.on('update-available', () => callback());
    },

    onUpdateDownloaded: (callback) => {
        ipcRenderer.on('update-downloaded', () => callback());
    },

    // Platform info
    platform: process.platform,
    isDesktop: true
});
