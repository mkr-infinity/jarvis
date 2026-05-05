const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('jarvisShell', {
  backendWsUrl: () => ipcRenderer.invoke('app:backendUrl'),
  openExternal: url => ipcRenderer.invoke('app:openExternal', url)
});
