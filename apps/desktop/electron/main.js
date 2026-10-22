import { app, BrowserWindow, ipcMain, shell } from 'electron'
import { spawn } from 'node:child_process'
import fs from 'node:fs'; import os from 'node:os'; import path from 'node:path'; import { fileURLToPath } from 'node:url'
const __dirname = path.dirname(fileURLToPath(import.meta.url))
const DATA = path.join(os.homedir(), '.careerpilot'); fs.mkdirSync(DATA, { recursive: true })
const TOKEN_FILE = path.join(DATA, '.api_token')
let backend = null
function readToken(){ try { return fs.readFileSync(TOKEN_FILE,'utf8').trim() } catch { return '' } }
function startBackend(){
  const isDev = !app.isPackaged
  const backendDir = isDev ? path.join(__dirname,'..','..','..','backend') : path.join(process.resourcesPath,'backend')
  const py = process.env.CAREERPILOT_PYTHON || (process.platform==='win32' ? 'python' : 'python3')
  backend = spawn(py, ['run.py'], { cwd: backendDir, env:{ ...process.env, CAREERPILOT_DATA_DIR: DATA }, stdio:'ignore' })
  backend.on('error', ()=>{} )
}
function createWindow(){
  const win = new BrowserWindow({ width:1440, height:920, minWidth:900, minHeight:600, title:'CareerPilot AI', backgroundColor:'#080B09',
    webPreferences:{ preload: path.join(__dirname,'preload.cjs'), contextIsolation:true, nodeIntegration:false, sandbox:true, webSecurity:true } })
  win.webContents.setWindowOpenHandler(({url})=>{ if(url.startsWith('http')) shell.openExternal(url); return {action:'deny'} })
  win.webContents.on('will-navigate',(e,url)=>{ const ok = url.startsWith('http://localhost:5173') || url.startsWith('file://'); if(!ok) e.preventDefault() })
  const dev = process.env.CAREERPILOT_DEV_URL
  if(dev) win.loadURL(dev); else win.loadFile(path.join(__dirname,'..','dist','index.html'))
  return win
}
ipcMain.handle('cp:get-api-token', ()=> readToken())
app.whenReady().then(()=>{ startBackend(); setTimeout(createWindow, 600)
  app.on('activate', ()=>{ if(BrowserWindow.getAllWindows().length===0) createWindow() }) })
app.on('window-all-closed', ()=>{ if(backend) backend.kill(); if(process.platform!=='darwin') app.quit() })
app.on('before-quit', ()=>{ if(backend) backend.kill() })
