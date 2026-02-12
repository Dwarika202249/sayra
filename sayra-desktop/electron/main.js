const { app, BrowserWindow, screen, ipcMain } = require('electron');
const path = require('path');

let mainWindow;

function createWindow() {
  const { width, height } = screen.getPrimaryDisplay().workAreaSize;

  mainWindow = new BrowserWindow({
    width: 120,          // Small Orb size
    height: 120,
    x: width - 150,      // Bottom-Right corner
    y: height - 150,
    frame: false,        // No title bar
    transparent: true,   // Transparent background
    alwaysOnTop: true,   // Always visible
    resizable: false,    // Fixed size initially
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false, // For simple proto, security can be tightened later
    },
  });
  
  // Load React App
  // Development mode mein hum seedha localhost load karenge
  const startUrl = 'http://localhost:5173';
  // Future Production Logic (abhi comment rakho):
  // const startUrl = process.env.ELECTRON_START_URL || `file://${path.join(__dirname, '../dist/index.html')}`;
  mainWindow.loadURL(startUrl);

  // DevTools (Optional: Comment out in prod)
  // mainWindow.webContents.openDevTools({ mode: 'detach' });
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});