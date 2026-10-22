declare global { interface Window { careerpilot?: { getApiToken: () => Promise<string>; openExternal: (u:string)=>void } } }
let tokenCache = ''
export async function getToken(): Promise<string> {
  if (tokenCache) return tokenCache
  if (window.careerpilot) { tokenCache = await window.careerpilot.getApiToken(); return tokenCache }
  tokenCache = localStorage.getItem('cp-api-token') || (import.meta as any).env?.VITE_CP_TOKEN || ''
  return tokenCache
}
export function setToken(t:string){ tokenCache=t; localStorage.setItem('cp-api-token',t) }
const BASE = (import.meta as any).env?.VITE_API_BASE || ''
export async function api(path:string, opts:RequestInit={}): Promise<any> {
  const t = await getToken()
  const res = await fetch(`${BASE}${path}`, { ...opts, headers:{ 'Content-Type':'application/json', 'x-careerpilot-token':t, ...(opts.headers||{}) } })
  if (!res.ok) { let msg = `Request failed (${res.status})`; try { const j = await res.json(); msg = typeof j.detail==='string'? j.detail : JSON.stringify(j.detail||j) } catch {} throw new Error(msg) }
  return res.status===204 ? null : res.json()
}
export async function apiUpload(path:string, file:File): Promise<any> {
  const t = await getToken(); const fd = new FormData(); fd.append('file', file)
  const res = await fetch(`${BASE}${path}`, { method:'POST', body:fd, headers:{ 'x-careerpilot-token':t } })
  if (!res.ok) { let m='Upload failed'; try{ m=(await res.json()).detail||m }catch{} throw new Error(m) }
  return res.json()
}
export async function download(path:string, filename:string) {
  const t = await getToken()
  const res = await fetch(`${BASE}${path}`, { headers:{ 'x-careerpilot-token':t } })
  if (!res.ok) throw new Error('Download failed')
  const blob = await res.blob(); const a = document.createElement('a')
  a.href = URL.createObjectURL(blob); a.download = filename; a.click(); URL.revokeObjectURL(a.href)
}
export const get = (p:string)=>api(p)
export const post = (p:string,b:any={})=>api(p,{method:'POST',body:JSON.stringify(b)})
export const put = (p:string,b:any)=>api(p,{method:'PUT',body:JSON.stringify(b)})
export const del = (p:string)=>api(p,{method:'DELETE'})
