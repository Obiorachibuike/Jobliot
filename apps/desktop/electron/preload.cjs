const { contextBridge, ipcRenderer, shell } = require('electron')
contextBridge.exposeInMainWorld('careerpilot', {
  getApiToken: () => ipcRenderer.invoke('cp:get-api-token'),
  openExternal: (url) => { if (typeof url === 'string' && (url.startsWith('https://') || url.startsWith('http://'))) shell.openExternal(url) }
})
