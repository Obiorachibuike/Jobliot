import React from 'react'
export const Card = ({children,className=''}:{children:React.ReactNode;className?:string}) =>
  <div className={`rounded-2xl border bg-mist-surface border-mist-line dark:bg-ink-surface dark:border-ink-line p-5 ${className}`}>{children}</div>
export const Btn = ({children,onClick,variant='primary',disabled,title,type}:any) => {
  const styles:any = {
    primary:'bg-neon text-black font-semibold hover:bg-neonHover dark:shadow-glow disabled:opacity-40',
    ghost:'border border-mist-line dark:border-ink-line hover:bg-mist-alt dark:hover:bg-ink-alt disabled:opacity-40',
    danger:'bg-red-600 text-white hover:bg-red-500 disabled:opacity-40',
    subtle:'text-pgreen dark:text-neon hover:underline text-sm' }
  return <button type={type||'button'} title={title} disabled={disabled} onClick={onClick} className={`inline-flex items-center gap-2 rounded-xl px-4 py-2 text-sm transition ${styles[variant]}`}>{children}</button>
}
export const Input = (p:any)=><input {...p} className={`w-full rounded-xl border px-3 py-2 text-sm bg-white border-mist-line text-dk dark:bg-ink-input dark:border-ink-line dark:text-fg placeholder:text-mute ${p.className||''}`}/>
export const Textarea = (p:any)=><textarea {...p} className={`w-full rounded-xl border px-3 py-2 text-sm bg-white border-mist-line text-dk dark:bg-ink-input dark:border-ink-line dark:text-fg placeholder:text-mute ${p.className||''}`}/>
export const Select = (p:any)=><select {...p} className={`rounded-xl border px-3 py-2 text-sm bg-white border-mist-line text-dk dark:bg-ink-input dark:border-ink-line dark:text-fg ${p.className||''}`}>{p.children}</select>
export const Label = ({children,htmlFor}:{children:React.ReactNode;htmlFor?:string})=><label htmlFor={htmlFor} className="block text-xs font-medium mb-1 text-dsub dark:text-sub">{children}</label>
export const Badge = ({children,tone='neutral'}:any)=>{
  const tones:any={ neutral:'bg-mist-alt dark:bg-ink-alt', green:'bg-green-100 text-green-900 dark:bg-green-950 dark:text-green-300 border border-green-400/40', amber:'bg-yellow-100 text-yellow-900 dark:bg-yellow-950 dark:text-yellow-300', red:'bg-red-100 text-red-900 dark:bg-red-950 dark:text-red-300' }
  return <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ${tones[tone]}`}>{children}</span> }
export const Empty = ({title,text,action}:any)=><Card className="text-center py-10"><p className="font-semibold">{title}</p><p className="text-sm text-dsub dark:text-sub mt-1 max-w-md mx-auto">{text}</p>{action&&<div className="mt-4">{action}</div>}</Card>
export const Skeleton = ()=><div className="space-y-3" aria-label="Loading"><div className="skeleton h-24 rounded-2xl bg-mist-alt dark:bg-ink-elev"/><div className="skeleton h-24 rounded-2xl bg-mist-alt dark:bg-ink-elev"/></div>
export const ScoreRing = ({score}:{score:number})=>{
  const label = score>=70?'Strong':score>=50?'Good':score>=30?'Stretch':'Low'
  return <div className="text-center" role="img" aria-label={`Match score ${score} percent, ${label}`}>
    <div className="text-2xl font-bold text-pgreen dark:text-neon">{score}%</div><div className="text-[11px] text-dsub dark:text-sub">{label} match</div></div> }
export function Confirm({open,title,text,onCancel,onConfirm}:any){
  if(!open) return null
  return <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" role="dialog" aria-modal="true" aria-label={title}>
    <Card className="max-w-md w-full"><h2 className="font-bold text-lg">{title}</h2><p className="text-sm mt-2 text-dsub dark:text-sub">{text}</p>
    <div className="flex justify-end gap-2 mt-5"><Btn variant="ghost" onClick={onCancel}>Cancel</Btn><Btn variant="danger" onClick={onConfirm}>Confirm</Btn></div></Card></div> }
export function Toasts({items}:{items:{id:number;msg:string;kind:string}[]}){
  return <div className="fixed bottom-4 right-4 z-50 space-y-2" aria-live="polite">{items.map(t=>
    <div key={t.id} className={`rounded-xl px-4 py-3 text-sm shadow-lg border ${t.kind==='error'?'bg-red-950 text-red-200 border-red-800':'bg-ink-elev text-fg border-neon/50'}`}>{t.msg}</div>)}</div> }
export const Spinner = ()=><span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" aria-label="Working"/>
