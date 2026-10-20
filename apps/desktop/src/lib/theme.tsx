import React, { createContext, useContext, useEffect, useState } from 'react'
export type ThemePref = 'light'|'dark'|'system'
const Ctx = createContext<{pref:ThemePref; dark:boolean; setPref:(t:ThemePref)=>void}>({pref:'system',dark:false,setPref:()=>{}})
export const useTheme = ()=>useContext(Ctx)
export function applyTheme(pref:ThemePref): boolean {
  const dark = pref==='dark' || (pref==='system' && typeof window.matchMedia==='function' && window.matchMedia('(prefers-color-scheme: dark)').matches)
  document.documentElement.classList.toggle('dark', dark); return dark
}
export function ThemeProvider({children}:{children:React.ReactNode}) {
  const [pref,setPrefState] = useState<ThemePref>((localStorage.getItem('cp-theme') as ThemePref)||'system')
  const [dark,setDark] = useState(false)
  useEffect(()=>{ setDark(applyTheme(pref)) },[pref])
  useEffect(()=>{ if(typeof window.matchMedia!=='function') return; const mq=window.matchMedia('(prefers-color-scheme: dark)'); const h=()=>{ if(pref==='system') setDark(applyTheme('system')) }; mq.addEventListener('change',h); return ()=>mq.removeEventListener('change',h) },[pref])
  const setPref=(t:ThemePref)=>{ localStorage.setItem('cp-theme',t); setPrefState(t) }
  return <Ctx.Provider value={{pref,dark,setPref}}>{children}</Ctx.Provider>
}
