/**
 * Preload bridge. Exposes a minimal, explicit surface to the
 * renderer. Nothing else from Node or Electron is reachable
 * from web content.
 */

const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("careerpilot", {
  getApiToken: () => ipcRenderer.invoke("careerpilot:getApiToken"),
  getVersion: () => ipcRenderer.invoke("careerpilot:getVersion"),
  platform: process.platform,
});
