import React, { useEffect, useMemo, useState } from 'react'
import { LayoutDashboard, Compass, Wand2, UserCircle, FileText, Mic, KanbanSquare, LineChart, Settings, Sun, Moon, Monitor, Search, Plus, Sparkles, Trash2, Download, Upload, ExternalLink, CheckCircle2, AlertTriangle, XCircle, ListFilter, CalendarDays, Table2, Columns3, ShieldCheck, Cpu, Database, RefreshCw, ChevronRight, Bot } from 'lucide-react'
import { get, post, put, del, apiUpload, download, setToken } from './lib/api'
import { useTheme } from './lib/theme'
import { Card, Btn, Input, Textarea, Select, Label, Badge, Empty, Skeleton, ScoreRing, Confirm, Toasts, Spinner } from './components/ui'

type Page = 'onboarding'|'dashboard'|'discover'|'studio'|'profile'|'documents'|'interview'|'tracker'|'insights'|'settings'
const NAV:{id:Page;label:string;icon:any}[] = [
 {id:'dashboard',label:'Dashboard',icon:LayoutDashboard},{id:'discover',label:'Discover Jobs',icon:Compass},
 {id:'studio',label:'Application Studio',icon:Wand2},{id:'profile',label:'Career Profile',icon:UserCircle},
 {id:'documents',label:'Documents',icon:FileText},{id:'interview',label:'Interview Coach',icon:Mic},
 {id:'tracker',label:'Application Tracker',icon:KanbanSquare},{id:'insights',label:'Career Insights',icon:LineChart},
 {id:'settings',label:'Settings',icon:Settings}]
let tid=0
export default function App(){
  const {pref,dark,setPref}=useTheme()
  const [page,setPage]=useState<Page>('dashboard')
  const [health,setHealth]=useState<any>(null); const [offline,setOffline]=useState(false)
  const [profile,setProfile]=useState<any>(null); const [jobSel,setJobSel]=useState<any>(null)
  const [toasts,setToasts]=useState<any[]>([]); const [search,setSearch]=useState('')
  const toast=(msg:string,kind='ok')=>{ const id=++tid; setToasts(t=>[...t,{id,msg,kind}]); setTimeout(()=>setToasts(t=>t.filter(x=>x.id!==id)),4200) }
  const err=(e:any)=>toast(e?.message||String(e),'error')
  async function loadProfile(){ try{ const p=await get('/api/v1/profile'); setProfile(p); if(!p.profile.onboarding_complete && !p.profile.full_name) setPage('onboarding') }catch{ setOffline(true) } }
  useEffect(()=>{ get('/api/v1/health').then(h=>{setHealth(h);setOffline(false)}).catch(()=>setOffline(true)); loadProfile() },[])
  const ctx={profile,setProfile,toast,err,go:(p:Page)=>setPage(p),jobSel,setJobSel,reloadProfile:loadProfile,health}
  const completeness=profile?.completeness?.percent??0
  return <div className="min-h-screen bg-mist-bg text-dk dark:bg-ink-bg dark:text-fg lg:flex">
    <a href="#main" className="sr-only focus:not-sr-only focus:absolute focus:z-50 focus:bg-neon focus:text-black focus:px-3 focus:py-2">Skip to content</a>
    <aside className="lg:w-64 lg:min-h-screen lg:sticky lg:top-0 border-b lg:border-r border-mist-line dark:border-ink-line bg-mist-side dark:bg-ink-side p-4" aria-label="Primary">
      <div className="flex items-center gap-2 px-1">
        <div className="h-9 w-9 rounded-xl bg-neon grid place-items-center text-black font-black shadow-glow" aria-hidden>CP</div>
        <div><div className="font-bold leading-tight">CareerPilot <span className="text-pgreen dark:text-neon">AI</span></div>
        <div className="text-[11px] text-dsub dark:text-sub">Your Career. Your Strategy.</div></div>
      </div>
      <nav className="mt-5 flex lg:flex-col gap-1 overflow-x-auto pb-1">
        {NAV.map(n=>{ const Icon=n.icon; const active=page===n.id; return <button key={n.id} onClick={()=>setPage(n.id)} aria-current={active?'page':undefined}
          className={`flex items-center gap-2.5 rounded-xl px-3 py-2.5 text-sm whitespace-nowrap transition ${active?'bg-mist-alt dark:bg-ink-alt text-pgreen dark:text-neon font-semibold border border-green-500/40 dark:border-neon/40':'text-dsub dark:text-sub hover:bg-mist-alt dark:hover:bg-ink-alt'}`}><Icon size={17}/>{n.label}</button> })}
      </nav>
      <div className="hidden lg:block mt-6 rounded-2xl border border-mist-line dark:border-ink-line p-3">
        <div className="text-xs font-medium">Career profile</div>
        <div className="text-sm font-semibold mt-0.5">{profile?.profile?.full_name||'Not set up yet'}</div>
        <div className="mt-2 h-2 rounded-full bg-mist-alt dark:bg-ink-elev overflow-hidden" role="progressbar" aria-valuenow={completeness} aria-label="Profile completeness"><div className="h-full bg-neon transition-all" style={{width:`${completeness}%`}}/></div>
        <div className="text-[11px] text-dsub dark:text-sub mt-1">{completeness}% complete</div>
        <button className="text-xs mt-2 text-pgreen dark:text-neon hover:underline" onClick={()=>setPage('onboarding')}>{profile?.profile?.onboarding_complete?'Review onboarding':'Continue onboarding'} →</button>
      </div>
      <div className="hidden lg:flex items-center gap-2 mt-4 text-xs text-dsub dark:text-sub px-1">
        <span className={`h-2 w-2 rounded-full ${offline?'bg-red-500':'bg-neon'}`} aria-hidden/>
        {offline?'Local backend offline':`Local backend · AI: ${health?.ai_provider||'none'}${health?.ai_model?` (${health.ai_model})`:''}`}
      </div>
    </aside>
    <div className="flex-1 min-w-0">
      <header className="sticky top-0 z-30 flex items-center gap-3 px-4 sm:px-6 py-3 border-b border-mist-line dark:border-ink-line bg-mist-bg/90 dark:bg-ink-bg/90 backdrop-blur">
        <div className="relative flex-1 max-w-md"><Search size={16} className="absolute left-3 top-2.5 text-mute"/><Input aria-label="Global search (jobs)" placeholder="Search jobs, companies…" className="pl-9" value={search} onChange={(e:any)=>setSearch(e.target.value)} onKeyDown={(e:any)=>{ if(e.key==='Enter') setPage('discover') }}/></div>
        <span className="hidden md:inline-flex"><Badge tone={health?.ai_provider&&health.ai_provider!=='none'?'green':'neutral'}><Bot size={13}/> {health?.ai_provider==='ollama'?'Local AI':health?.ai_provider&&health.ai_provider!=='none'?'Cloud AI':'No AI (built-in mode)'}</Badge></span>
        <Btn onClick={()=>setPage('discover')}><Plus size={15}/> Analyze a Job</Btn>
        <div className="flex rounded-xl border border-mist-line dark:border-ink-line overflow-hidden" role="group" aria-label="Theme">
          {([['light',Sun],['dark',Moon],['system',Monitor]] as const).map(([t,Icon]:any)=><button key={t} title={`${t} theme`} aria-pressed={pref===t} onClick={()=>setPref(t)} className={`p-2 ${pref===t?'bg-neon text-black':'hover:bg-mist-alt dark:hover:bg-ink-alt'}`}><Icon size={15}/></button>)}
        </div>
      </header>
      {offline && <div className="m-4 rounded-xl border border-red-400/50 bg-red-50 dark:bg-red-950/40 p-4 text-sm flex flex-wrap gap-3 items-center" role="alert">
        <AlertTriangle size={17}/> <span>Cannot reach the local backend. Start it with <code className="font-mono">cd backend &amp;&amp; python run.py</code>, then add your local API token (printed in the app data folder as <code className="font-mono">.api_token</code>) if requested.</span>
        <TokenBox onDone={()=>{setOffline(false); loadProfile(); get('/api/v1/health').then(setHealth).catch(()=>setOffline(true))}}/>
      </div>}
      <main id="main" className="p-4 sm:p-6 max-w-7xl mx-auto w-full">
        {page==='onboarding'&&<Onboarding {...ctx}/>}
        {page==='dashboard'&&<Dashboard {...ctx}/>}
        {page==='discover'&&<Discover {...ctx} externalQuery={search}/>}
        {page==='studio'&&<Studio {...ctx}/>}
        {page==='profile'&&<ProfilePage {...ctx}/>}
        {page==='documents'&&<Documents {...ctx}/>}
        {page==='interview'&&<Interview {...ctx}/>}
        {page==='tracker'&&<Tracker {...ctx}/>}
        {page==='insights'&&<Insights {...ctx}/>}
        {page==='settings'&&<SettingsPage {...ctx}/>}
      </main>
      <footer className="px-6 pb-6 text-xs text-mute max-w-7xl mx-auto">CareerPilot AI runs locally. No telemetry. Nothing is sent to a cloud provider unless you configure one in Settings. It never applies to jobs on your behalf and never fabricates qualifications.</footer>
    </div>
    <Toasts items={toasts}/>
  </div>
}
function TokenBox({onDone}:any){ const [t,setT]=useState(''); return <span className="inline-flex gap-2"><Input placeholder="Local API token" value={t} onChange={(e:any)=>setT(e.target.value)} className="w-56"/><Btn onClick={()=>{setToken(t.trim()); onDone()}}>Connect</Btn></span> }

/* ---------------- Dashboard ---------------- */
function Dashboard({go,toast,err,profile,setJobSel}:any){
  const [d,setD]=useState<any>(null)
  useEffect(()=>{ get('/api/v1/dashboard').then(setD).catch(err) },[])
  if(!d) return <Skeleton/>
  const a=d.analytics||{}
  return <div className="space-y-5">
    <div><h1 className="text-2xl font-bold">{d.profile_name?`Welcome back, ${d.profile_name.split(' ')[0]}`:'Welcome to CareerPilot AI'} <span aria-hidden>🟢</span></h1>
    <p className="text-sm text-dsub dark:text-sub mt-1">Your Career. Your Strategy. Your Next Opportunity.</p></div>
    {!d.onboarding_complete && <Card className="border-green-500/50"><div className="flex flex-wrap items-center gap-3 justify-between"><div><p className="font-semibold">Finish setting up your career profile</p><p className="text-sm text-dsub dark:text-sub">Matching and document generation are only as good as your verified profile. Missing: {d.completeness?.missing?.join(', ')||'—'}</p></div><Btn onClick={()=>go('onboarding')}>Continue onboarding <ChevronRight size={15}/></Btn></div></Card>}
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {[['Profile completeness',`${d.completeness?.percent??0}%`],['Jobs discovered',a.opportunities_discovered??0],['Applications active',d.applications_in_progress??0],['Interviews',a.interviews??0]].map(([k,v]:any)=>
        <Card key={k}><div className="text-xs text-dsub dark:text-sub">{k}</div><div className="text-2xl font-bold mt-1 text-pgreen dark:text-neon">{v}</div></Card>)}
    </div>
    <div className="grid lg:grid-cols-3 gap-4">
      <Card className="lg:col-span-2"><h2 className="font-semibold mb-3">Quick actions</h2><div className="flex flex-wrap gap-2">
        {[['Find Jobs','discover'],['Analyze a Job','discover'],['Tailor My CV','studio'],['Generate a Cover Letter','studio'],['Prepare for an Interview','interview'],['Add an Application','tracker']].map(([l,p]:any)=><Btn key={l} variant="ghost" onClick={()=>go(p)}>{l}</Btn>)}
      </div>
      <h2 className="font-semibold mt-6 mb-3">Top matches</h2>
      {d.top_matches?.length? d.top_matches.map((j:any)=><button key={j.id} onClick={()=>{setJobSel(j);go('discover')}} className="w-full text-left flex items-center justify-between gap-3 rounded-xl border border-mist-line dark:border-ink-line px-3 py-2.5 mb-2 hover:bg-mist-alt dark:hover:bg-ink-alt"><span><span className="font-medium text-sm block">{j.title}</span><span className="text-xs text-dsub dark:text-sub">{j.company} · {j.location||'Location n/a'} · {j.source}</span></span><ScoreRing score={j.match?.score??0}/></button>)
      : <p className="text-sm text-dsub dark:text-sub">No jobs yet — use <button className="underline text-pgreen dark:text-neon" onClick={()=>go('discover')}>Discover Jobs</button> to search live sources or paste a job URL. We never show fictional listings.</p>}
      </Card>
      <div className="space-y-4">
        <Card><h2 className="font-semibold mb-2">Upcoming reminders</h2>{d.upcoming_reminders?.length? d.upcoming_reminders.map((r:any)=><p key={r.id} className="text-sm py-1">📅 {r.title} <span className="text-xs text-mute">({r.due_at} {r.timezone})</span></p>) : <p className="text-sm text-dsub dark:text-sub">None scheduled. Add reminders in the Tracker.</p>}</Card>
        <Card><h2 className="font-semibold mb-2">Recent activity</h2>{d.recent_tasks?.length? d.recent_tasks.map((t:any)=><p key={t.id} className="text-sm py-1 flex justify-between gap-2"><span>{t.name}</span><Badge tone={t.status==='completed'?'green':t.status==='failed'?'red':'neutral'}>{t.status}</Badge></p>) : <p className="text-sm text-dsub dark:text-sub">No background tasks yet.</p>}
        {d.recent_documents?.length>0 && <><h3 className="text-xs font-semibold mt-3 text-dsub dark:text-sub">RECENT DOCUMENTS</h3>{d.recent_documents.map((x:any)=><p key={x.id} className="text-sm py-0.5">📄 {x.title} <span className="text-xs text-mute">({x.status})</span></p>)}</>}
        </Card>
      </div>
    </div>
  </div>
}

/* ---------------- Onboarding ---------------- */
const OBJECTIVES=['Find a full-time job','Find remote work','Find internships','Find graduate opportunities','Find contract work','Find freelance clients','Change careers','Improve existing applications','Prepare for interviews','Explore several options']
const SKILL_CATS=['Programming Languages','Frontend','Backend','Mobile','AI & Machine Learning','Databases','Cloud & DevOps','Security','Blockchain','Communication','Leadership','Research','General']
function Onboarding({profile,reloadProfile,toast,err,go}:any){
  const [step,setStep]=useState(profile?.profile?.onboarding_step||0)
  const [p,setP]=useState<any>({}); const [busy,setBusy]=useState(false)
  const [exp,setExp]=useState<any>({}); const [edu,setEdu]=useState<any>({}); const [sk,setSk]=useState<any>({name:'',category:'Backend',proficiency:'Intermediate'}); const [proj,setProj]=useState<any>({}); const [cert,setCert]=useState<any>({})
  const [importRes,setImportRes]=useState<any>(null); const [approve,setApprove]=useState<any>({}); const [pickSkills,setPickSkills]=useState<string[]>([])
  useEffect(()=>{ if(profile?.profile) setP(profile.profile) },[profile])
  const steps=['Welcome','About you','Education','Experience','Skills','Projects','Certifications','Preferences','Writing style','Import CV','Review']
  async function saveProfile(extra:any={}){ const body={full_name:'',headline:'',email:'',phone:'',city:'',country:'',linkedin:'',github:'',portfolio:'',summary:'',objectives:[],show_on_cv:{},preferences:{},writing_style:{},...p,...extra,onboarding_step:step}; const r=await put('/api/v1/profile',body); setP(r); await reloadProfile() }
  async function next(){ setBusy(true); try{ await saveProfile({onboarding_step:Math.min(step+1,10)}); setStep(s=>Math.min(s+1,10)) }catch(e){err(e)} finally{setBusy(false)} }
  const upd=(k:string,v:any)=>setP((x:any)=>({...x,[k]:v}))
  const updNested=(g:string,k:string,v:any)=>setP((x:any)=>({...x,[g]:{...(x[g]||{}),[k]:v}}))
  const prefs=p.preferences||{}; const ws=p.writing_style||{}
  return <div className="max-w-3xl mx-auto space-y-5">
    <div><h1 className="text-2xl font-bold">Let's build your career profile</h1><p className="text-sm text-dsub dark:text-sub mt-1">Guided, saved automatically as you go, and fully editable later. Everything stays on this computer. Skip anything optional.</p></div>
    <div className="flex gap-1" role="progressbar" aria-valuenow={step+1} aria-valuemin={1} aria-valuemax={steps.length} aria-label="Onboarding progress">{steps.map((s,i)=><div key={s} title={s} className={`h-2 flex-1 rounded-full ${i<=step?'bg-neon':'bg-mist-alt dark:bg-ink-elev'}`}/>)}</div>
    <p className="text-xs text-dsub dark:text-sub">Step {step+1} of {steps.length} — {steps[step]}</p>
    <Card>
    {step===0 && <div className="space-y-4"><p className="text-sm">CareerPilot AI learns your verified background, finds relevant roles, scores your fit with evidence, drafts tailored documents, independently reviews them for accuracy, and tracks every application. It will <b>never invent</b> qualifications or apply without your approval.</p>
      <Label>What are you here to do? (choose any)</Label><div className="flex flex-wrap gap-2">{OBJECTIVES.map(o=>{const on=(p.objectives||[]).includes(o); return <button key={o} aria-pressed={on} onClick={()=>upd('objectives',on?(p.objectives||[]).filter((x:string)=>x!==o):[...(p.objectives||[]),o])} className={`rounded-full px-3 py-1.5 text-sm border ${on?'bg-neon text-black font-semibold border-transparent':'border-mist-line dark:border-ink-line'}`}>{o}</button>})}</div></div>}
    {step===1 && <div className="grid sm:grid-cols-2 gap-3">
      {[['full_name','Preferred / full name'],['headline','Professional headline (e.g. Backend Developer)'],['email','Email'],['phone','Phone'],['city','City'],['country','Country'],['linkedin','LinkedIn URL'],['github','GitHub URL'],['portfolio','Portfolio URL']].map(([k,l]:any)=><div key={k}><Label>{l}</Label><Input value={p[k]||''} onChange={(e:any)=>upd(k,e.target.value)}/></div>)}
      <div className="sm:col-span-2"><Label>Professional summary</Label><Textarea rows={4} value={p.summary||''} onChange={(e:any)=>upd('summary',e.target.value)} placeholder="2–4 honest sentences about your background and strengths…"/></div>
      <p className="sm:col-span-2 text-xs text-mute">Private profile data only appears on a CV when generated from these fields. Phone/address are never sent to job sources.</p></div>}
    {step===2 && <div className="space-y-3">{(profile?.education||[]).map((e:any)=><div key={e.id} className="flex justify-between items-center rounded-xl border border-mist-line dark:border-ink-line px-3 py-2 text-sm"><span>{e.qualification} — {e.institution}</span><button aria-label="Delete" onClick={async()=>{await del(`/api/v1/education/${e.id}`);reloadProfile()}}><Trash2 size={15}/></button></div>)}
      <div className="grid sm:grid-cols-2 gap-3">{[['institution','Institution'],['qualification','Qualification'],['field','Field of study'],['start_date','Start (YYYY-MM)'],['end_date','End (YYYY-MM)']].map(([k,l]:any)=><div key={k}><Label>{l}</Label><Input value={edu[k]||''} onChange={(e:any)=>setEdu({...edu,[k]:e.target.value})}/></div>)}
      <label className="text-sm flex gap-2 items-center"><input type="checkbox" checked={!!edu.current} onChange={e=>setEdu({...edu,current:e.target.checked})}/> Currently studying</label></div>
      <Label>Relevant coursework / achievements</Label><Textarea value={edu.achievements||''} onChange={(e:any)=>setEdu({...edu,achievements:e.target.value})}/>
      <Btn variant="ghost" onClick={async()=>{ if(!edu.institution||!edu.qualification) return toast('Add institution and qualification','error'); await post('/api/v1/education',{institution:'',qualification:'',...edu}); setEdu({}); reloadProfile(); toast('Education added') }}><Plus size={15}/> Add education</Btn></div>}
    {step===3 && <div className="space-y-3">{(profile?.experience||[]).map((e:any)=><div key={e.id} className="flex justify-between items-center rounded-xl border border-mist-line dark:border-ink-line px-3 py-2 text-sm"><span>{e.title} @ {e.organization}</span><button aria-label="Delete" onClick={async()=>{await del(`/api/v1/experience/${e.id}`);reloadProfile()}}><Trash2 size={15}/></button></div>)}
      <div className="grid sm:grid-cols-2 gap-3">{[['organization','Organization'],['title','Job title'],['employment_type','Type (Full-time, Contract…)'],['start_date','Start (YYYY-MM)'],['end_date','End (YYYY-MM)'],['location','Location']].map(([k,l]:any)=><div key={k}><Label>{l}</Label><Input value={exp[k]||''} onChange={(e:any)=>setExp({...exp,[k]:e.target.value})}/></div>)}
      <label className="text-sm flex gap-2 items-center"><input type="checkbox" checked={!!exp.current} onChange={e=>setExp({...exp,current:e.target.checked})}/> I currently work here</label></div>
      <Label>Describe it conversationally — responsibilities &amp; what you actually did</Label><Textarea rows={3} value={exp.description||''} onChange={(e:any)=>setExp({...exp,description:e.target.value})} placeholder="Be specific and truthful. If you have real metrics, include them; never guess numbers."/>
      <Label>Achievements (one per line, only real ones)</Label><Textarea rows={2} value={(exp.achievements||[]).join('\n')} onChange={(e:any)=>setExp({...exp,achievements:e.target.value.split('\n').filter(Boolean)})}/>
      <Label>Tools / technologies (comma-separated)</Label><Input value={(exp.tools||[]).join(', ')} onChange={(e:any)=>setExp({...exp,tools:e.target.value.split(',').map((s:string)=>s.trim()).filter(Boolean)})}/>
      <Btn variant="ghost" onClick={async()=>{ if(!exp.organization||!exp.title) return toast('Add organization and title','error'); await post('/api/v1/experience',{organization:'',title:'',employment_type:'Full-time',achievements:[],tools:[],...exp}); setExp({}); reloadProfile(); toast('Experience added') }}><Plus size={15}/> Add experience</Btn></div>}
    {step===4 && <div className="space-y-3"><div className="flex flex-wrap gap-2">{(profile?.skills||[]).map((s:any)=><Badge key={s.id} tone={s.verification_status==='user_confirmed'?'green':'amber'}>{s.name} · {s.proficiency}{s.verification_status!=='user_confirmed'?' (unverified)':''} <button aria-label={`Remove ${s.name}`} onClick={async()=>{await del(`/api/v1/skills/${s.id}`);reloadProfile()}}>×</button></Badge>)}</div>
      <div className="grid sm:grid-cols-3 gap-3"><div><Label>Skill</Label><Input value={sk.name} onChange={(e:any)=>setSk({...sk,name:e.target.value})} placeholder="e.g. Python"/></div>
      <div><Label>Category</Label><Select value={sk.category} onChange={(e:any)=>setSk({...sk,category:e.target.value})}>{SKILL_CATS.map(c=><option key={c}>{c}</option>)}</Select></div>
      <div><Label>Proficiency (be honest)</Label><Select value={sk.proficiency} onChange={(e:any)=>setSk({...sk,proficiency:e.target.value})}>{['Beginner','Intermediate','Advanced','Expert'].map(c=><option key={c}>{c}</option>)}</Select></div>
      <div><Label>Years (optional)</Label><Input type="number" step="0.5" value={sk.years||''} onChange={(e:any)=>setSk({...sk,years:parseFloat(e.target.value)||null})}/></div>
      <div className="sm:col-span-2"><Label>Evidence (project/cert that proves it)</Label><Input value={sk.evidence||''} onChange={(e:any)=>setSk({...sk,evidence:e.target.value})}/></div></div>
      <Btn variant="ghost" onClick={async()=>{ if(!sk.name.trim()) return toast('Type a skill name','error'); await post('/api/v1/skills',sk); setSk({name:'',category:sk.category,proficiency:'Intermediate'}); reloadProfile() }}><Plus size={15}/> Add skill</Btn>
      <p className="text-xs text-mute">Skills you add here are marked user-confirmed. Imported skills stay “unverified” until you confirm them —matching treats them differently.</p></div>}
    {step===5 && <div className="space-y-3">{(profile?.projects||[]).map((e:any)=><div key={e.id} className="flex justify-between items-center rounded-xl border border-mist-line dark:border-ink-line px-3 py-2 text-sm"><span>{e.name}</span><button aria-label="Delete" onClick={async()=>{await del(`/api/v1/projects/${e.id}`);reloadProfile()}}><Trash2 size={15}/></button></div>)}
      <div className="grid sm:grid-cols-2 gap-3"><div><Label>Project name</Label><Input value={proj.name||''} onChange={(e:any)=>setProj({...proj,name:e.target.value})}/></div>
      <div><Label>Technologies (comma-separated)</Label><Input value={(proj.technologies||[]).join(', ')} onChange={(e:any)=>setProj({...proj,technologies:e.target.value.split(',').map((s:string)=>s.trim()).filter(Boolean)})}/></div>
      <div><Label>Repo URL</Label><Input value={proj.repo_url||''} onChange={(e:any)=>setProj({...proj,repo_url:e.target.value})}/></div>
      <div><Label>Live demo URL</Label><Input value={proj.demo_url||''} onChange={(e:any)=>setProj({...proj,demo_url:e.target.value})}/></div></div>
      <Label>Problem solved &amp; description</Label><Textarea rows={3} value={proj.description||''} onChange={(e:any)=>setProj({...proj,description:e.target.value})}/>
      <Label>Your responsibilities &amp; real outcomes</Label><Textarea rows={2} value={proj.outcomes||''} onChange={(e:any)=>setProj({...proj,outcomes:e.target.value})}/>
      <label className="text-sm flex gap-2 items-center"><input type="checkbox" checked={proj.is_public!==false} onChange={e=>setProj({...proj,is_public:e.target.checked})}/> Public project</label>
      <Btn variant="ghost" onClick={async()=>{ if(!proj.name) return toast('Add a project name','error'); await post('/api/v1/projects',{name:'',technologies:[],...proj}); setProj({}); reloadProfile(); toast('Project added') }}><Plus size={15}/> Add project</Btn></div>}
    {step===6 && <div className="space-y-3">{(profile?.certifications||[]).map((e:any)=><div key={e.id} className="flex justify-between items-center rounded-xl border border-mist-line dark:border-ink-line px-3 py-2 text-sm"><span>{e.name} — {e.issuer}</span><button aria-label="Delete" onClick={async()=>{await del(`/api/v1/certifications/${e.id}`);reloadProfile()}}><Trash2 size={15}/></button></div>)}
      <div className="grid sm:grid-cols-2 gap-3">{[['name','Certification / award name'],['issuer','Issuing organization'],['issue_date','Issue date'],['expiry_date','Expiry (optional)'],['credential_url','Credential URL'],['credential_id','Credential ID (optional)']].map(([k,l]:any)=><div key={k}><Label>{l}</Label><Input value={cert[k]||''} onChange={(e:any)=>setCert({...cert,[k]:e.target.value})}/></div>)}</div>
      <Btn variant="ghost" onClick={async()=>{ if(!cert.name) return toast('Add a name','error'); await post('/api/v1/certifications',{name:'',...cert}); setCert({}); reloadProfile(); toast('Added') }}><Plus size={15}/> Add</Btn></div>}
    {step===7 && <div className="grid sm:grid-cols-2 gap-3">
      {[['desired_titles','Desired job titles (comma-separated)','text'],['industries','Target industries','text'],['countries','Preferred countries','text'],['salary_currency','Currency (USD, NGN…)','text']].map(([k,l]:any)=><div key={k}><Label>{l}</Label><Input value={Array.isArray(prefs[k])?prefs[k].join(', '):prefs[k]||''} onChange={(e:any)=>updNested('preferences',k,e.target.value)}/></div>)}
      <div><Label>Workplace preference</Label><Select value={prefs.workplace||''} onChange={(e:any)=>updNested('preferences','workplace',e.target.value)}><option value="">Any</option><option>Remote</option><option>Hybrid</option><option>Onsite</option></Select></div>
      <div><Label>Experience level</Label><Select value={prefs.level||''} onChange={(e:any)=>updNested('preferences','level',e.target.value)}><option value="">Any</option>{['Internship','Entry','Mid-level','Senior','Lead'].map(x=><option key={x}>{x}</option>)}</Select></div>
      <div><Label>Minimum acceptable salary (optional)</Label><Input type="number" value={prefs.salary_min||''} onChange={(e:any)=>updNested('preferences','salary_min',parseFloat(e.target.value)||null)}/></div>
      <div><Label>Max daily recommendations</Label><Input type="number" value={prefs.max_daily||10} onChange={(e:any)=>updNested('preferences','max_daily',parseInt(e.target.value)||10)}/></div>
      <div><Label>Technologies / industries to avoid</Label><Input value={(prefs.avoid||[]).join(', ')} onChange={(e:any)=>updNested('preferences','avoid',e.target.value.split(',').map((s:string)=>s.trim()).filter(Boolean))}/></div>
      <label className="text-sm flex gap-2 items-center"><input type="checkbox" checked={!!prefs.relocation} onChange={e=>updNested('preferences','relocation',e.target.checked)}/> Willing to relocate</label></div>}
    {step===8 && <div className="space-y-4">
      {[['tone','Tone',['Formal','Conversational']],['length','Detail',['Concise','Balanced','Detailed']],['confidence','Confidence',['Confident','Understated']],['technical','Language',['Technical','Accessible']],['first_person','Voice',['First person (I built…)','Implied (Built…)']]].map(([k,l,opts]:any)=>
      <div key={k}><Label>{l}</Label><div className="flex gap-2 flex-wrap">{opts.map((o:string)=><button key={o} aria-pressed={ws[k]===o} onClick={()=>updNested('writing_style',k,o)} className={`rounded-full px-3 py-1.5 text-sm border ${ws[k]===o?'bg-neon text-black font-semibold border-transparent':'border-mist-line dark:border-ink-line'}`}>{o}</button>)}</div></div>)}
      <div><Label>Which sounds most like you?</Label><div className="space-y-2">{['I build reliable backend systems and care about clean, tested code.','Results-focused engineer: I ship, measure, and iterate.','Quietly thorough — I let well-documented work speak for itself.'].map(s=><button key={s} aria-pressed={ws.example===s} onClick={()=>updNested('writing_style','example',s)} className={`block w-full text-left rounded-xl border px-3 py-2 text-sm ${ws.example===s?'border-neon bg-mist-alt dark:bg-ink-alt':'border-mist-line dark:border-ink-line'}`}>{s}</button>)}</div></div>
      <div><Label>Words/phrases you dislike</Label><Input value={ws.disliked||''} onChange={(e:any)=>updNested('writing_style','disliked',e.target.value)}/></div>
      <div><Label>Optional: paste a writing sample you have permission to use (style only)</Label><Textarea rows={3} value={ws.sample||''} onChange={(e:any)=>updNested('writing_style','sample',e.target.value.slice(0,2000))}/></div>
      <p className="text-xs text-mute">We approximate your style; AI text won't be a perfect clone — always review before sending.</p></div>}
    {step===9 && <div className="space-y-3"><p className="text-sm">Import a PDF, DOCX or TXT CV. We extract suggestions only — <b>nothing is saved until you approve it</b>, and imported skills are marked unverified.</p>
      <input type="file" accept=".pdf,.docx,.txt" aria-label="Upload CV" onChange={async(e:any)=>{ const f=e.target.files?.[0]; if(!f) return; try{ const r=await apiUpload('/api/v1/profile/import-cv',f); setImportRes(r); const a:any={}; Object.entries(r.suggested).forEach(([k,v]:any)=>{ if(v.value) a[k]=v.value }); setApprove(a); setPickSkills(r.skills_detected||[]) }catch(e){err(e)} }}/>
      {importRes && <div className="space-y-3"><p className="text-xs text-mute">{importRes.note}</p>
      {Object.entries(importRes.suggested).map(([k,v]:any)=><div key={k}><Label>{k}{v.uncertain?' (uncertain — please verify)':''}</Label><Input value={approve[k]||''} onChange={(e:any)=>setApprove({...approve,[k]:e.target.value})}/></div>)}
      <Label>Detected skills (unselect any that aren't truly yours)</Label><div className="flex flex-wrap gap-2">{(importRes.skills_detected||[]).map((s:string)=><button key={s} aria-pressed={pickSkills.includes(s)} onClick={()=>setPickSkills(pickSkills.includes(s)?pickSkills.filter(x=>x!==s):[...pickSkills,s])} className={`rounded-full px-3 py-1 text-xs border ${pickSkills.includes(s)?'bg-neon text-black font-semibold':'border-mist-line dark:border-ink-line'}`}>{s}</button>)}</div>
      <Btn onClick={async()=>{ await post('/api/v1/profile/approve-import',{fields:approve,skills:pickSkills}); reloadProfile(); toast('Approved details saved (skills marked unverified)') }}>Approve &amp; save these details</Btn></div>}</div>}
    {step===10 && <div className="space-y-3">{profile?.completeness && <div><div className="h-3 rounded-full bg-mist-alt dark:bg-ink-elev overflow-hidden"><div className="h-full bg-neon" style={{width:`${profile.completeness.percent}%`}}/></div>
      <p className="text-sm mt-2">{profile.completeness.percent}% complete. {profile.completeness.missing.length?`Still missing (optional but helpful): ${profile.completeness.missing.join(', ')}.`:'All core sections complete.'} You can finish now and add more anytime from Career Profile.</p></div>}
      <div className="text-sm space-y-1"><p><b>{p.full_name||'—'}</b> · {p.headline||'—'}</p><p>{(profile?.experience||[]).length} experience · {(profile?.education||[]).length} education · {(profile?.skills||[]).length} skills · {(profile?.projects||[]).length} projects · {(profile?.certifications||[]).length} certifications</p></div>
      <Btn onClick={async()=>{ await saveProfile({onboarding_complete:true,onboarding_step:10}); toast('Welcome aboard 🎉 Profile saved locally'); go('dashboard') }}>Complete onboarding</Btn></div>}
    </Card>
    <div className="flex justify-between">
      <Btn variant="ghost" disabled={step===0} onClick={()=>setStep(s=>Math.max(s-1,0))}>Back</Btn>
      <div className="flex gap-2"><Btn variant="ghost" onClick={async()=>{await saveProfile(); go('dashboard'); toast('Progress saved — resume anytime')}}>Save &amp; exit</Btn>
      {step<10 && <Btn onClick={next} disabled={busy}>{busy?<Spinner/>:null} Continue</Btn>}</div>
    </div>
  </div>
}

/* ---------------- Discover + Job Details ---------------- */
function MatchReport({m}:any){
  if(!m||!m.job_skills) return <p className="text-sm text-dsub dark:text-sub">Not analyzed yet.</p>
  const List=({t,items,tone,icon}:any)=>items?.length?<div><p className="text-xs font-semibold mt-3 flex items-center gap-1">{icon}{t}</p>{items.map((x:any,i:number)=><p key={i} className="text-sm py-0.5"><Badge tone={tone}>{x.skill||x.item||x}</Badge> <span className="text-dsub dark:text-sub">{x.evidence||x.detail||''}</span></p>)}</div>:null
  return <div className="text-sm">
    <div className="flex items-center gap-4"><ScoreRing score={m.score}/><div><Badge tone={m.score>=70?'green':m.score>=50?'green':m.score>=30?'amber':'red'}>{m.category}</Badge><p className="text-xs text-dsub dark:text-sub mt-1 max-w-lg">{m.rationale}</p><p className="text-[11px] text-mute">Method: {m.method} · Breakdown: {Object.entries(m.breakdown||{}).map(([k,v]:any)=>`${k.replace(/_/g,' ')} ${v}`).join(' · ')}</p></div></div>
    <List t="Strong matches (confirmed in profile)" items={m.strong_matches} tone="green" icon={<CheckCircle2 size={13}/>}/>
    <List t="Partial matches (in profile, unverified)" items={m.partial_matches} tone="amber" icon={<AlertTriangle size={13}/>}/>
    <List t="Not in profile (unknown — may be missing data, not missing ability)" items={m.missing} tone="red" icon={<XCircle size={13}/>}/>
    {m.potential_disqualifiers?.length>0 && <><p className="text-xs font-semibold mt-3">Potential disqualifiers</p>{m.potential_disqualifiers.map((x:string,i:number)=><p key={i}>⚠️ {x}</p>)}</>}
    {m.suggestions?.length>0 && <><p className="text-xs font-semibold mt-3">Truthful ways to address gaps</p>{m.suggestions.map((x:string,i:number)=><p key={i}>• {x}</p>)}</>}
  </div>
}
function Discover({toast,err,go,jobSel,setJobSel,externalQuery}:any){
  const [jobs,setJobs]=useState<any[]>([]); const [loading,setLoading]=useState(true)
  const [q,setQ]=useState(externalQuery||''); const [source,setSource]=useState('Remotive'); const [board,setBoard]=useState('')
  const [fSource,setFSource]=useState(''); const [minScore,setMinScore]=useState(0); const [workplace,setWorkplace]=useState('')
  const [manual,setManual]=useState<any>({title:'',company:'',description:'',url:''}); const [url,setUrl]=useState(''); const [busy,setBusy]=useState('')
  const [confirmDel,setConfirmDel]=useState<any>(null); const [searchName,setSearchName]=useState('')
  const selected = jobs.find(j=>j.id===jobSel?.id)||jobSel
  async function load(){ setLoading(true); try{ setJobs(await get(`/api/v1/jobs?q=${encodeURIComponent(q)}&source=${encodeURIComponent(fSource)}&min_score=${minScore}&workplace=${encodeURIComponent(workplace)}`)) }catch(e){err(e)} finally{setLoading(false)} }
  useEffect(()=>{ load() },[fSource,minScore,workplace])
  async function runSearch(){ setBusy('search'); try{ const r=await post('/api/v1/jobs/search',{query:q,source,board}); toast(`Found ${r.jobs.length} new job(s) from ${source} (${r.duplicates_skipped} duplicates skipped)`); load() }catch(e){err(e)} finally{setBusy('')} }
  async function importUrl(){ setBusy('url'); try{ const d=await post('/api/v1/jobs/import-url',{url}); setManual({title:d.title||'',company:d.company||'',description:d.description||'',url:d.url||url,skills:d.skills||[]}); toast('Page extracted — review & correct the fields, then save') }catch(e){err(e)} finally{setBusy('')} }
  return <div className="space-y-5">
    <div><h1 className="text-2xl font-bold">Discover Jobs</h1><p className="text-sm text-dsub dark:text-sub mt-1">Live public sources, URL import, or manual entry. Listings are marked unverified until checked — always confirm a role is open on the employer's site.</p></div>
    <Card><h2 className="font-semibold flex items-center gap-2"><Sparkles size={16}/> Search live sources</h2>
      <div className="grid sm:grid-cols-4 gap-3 mt-3">
        <div className="sm:col-span-2"><Label>Keywords / title</Label><Input value={q} onChange={(e:any)=>setQ(e.target.value)} placeholder="e.g. Python developer"/></div>
        <div><Label>Source (public APIs, no key)</Label><Select value={source} onChange={(e:any)=>setSource(e.target.value)} className="w-full"><option>Remotive</option><option>Greenhouse</option><option>Lever</option></Select></div>
        <div><Label>Company board/slug (Greenhouse/Lever)</Label><Input value={board} onChange={(e:any)=>setBoard(e.target.value)} placeholder="e.g. stripe"/></div>
      </div>
      <div className="flex flex-wrap gap-2 mt-3"><Btn onClick={runSearch} disabled={!!busy}>{busy==='search'?<Spinner/>:<Search size={15}/>} Search &amp; save new jobs</Btn>
      <span className="inline-flex gap-2 items-center"><Input placeholder="Saved search name" value={searchName} onChange={(e:any)=>setSearchName(e.target.value)} className="w-44"/><Btn variant="ghost" onClick={async()=>{ if(!searchName) return toast('Name the search first','error'); await post('/api/v1/saved-searches',{name:searchName,filters:{q,source,board},schedule:{frequency:'manual',note:'Scheduled runs need the app open — configure in Settings'}}); toast('Search saved') }}>Save search</Btn></span></div>
      <p className="text-xs text-mute mt-2">Remotive searches remote jobs globally. Greenhouse/Lever fetch one company's public board (find the slug in their careers URL). Sources that need paid keys are not faked — see Settings → Job sources.</p>
    </Card>
    <div className="grid lg:grid-cols-2 gap-4">
      <Card><h2 className="font-semibold">Analyze a Job (paste URL)</h2>
        <div className="flex gap-2 mt-3"><Input value={url} onChange={(e:any)=>setUrl(e.target.value)} placeholder="https://company.com/jobs/…" aria-label="Job URL"/><Btn onClick={importUrl} disabled={!url||!!busy}>{busy==='url'?<Spinner/>:null} Fetch</Btn></div>
        <p className="text-xs text-mute mt-2">Protected by SSRF checks (public http/https only, no local/private addresses). If a site blocks fetching, paste the description below instead.</p>
        <h3 className="font-semibold mt-5">…or enter it manually</h3>
        <div className="grid grid-cols-2 gap-3 mt-2"><div><Label>Title *</Label><Input value={manual.title} onChange={(e:any)=>setManual({...manual,title:e.target.value})}/></div>
        <div><Label>Company *</Label><Input value={manual.company} onChange={(e:any)=>setManual({...manual,company:e.target.value})}/></div>
        <div><Label>Location</Label><Input value={manual.location||''} onChange={(e:any)=>setManual({...manual,location:e.target.value})}/></div>
        <div><Label>Workplace</Label><Select value={manual.workplace_type||''} onChange={(e:any)=>setManual({...manual,workplace_type:e.target.value})} className="w-full"><option value="">Unspecified</option><option>Remote</option><option>Hybrid</option><option>Onsite</option></Select></div></div>
        <Label>Job description</Label><Textarea rows={6} value={manual.description} onChange={(e:any)=>setManual({...manual,description:e.target.value})} placeholder="Paste the full job description…"/>
        <Btn className="mt-3" onClick={async()=>{ if(!manual.title||!manual.company) return toast('Title and company are required','error'); try{ const j=await post('/api/v1/jobs',{location:'',source:manual.url?'URL Import':'Manual',...manual}); toast(j.was_duplicate?'Already saved (duplicate detected)':'Job saved & analyzed'); setJobSel(j); load() }catch(e){err(e)} }}>Save &amp; analyze</Btn>
      </Card>
      <Card><h2 className="font-semibold flex items-center gap-2"><ListFilter size={16}/> Filters</h2>
        <div className="grid grid-cols-3 gap-3 mt-3"><div><Label>Saved source</Label><Select value={fSource} onChange={(e:any)=>setFSource(e.target.value)} className="w-full"><option value="">All</option>{['Remotive','Greenhouse','Lever','Manual','URL Import'].map(s=><option key={s}>{s}</option>)}</Select></div>
        <div><Label>Workplace</Label><Select value={workplace} onChange={(e:any)=>setWorkplace(e.target.value)} className="w-full"><option value="">Any</option><option>Remote</option><option>Hybrid</option><option>Onsite</option></Select></div>
        <div><Label>Min. match: {minScore}%</Label><Input type="range" min="0" max="90" step="10" value={minScore} onChange={(e:any)=>setMinScore(parseInt(e.target.value))}/></div></div>
        <Btn variant="ghost" onClick={load}><RefreshCw size={14}/> Apply text search</Btn>
        <p className="text-xs text-mute mt-2">Jobs below a threshold are filtered from view only — never auto-rejected or deleted.</p>
      </Card>
    </div>
    {loading? <Skeleton/> : jobs.length===0? <Empty title="No jobs saved yet" text="Search a live source above, paste a job URL, or add one manually. Your first analyzed job will appear here with an explainable match score."/>
    : <div className="grid lg:grid-cols-2 gap-4"><div className="space-y-3 max-h-[900px] overflow-auto pr-1">
      {jobs.map(j=><button key={j.id} onClick={()=>setJobSel(j)} aria-pressed={selected?.id===j.id} className={`w-full text-left rounded-2xl border p-4 transition ${selected?.id===j.id?'border-neon bg-mist-alt dark:bg-ink-alt':'border-mist-line dark:border-ink-line bg-mist-surface dark:bg-ink-surface hover:bg-mist-alt dark:hover:bg-ink-alt'}`}>
        <span className="flex justify-between gap-3"><span><span className="font-semibold block">{j.title}</span><span className="text-xs text-dsub dark:text-sub">{j.company} · {j.location||'n/a'} · {j.source} · {j.status}</span><span className="flex flex-wrap gap-1 mt-2">{(j.skills||[]).slice(0,6).map((s:string)=><Badge key={s}>{s}</Badge>)}</span></span><ScoreRing score={j.match?.score??0}/></span></button>)}
      </div>
      <div>{selected? <Card className="sticky top-20"><h2 className="text-lg font-bold">{selected.title}</h2><p className="text-sm text-dsub dark:text-sub">{selected.company} · {selected.location||''} {selected.workplace_type?`· ${selected.workplace_type}`:''}</p>
        <div className="flex flex-wrap gap-2 my-3">
          {selected.url && <Btn variant="ghost" onClick={()=>window.open(selected.url,'_blank','noopener')}><ExternalLink size={14}/> Original listing</Btn>}
          <Btn onClick={()=>go('studio')}><Wand2 size={15}/> Open in Application Studio</Btn>
          <Btn variant="ghost" onClick={async()=>{ const m=await post(`/api/v1/jobs/${selected.id}/analyze`); toast('Re-analyzed against current profile'); load(); setJobSel({...selected,match:m}) }}>Re-analyze</Btn>
          <Btn variant="ghost" onClick={async()=>{ await post('/api/v1/applications',{job_id:selected.id,status:'Saved'}); toast('Added to Application Tracker') }}>Track application</Btn>
          <button className="text-red-500 p-2" aria-label="Delete job" onClick={()=>setConfirmDel(selected)}><Trash2 size={16}/></button>
        </div>
        <h3 className="font-semibold text-sm mt-2">Suitability report</h3><MatchReport m={selected.match}/>
        <details className="mt-4"><summary className="text-sm font-medium cursor-pointer">Full job description</summary><pre className="whitespace-pre-wrap text-xs mt-2 max-h-80 overflow-auto">{selected.description}</pre></details>
      </Card> : <Empty title="Select a job" text="Choose a listing to see its details and explainable suitability report."/>}</div>
    </div>}
    <Confirm open={!!confirmDel} title="Delete this job?" text="The saved listing and its match report will be removed. Applications already created keep their company/title snapshot." onCancel={()=>setConfirmDel(null)} onConfirm={async()=>{ await del(`/api/v1/jobs/${confirmDel.id}`); setConfirmDel(null); setJobSel(null); load(); toast('Job deleted') }}/>
  </div>
}

/* ---------------- Studio ---------------- */
function Studio({toast,err,jobSel,setJobSel,go}:any){
  const [jobs,setJobs]=useState<any[]>([]); const [jobId,setJobId]=useState<number|''>(jobSel?.id||'')
  const [templates,setTemplates]=useState<any[]>([]); const [tpl,setTpl]=useState('ats'); const [len,setLen]=useState('standard'); const [rounds,setRounds]=useState(2)
  const [strategy,setStrategy]=useState<any>(null); const [pkg,setPkg]=useState<any>(null); const [busy,setBusy]=useState('')
  useEffect(()=>{ get('/api/v1/jobs').then(setJobs).catch(()=>{}); get('/api/v1/documents/templates').then(setTemplates).catch(()=>{}) },[])
  useEffect(()=>{ if(jobSel?.id) setJobId(jobSel.id) },[jobSel])
  const job=jobs.find(j=>j.id===Number(jobId))
  async function getStrategy(){ if(!jobId) return toast('Choose a job first','error'); setBusy('strategy'); try{ setStrategy(await post('/api/v1/studio/strategy',{job_id:Number(jobId)})) }catch(e){err(e)} finally{setBusy('')} }
  async function generate(){ if(!jobId) return toast('Choose a job first','error'); setBusy('gen'); try{ const r=await post('/api/v1/studio/generate',{job_id:Number(jobId),template:tpl,cover_length:len,review_rounds:rounds,strategy_override:strategy}); setPkg(r); toast('Application package drafted & independently reviewed') }catch(e){err(e)} finally{setBusy('')} }
  return <div className="space-y-5">
    <div><h1 className="text-2xl font-bold">Application Studio</h1><p className="text-sm text-dsub dark:text-sub mt-1">Strategy → Draft → Independent review → Revise → Your approval → Export. Documents use verified profile facts only; critical factual findings block approval.</p></div>
    <Card><div className="grid md:grid-cols-4 gap-3">
      <div className="md:col-span-2"><Label>1 · Job opportunity</Label><Select className="w-full" value={jobId} onChange={(e:any)=>{setJobId(e.target.value?Number(e.target.value):''); setStrategy(null); setPkg(null)}}><option value="">Select a saved job…</option>{jobs.map(j=><option key={j.id} value={j.id}>{j.title} @ {j.company} ({j.match?.score??0}%)</option>)}</Select></div>
      <div><Label>CV template</Label><Select className="w-full" value={tpl} onChange={(e:any)=>setTpl(e.target.value)}>{templates.map(t=><option key={t.key} value={t.key}>{t.name}</option>)}</Select><p className="text-[11px] text-mute mt-1">{templates.find(t=>t.key===tpl)?.desc}</p></div>
      <div><Label>Cover letter length</Label><Select className="w-full" value={len} onChange={(e:any)=>setLen(e.target.value)}><option value="concise">Concise</option><option value="standard">Standard</option><option value="detailed">Detailed</option></Select>
      <Label>Review rounds</Label><Input type="number" min="1" max="3" value={rounds} onChange={(e:any)=>setRounds(parseInt(e.target.value)||2)}/></div>
    </div>
    {jobs.length===0 && <p className="text-sm mt-3">No jobs yet. <button className="underline text-pgreen dark:text-neon" onClick={()=>go('discover')}>Add one in Discover Jobs →</button></p>}
    {job && <details className="mt-4" open><summary className="text-sm font-semibold cursor-pointer">2 · Suitability ({job.title})</summary><div className="mt-2"><MatchReport m={job.match}/></div></details>}
    <div className="flex flex-wrap gap-2 mt-4"><Btn variant="ghost" onClick={getStrategy} disabled={!!busy}>{busy==='strategy'?<Spinner/>:<Bot size={15}/>} 3 · Get application strategy</Btn>
    <Btn onClick={generate} disabled={!!busy}>{busy==='gen'?<Spinner/>:<Wand2 size={15}/>} 4 · Draft + review documents</Btn></div>
    {strategy && <div className="mt-4 text-sm space-y-2"><h3 className="font-semibold">Strategy <Badge>{strategy.generated_by}</Badge></h3>
      <p><b>Positioning:</b> {strategy.positioning}</p><p><b>Highlight:</b> {[...(strategy.highlight_skills||[]),...(strategy.highlight_projects||[])].join(', ')||'—'}</p>
      <p><b>Gaps:</b> {(strategy.gaps||[]).join(', ')||'none detected'}</p><p><b>Gap approach:</b> {(strategy.gap_strategy||[]).join(' ')}</p>
      <Label>Tailored summary (editable — this exact text goes on the CV)</Label><Textarea rows={3} value={strategy.tailored_summary||''} onChange={(e:any)=>setStrategy({...strategy,tailored_summary:e.target.value})}/>
      {strategy.note && <p className="text-xs text-amber-600 dark:text-yellow-300">⚠️ {strategy.note}</p>}</div>}
    </Card>
    {pkg && <div className="grid lg:grid-cols-2 gap-4">{[pkg.tailored_cv,pkg.cover_letter].filter(Boolean).map((d:any)=><DocCard key={d.id} doc={d} toast={toast} err={err} onTrack={async()=>{ const apps=await get('/api/v1/applications'); const ex=apps.find((a:any)=>a.job_id===Number(jobId)); if(ex) await put(`/api/v1/applications/${ex.id}`,{...ex,[d.kind==='tailored_cv'?'cv_document_id':'cover_letter_id']:d.id,status:'Documents in Progress'}); else await post('/api/v1/applications',{job_id:Number(jobId),status:'Documents in Progress',[d.kind==='tailored_cv'?'cv_document_id':'cover_letter_id']:d.id}); toast('Linked to Application Tracker') }}/>)}</div>}
  </div>
}
function DocCard({doc,toast,err,onTrack}:any){
  const [d,setD]=useState<any>(doc); const [text,setText]=useState(doc.plain_text); const [busy,setBusy]=useState(''); const [undo,setUndo]=useState<string[]>([])
  const review=d.review?.final; const verdictTone:any={ready_for_approval:'green',needs_user_confirmation:'amber',revision_required:'red'}
  async function refresh(){ const r=await get(`/api/v1/documents/${d.id}`); setD(r); setText(r.plain_text) }
  return <Card><div className="flex items-start justify-between gap-2"><div><h3 className="font-semibold text-sm">{d.title}</h3><p className="text-xs text-mute">{d.kind} · status: {d.status} · v{(d.versions||[]).length}</p></div>
    {review && <Badge tone={verdictTone[review.verdict]||'neutral'}>Review: {review.verdict.replace(/_/g,' ')} · {review.quality_score}/100</Badge>}</div>
    <Textarea rows={14} className="mt-3 font-mono text-xs" value={text} onChange={(e:any)=>{setUndo(u=>[...u.slice(-19),text]); setText(e.target.value)}} aria-label={`Edit ${d.title}`}/>
    <div className="flex flex-wrap gap-2 mt-3">
      <Btn variant="ghost" onClick={async()=>{ setBusy('save'); try{ await put(`/api/v1/documents/${d.id}`,{plain_text:text}); refresh(); toast('Saved new version') }catch(e){err(e)} finally{setBusy('')} }} disabled={!!busy}>{busy==='save'?<Spinner/>:null} Save version</Btn>
      <Btn variant="ghost" onClick={()=>{ const u=[...undo]; const last=u.pop(); if(last!==undefined){ setUndo(u); setText(last) } }} disabled={!undo.length}>Undo</Btn>
      <Btn variant="ghost" onClick={async()=>{ try{ await put(`/api/v1/documents/${d.id}`,{plain_text:text}); await post(`/api/v1/documents/${d.id}/review`); refresh(); toast('Independent review updated') }catch(e){err(e)} }}>Re-run review</Btn>
      <Btn variant="ghost" onClick={async()=>{ try{ const r=await post(`/api/v1/documents/${d.id}/revise`); toast('Safe fixes applied: '+(r.changes||[]).join('; ')); refresh() }catch(e){err(e)} }}>Apply safe revisions</Btn>
      <Btn onClick={async()=>{ try{ await put(`/api/v1/documents/${d.id}`,{plain_text:text,status:'approved'}); refresh(); toast('Approved by you ✓') }catch(e){err(e)} }}>Approve</Btn>
      {onTrack && <Btn variant="ghost" onClick={onTrack}>Track application</Btn>}
    </div>
    <div className="flex flex-wrap gap-2 mt-2 items-center"><span className="text-xs text-mute">Export:</span>
      {['pdf','docx','txt'].map(f=><button key={f} className="text-xs underline text-pgreen dark:text-neon" onClick={async()=>{ try{ await download(`/api/v1/documents/${d.id}/export/${f}`,`${d.title}.${f}`); refresh() }catch(e){err(e)} }}><Download size={12} className="inline"/> {f.toUpperCase()}</button>)}
      {d.kind!=='cover_letter' && <button className="text-xs underline text-pgreen dark:text-neon" onClick={()=>download(`/api/v1/documents/${d.id}/export/tex`,`${d.title}.tex`).catch(err)}>LaTeX</button>}
    </div>
    {review?.findings?.length>0 && <details className="mt-3" open><summary className="text-sm font-semibold cursor-pointer">Reviewer findings ({review.findings.length})</summary>
      {review.findings.map((f:any,i:number)=><div key={i} className="text-xs border-l-2 border-yellow-500 pl-3 py-1 mt-2"><Badge tone={f.severity==='critical'?'red':f.severity==='high'?'amber':'neutral'}>{f.severity}</Badge> <b>{f.category}</b> — “{f.location}”: {f.explanation} <span className="text-dsub dark:text-sub">Fix: {f.recommendation}{f.requires_user_confirmation?' (needs your confirmation)':''}</span></div>)}</details>}
    {review && <p className="text-xs text-mute mt-2">{review.summary} Keywords covered: {(review.keyword_coverage?.covered||[]).join(', ')||'—'}.</p>}
    {(d.versions||[]).length>1 && <details className="mt-2"><summary className="text-xs cursor-pointer">Version history</summary>{d.versions.map((v:any)=><p key={v.id} className="text-xs py-0.5">v{v.version} — {v.note} <button className="underline" onClick={async()=>{ await post(`/api/v1/documents/${d.id}/restore/${v.version}`); refresh(); toast(`Restored v${v.version}`) }}>restore</button></p>)}</details>}
  </Card>
}

/* ---------------- Profile / Documents ---------------- */
function ProfilePage({profile,reloadProfile,err,toast,go}:any){
  if(!profile) return <Skeleton/>
  const p=profile.profile
  const Sec=({title,items,render,empty}:any)=><Card><h2 className="font-semibold">{title}</h2>{items?.length? items.map(render):<p className="text-sm text-dsub dark:text-sub mt-2">{empty} <button className="underline text-pgreen dark:text-neon" onClick={()=>go('onboarding')}>Add via onboarding →</button></p>}</Card>
  const vs=(s:string)=><Badge tone={s==='user_confirmed'?'green':'amber'}>{s.replace(/_/g,' ')}</Badge>
  return <div className="space-y-4">
    <div className="flex flex-wrap items-center justify-between gap-3"><div><h1 className="text-2xl font-bold">Career Profile</h1><p className="text-sm text-dsub dark:text-sub">Your verified source of truth. Documents may only use facts recorded here.</p></div>
    <Btn onClick={()=>go('onboarding')}>Edit via guided onboarding</Btn></div>
    <Card><div className="flex flex-wrap justify-between gap-3"><div><h2 className="text-lg font-bold">{p.full_name||'No name yet'}</h2><p className="text-sm text-dsub dark:text-sub">{p.headline} {p.city?`· ${p.city}, ${p.country}`:''}</p><p className="text-sm mt-1">{p.summary}</p>
    <p className="text-xs text-mute mt-1">{[p.email,p.phone,p.linkedin,p.github,p.portfolio].filter(Boolean).join(' · ')}</p></div>
    <div className="text-center"><div className="text-2xl font-bold text-pgreen dark:text-neon">{profile.completeness.percent}%</div><div className="text-[11px] text-mute">complete</div></div></div>
    {profile.completeness.missing.length>0 && <p className="text-xs text-amber-700 dark:text-yellow-300 mt-2">Missing (improves matching): {profile.completeness.missing.join(', ')}</p>}
    <div className="flex flex-wrap gap-1.5 mt-3">{Object.entries(profile.completeness.checks).map(([k,v]:any)=><Badge key={k} tone={v?'green':'neutral'}>{v?'✓':'○'} {k}</Badge>)}</div></Card>
    <div className="grid lg:grid-cols-2 gap-4">
      <Sec title="Experience" empty="No experience recorded." items={profile.experience} render={(e:any)=><div key={e.id} className="py-2 border-b border-mist-line dark:border-ink-line last:border-0 flex justify-between gap-2"><div><p className="text-sm font-medium">{e.title} @ {e.organization}</p><p className="text-xs text-mute">{e.start_date} – {e.current?'Present':e.end_date} · {e.employment_type}</p><p className="text-xs">{e.description}</p></div><span className="flex gap-1 items-start">{vs(e.verification_status)}<button aria-label="Delete" onClick={async()=>{await del(`/api/v1/experience/${e.id}`);reloadProfile()}}><Trash2 size={14}/></button></span></div>}/>
      <Sec title="Education" empty="No education recorded." items={profile.education} render={(e:any)=><div key={e.id} className="py-2 border-b border-mist-line dark:border-ink-line last:border-0 flex justify-between gap-2"><div><p className="text-sm font-medium">{e.qualification} — {e.institution}</p><p className="text-xs text-mute">{e.field} · {e.end_date}</p></div><span className="flex gap-1 items-start">{vs(e.verification_status)}<button aria-label="Delete" onClick={async()=>{await del(`/api/v1/education/${e.id}`);reloadProfile()}}><Trash2 size={14}/></button></span></div>}/>
      <Card><h2 className="font-semibold">Skills</h2><div className="flex flex-wrap gap-1.5 mt-2">{profile.skills.length? profile.skills.map((s:any)=><span key={s.id} className="inline-flex items-center gap-1"><Badge tone={s.verification_status==='user_confirmed'?'green':'amber'}>{s.name} · {s.category} · {s.proficiency}{s.verification_status!=='user_confirmed'?' · unverified':''}</Badge>{s.verification_status!=='user_confirmed'&&<button className="text-xs underline" onClick={async()=>{ await post('/api/v1/skills',{...s,verification_status:'user_confirmed'}); reloadProfile(); toast(`${s.name} confirmed`) }}>confirm</button>}<button aria-label="Delete" onClick={async()=>{await del(`/api/v1/skills/${s.id}`);reloadProfile()}}>×</button></span>):<span className="text-sm text-dsub dark:text-sub">No skills yet.</span>}</div></Card>
      <Sec title="Projects" empty="No projects recorded." items={profile.projects} render={(e:any)=><div key={e.id} className="py-2 border-b border-mist-line dark:border-ink-line last:border-0"><p className="text-sm font-medium">{e.name} <span className="text-xs text-mute">{(e.technologies||[]).join(', ')}</span></p><p className="text-xs">{e.description} {e.outcomes}</p></div>}/>
      <Sec title="Certifications & achievements" empty="None recorded." items={[...profile.certifications,...profile.achievements]} render={(e:any)=><p key={(e.name||e.title)+e.id} className="text-sm py-1">🏅 {e.name||e.title} {e.issuer?`— ${e.issuer}`:''}</p>}/>
      <Card><h2 className="font-semibold">Preferences & writing style</h2><pre className="text-xs whitespace-pre-wrap mt-2">{JSON.stringify({preferences:p.preferences,writing_style:{...p.writing_style,sample:p.writing_style?.sample?'[sample saved]':undefined}},null,2)}</pre></Card>
    </div>
  </div>
}
function Documents({toast,err,go}:any){
  const [docs,setDocs]=useState<any[]>([]); const [templates,setTemplates]=useState<any[]>([]); const [tpl,setTpl]=useState('ats'); const [confirm,setConfirm]=useState<any>(null); const [openId,setOpenId]=useState<number|null>(null)
  async function load(){ setDocs(await get('/api/v1/documents')) }
  useEffect(()=>{ load().catch(err); get('/api/v1/documents/templates').then(setTemplates).catch(()=>{}) },[])
  const master=docs.find(d=>d.kind==='master_cv'); const rest=docs.filter(d=>d.kind!=='master_cv')
  return <div className="space-y-5">
    <div><h1 className="text-2xl font-bold">Documents Library</h1><p className="text-sm text-dsub dark:text-sub">Your Master CV lives here, separate from tailored versions — tailoring never overwrites it.</p></div>
    <Card><h2 className="font-semibold">Master CV</h2>
      <div className="flex flex-wrap gap-2 mt-3 items-center"><Select value={tpl} onChange={(e:any)=>setTpl(e.target.value)}>{templates.map(t=><option key={t.key} value={t.key}>{t.name}</option>)}</Select>
      <Btn onClick={async()=>{ await post('/api/v1/documents/master',{template:tpl}); load(); toast('Master CV rebuilt from your verified profile') }}>{master?'Rebuild from profile':'Build Master CV'}</Btn>
      <span className="text-xs text-mute">{templates.find(t=>t.key===tpl)?.desc}</span></div>
      {master? <div className="mt-3"><DocCard doc={master} toast={toast} err={err}/></div> : <p className="text-sm mt-3 text-dsub dark:text-sub">Not built yet. Complete your profile first for a fuller CV.</p>}
    </Card>
    <h2 className="font-semibold">Tailored CVs & cover letters ({rest.length})</h2>
    {rest.length===0? <Empty title="No tailored documents yet" text="Generate a job-specific CV and cover letter in the Application Studio. They'll be stored here with version history and review findings." action={<Btn onClick={()=>go('studio')}>Open Application Studio</Btn>}/>
    : rest.map(d=><Card key={d.id}><div className="flex flex-wrap justify-between gap-2 items-center"><div><p className="font-medium text-sm">{d.title}</p><p className="text-xs text-mute">{d.kind} · {d.status} · template: {d.template} · updated {String(d.updated_at||'').slice(0,10)}</p></div>
      <div className="flex gap-2"><Btn variant="ghost" onClick={()=>setOpenId(openId===d.id?null:d.id)}>{openId===d.id?'Close':'Open editor'}</Btn>
      <button className="text-red-500 p-2" aria-label="Delete document" onClick={()=>setConfirm(d)}><Trash2 size={16}/></button></div></div>
      {openId===d.id && <div className="mt-3"><DocCard doc={d} toast={toast} err={err}/></div>}</Card>)}
    <Confirm open={!!confirm} title="Delete document?" text={`“${confirm?.title}” and all its versions will be permanently deleted.`} onCancel={()=>setConfirm(null)} onConfirm={async()=>{ await del(`/api/v1/documents/${confirm.id}`); setConfirm(null); load(); toast('Deleted') }}/>
  </div>
}

/* ---------------- Interview ---------------- */
function Interview({toast,err,jobSel}:any){
  const [jobs,setJobs]=useState<any[]>([]); const [jobId,setJobId]=useState<any>(jobSel?.id||'')
  const [sessions,setSessions]=useState<any[]>([]); const [active,setActive]=useState<any>(null); const [qi,setQi]=useState(0); const [answer,setAnswer]=useState('')
  async function load(){ setSessions(await get('/api/v1/interview/sessions')) }
  useEffect(()=>{ get('/api/v1/jobs').then(setJobs).catch(()=>{}); load().catch(()=>{}) },[])
  const q=active?.questions?.[qi]; const myAnswer=active?.answers?.find((a:any)=>a.question_index===qi)
  return <div className="space-y-5">
    <div><h1 className="text-2xl font-bold">Interview Coach</h1><p className="text-sm text-dsub dark:text-sub">Job-specific questions from the real description + your profile. Feedback checks structure and evidence — never invent stories; if you lack an example, explain your approach instead.</p></div>
    <Card><div className="flex flex-wrap gap-3 items-end"><div className="flex-1 min-w-56"><Label>Practice for</Label><Select className="w-full" value={jobId} onChange={(e:any)=>setJobId(e.target.value)}><option value="">General practice (no specific job)</option>{jobs.map(j=><option key={j.id} value={j.id}>{j.title} @ {j.company}</option>)}</Select></div>
    <Btn onClick={async()=>{ const s=await post('/api/v1/interview/sessions',{job_id:jobId?Number(jobId):null}); setActive(s); setQi(0); setAnswer(''); load(); toast('Mock interview ready') }}><Mic size={15}/> Start mock interview</Btn></div>
    <p className="text-xs text-mute mt-2">Voice input: use your OS dictation (Win+H / Fn-Fn on Mac) into the answer box if you prefer speaking.</p></Card>
    {active && q && <Card>
      <div className="flex justify-between items-center"><Badge tone="green">{q.category}</Badge><span className="text-xs text-mute">Question {qi+1} of {active.questions.length} · {(active.answers||[]).length} answered</span></div>
      <h2 className="text-lg font-semibold mt-3">{q.question}</h2>
      <p className="text-xs text-dsub dark:text-sub mt-1">💡 {q.guidance}</p>
      <Textarea rows={5} className="mt-3" value={myAnswer?.answer ?? answer} onChange={(e:any)=>setAnswer(e.target.value)} placeholder="Type your answer as you'd say it…" aria-label="Your answer"/>
      <div className="flex flex-wrap gap-2 mt-3">
        <Btn onClick={async()=>{ const text=(myAnswer?.answer ?? answer).trim(); if(text.length<10) return toast('Write a fuller answer first','error'); const s=await post(`/api/v1/interview/sessions/${active.id}/answer`,{question_index:qi,answer:text}); setActive(s); load() }}>Get feedback</Btn>
        <Btn variant="ghost" onClick={()=>{ setQi(Math.max(qi-1,0)); setAnswer('') }} disabled={qi===0}>Previous</Btn>
        <Btn variant="ghost" onClick={()=>{ setQi(Math.min(qi+1,active.questions.length-1)); setAnswer('') }} disabled={qi>=active.questions.length-1}>Next</Btn>
      </div>
      {myAnswer && <div className="mt-4 text-sm"><p className="font-semibold">Feedback — overall {myAnswer.evaluation.overall}/10</p>
        <div className="flex flex-wrap gap-1.5 mt-1">{Object.entries(myAnswer.evaluation.scores).map(([k,v]:any)=><Badge key={k} tone={v>=6?'green':'amber'}>{k}: {v}</Badge>)}</div>
        {myAnswer.evaluation.feedback.map((f:string,i:number)=><p key={i} className="mt-1">• {f}</p>)}<p className="text-xs text-mute mt-1">{myAnswer.evaluation.note}</p></div>}
      {active.status==='completed' && <p className="mt-4 text-sm"><CheckCircle2 className="inline" size={16}/> Session complete — average {active.summary.average_score}/10. {active.summary.advice}</p>}
    </Card>}
    <div><h2 className="font-semibold mb-2">Past sessions</h2>{sessions.length===0? <Empty title="No sessions yet" text="Start a mock interview above. Sessions are saved so you can review your answers and feedback later."/> :
      sessions.map(s=><Card key={s.id} className="mb-3"><div className="flex justify-between items-center gap-2"><div><p className="font-medium text-sm">{s.title}</p><p className="text-xs text-mute">{String(s.created_at||'').slice(0,10)} · {s.status} · {(s.answers||[]).length}/{s.questions.length} answered {s.summary?.average_score?`· avg ${s.summary.average_score}/10`:''}</p></div>
      <span className="flex gap-2"><Btn variant="ghost" onClick={()=>{setActive(s); setQi(0); setAnswer(''); window.scrollTo({top:0,behavior:'smooth'})}}>Resume / review</Btn><button aria-label="Delete session" className="text-red-500 p-2" onClick={async()=>{await del(`/api/v1/interview/sessions/${s.id}`); load()}}><Trash2 size={15}/></button></span></div></Card>)}
    </div>
  </div>
}

/* ---------------- Tracker ---------------- */
const STATUSES=['Saved','Planning','Documents in Progress','Ready to Apply','Applied','Assessment','Interview','Offer','Rejected','Withdrawn','Closed']
function Tracker({toast,err}:any){
  const [apps,setApps]=useState<any[]>([]); const [view,setView]=useState<'kanban'|'table'|'calendar'>('kanban')
  const [form,setForm]=useState<any>({company:'',title:'',status:'Saved'}); const [sel,setSel]=useState<any>(null); const [rem,setRem]=useState<any>({title:'',due_at:''})
  const [filter,setFilter]=useState('')
  async function load(){ setApps(await get(`/api/v1/applications?q=${encodeURIComponent(filter)}`)) }
  useEffect(()=>{ load().catch(()=>{}) },[filter])
  async function setStatus(a:any,s:string){ await put(`/api/v1/applications/${a.id}`,{...a,status:s}); load(); toast(`${a.title} → ${s}`) }
  const card=(a:any)=><div key={a.id} draggable onDragStart={(e:any)=>e.dataTransfer.setData('text/plain',String(a.id))} className="rounded-xl border border-mist-line dark:border-ink-line bg-mist-surface dark:bg-ink-elev p-3 mb-2 cursor-grab">
    <button className="text-left w-full" onClick={()=>setSel(a)}><p className="text-sm font-medium">{a.title}</p><p className="text-xs text-mute">{a.company}{a.match_score!=null?` · ${a.match_score}% match`:''}{a.deadline?` · ⏰ ${a.deadline}`:''}</p></button>
    <Select aria-label="Change status" className="w-full mt-2" value={a.status} onChange={(e:any)=>setStatus(a,e.target.value)}>{STATUSES.map(s=><option key={s}>{s}</option>)}</Select></div>
  return <div className="space-y-5">
    <div className="flex flex-wrap justify-between gap-3 items-center"><div><h1 className="text-2xl font-bold">Application Tracker</h1><p className="text-sm text-dsub dark:text-sub">Drag cards between columns or use the status dropdown (keyboard accessible). Reminders fire only while the app is running.</p></div>
    <div className="flex rounded-xl border border-mist-line dark:border-ink-line overflow-hidden" role="tablist" aria-label="View">
      {([['kanban',Columns3,'Board'],['table',Table2,'Table'],['calendar',CalendarDays,'Calendar']] as const).map(([v,Icon,l]:any)=><button key={v} role="tab" aria-selected={view===v} onClick={()=>setView(v)} className={`px-3 py-2 text-sm flex gap-1.5 items-center ${view===v?'bg-neon text-black font-semibold':'hover:bg-mist-alt dark:hover:bg-ink-alt'}`}><Icon size={14}/>{l}</button>)}
    </div></div>
    <Card><div className="grid sm:grid-cols-4 gap-3"><div><Label>Company</Label><Input value={form.company} onChange={(e:any)=>setForm({...form,company:e.target.value})}/></div>
      <div><Label>Job title</Label><Input value={form.title} onChange={(e:any)=>setForm({...form,title:e.target.value})}/></div>
      <div><Label>Status</Label><Select className="w-full" value={form.status} onChange={(e:any)=>setForm({...form,status:e.target.value})}>{STATUSES.map(s=><option key={s}>{s}</option>)}</Select></div>
      <div><Label>Deadline</Label><Input type="date" value={form.deadline||''} onChange={(e:any)=>setForm({...form,deadline:e.target.value})}/></div></div>
      <div className="flex flex-wrap gap-2 mt-3"><Btn onClick={async()=>{ if(!form.company||!form.title) return toast('Company and title required','error'); await post('/api/v1/applications',form); setForm({company:'',title:'',status:'Saved'}); load(); toast('Application added') }}><Plus size={15}/> Add application</Btn>
      <Input placeholder="Filter by company/title…" className="max-w-60" value={filter} onChange={(e:any)=>setFilter(e.target.value)}/></div></Card>
    {apps.length===0? <Empty title="No applications tracked" text="Add one above, or use 'Track application' on any job. Statistics come only from real records you create here."/> :
    view==='kanban'? <div className="flex gap-3 overflow-x-auto pb-3">{STATUSES.filter(s=>apps.some(a=>a.status===s)||['Saved','Applied','Interview'].includes(s)).map(s=>
      <div key={s} className="min-w-60 w-60 rounded-2xl border border-mist-line dark:border-ink-line p-2 bg-mist-alt/50 dark:bg-ink-surface" onDragOver={(e:any)=>e.preventDefault()} onDrop={(e:any)=>{ const id=Number(e.dataTransfer.getData('text/plain')); const a=apps.find(x=>x.id===id); if(a) setStatus(a,s) }}>
      <p className="text-xs font-semibold px-1 py-1">{s} ({apps.filter(a=>a.status===s).length})</p>{apps.filter(a=>a.status===s).map(card)}</div>)}</div>
    : view==='table'? <Card className="overflow-x-auto"><table className="w-full text-sm"><thead><tr className="text-left text-xs text-mute"><th className="py-2">Role</th><th>Company</th><th>Status</th><th>Match</th><th>Deadline</th><th>Applied</th></tr></thead><tbody>{apps.map(a=><tr key={a.id} className="border-t border-mist-line dark:border-ink-line"><td className="py-2"><button className="underline" onClick={()=>setSel(a)}>{a.title}</button></td><td>{a.company}</td><td><Select value={a.status} onChange={(e:any)=>setStatus(a,e.target.value)}>{STATUSES.map(s=><option key={s}>{s}</option>)}</Select></td><td>{a.match_score!=null?`${a.match_score}%`:'—'}</td><td>{a.deadline||'—'}</td><td>{a.date_applied||'—'}</td></tr>)}</tbody></table></Card>
    : <Card><h2 className="font-semibold">Upcoming dates</h2>{[...apps.filter(a=>a.deadline).map((a:any)=>({d:a.deadline,t:`Deadline: ${a.title} @ ${a.company}`})),...apps.filter(a=>a.follow_up_date).map((a:any)=>({d:a.follow_up_date,t:`Follow up: ${a.title} @ ${a.company}`})),...apps.flatMap((a:any)=>(a.interview_dates||[]).map((d:string)=>({d,t:`Interview: ${a.title} @ ${a.company}`})))].sort((x:any,y:any)=>x.d.localeCompare(y.d)).map((e:any,i:number)=><p key={i} className="text-sm py-1">📅 <b>{e.d}</b> — {e.t}</p>)}{apps.every(a=>!a.deadline&&!a.follow_up_date&&!(a.interview_dates||[]).length)&&<p className="text-sm text-dsub dark:text-sub">No dates set yet — open an application to add deadlines, interviews and follow-ups.</p>}</Card>}
    {sel && <Card><h2 className="font-semibold">{sel.title} @ {sel.company}</h2>
      <div className="grid sm:grid-cols-3 gap-3 mt-3">
        {[['deadline','Deadline','date'],['date_applied','Date applied','date'],['follow_up_date','Follow-up date','date'],['recruiter_name','Recruiter','text'],['recruiter_email','Recruiter email','email'],['application_url','Application URL','url']].map(([k,l,t]:any)=><div key={k}><Label>{l}</Label><Input type={t} value={sel[k]||''} onChange={(e:any)=>setSel({...sel,[k]:e.target.value})}/></div>)}
        <div><Label>Interview dates (comma-separated YYYY-MM-DD)</Label><Input value={(sel.interview_dates||[]).join(', ')} onChange={(e:any)=>setSel({...sel,interview_dates:e.target.value.split(',').map((s:string)=>s.trim()).filter(Boolean)})}/></div>
        <div><Label>Outcome</Label><Select className="w-full" value={sel.outcome||''} onChange={(e:any)=>setSel({...sel,outcome:e.target.value})}><option value="">—</option><option>Pending</option><option>Offer received</option><option>Rejected</option><option>Withdrew</option></Select></div>
      </div>
      <Label>Notes</Label><Textarea rows={3} value={sel.notes||''} onChange={(e:any)=>setSel({...sel,notes:e.target.value})}/>
      <div className="flex flex-wrap gap-2 mt-3"><Btn onClick={async()=>{ await put(`/api/v1/applications/${sel.id}`,sel); load(); toast('Saved') }}>Save details</Btn>
      <Btn variant="ghost" onClick={async()=>{ await del(`/api/v1/applications/${sel.id}`); setSel(null); load(); toast('Deleted') }}>Delete</Btn><Btn variant="ghost" onClick={()=>setSel(null)}>Close</Btn></div>
      {(sel.events||[]).length>0 && <div className="mt-3 text-xs text-mute">{sel.events.map((e:any)=><p key={e.id}>{String(e.created_at).slice(0,16).replace('T',' ')} · {e.event_type}: {e.detail}</p>)}</div>}
      <div className="grid sm:grid-cols-3 gap-2 mt-4"><div><Label>Reminder title</Label><Input value={rem.title} onChange={(e:any)=>setRem({...rem,title:e.target.value})} placeholder="e.g. Follow up with recruiter"/></div>
      <div><Label>Due (date & time)</Label><Input type="datetime-local" value={rem.due_at} onChange={(e:any)=>setRem({...rem,due_at:e.target.value})}/></div>
      <div className="flex items-end"><Btn variant="ghost" onClick={async()=>{ if(!rem.title||!rem.due_at) return toast('Add reminder title and time','error'); await post('/api/v1/reminders',{title:rem.title,due_at:rem.due_at,timezone:Intl.DateTimeFormat().resolvedOptions().timeZone,application_id:sel.id,kind:'follow_up'}); toast('Reminder saved (shown on Dashboard; desktop alerts appear while the app runs)') }}>Add reminder</Btn></div></div>
    </Card>}
  </div>
}

/* ---------------- Insights ---------------- */
function Insights({err}:any){
  const [a,setA]=useState<any>(null); const [i,setI]=useState<any>(null); const [dismissed,setDismissed]=useState<string[]>(()=>JSON.parse(localStorage.getItem('cp-dismissed')||'[]'))
  useEffect(()=>{ get('/api/v1/analytics').then(setA).catch(()=>{}); get('/api/v1/insights').then(setI).catch(()=>{}) },[])
  if(!a||!i) return <Skeleton/>
  const Row=({title,data,unit}:any)=>{ if(dismissed.includes(title)) return null; return <Card><div className="flex justify-between"><h2 className="font-semibold">{title}</h2><button className="text-xs text-mute hover:underline" onClick={()=>{ const d=[...dismissed,title]; setDismissed(d); localStorage.setItem('cp-dismissed',JSON.stringify(d)) }}>Dismiss</button></div>
    {data?.length? data.map(([k,v]:any)=><div key={k} className="flex justify-between text-sm py-1"><span>{k}</span><span><b>{v}</b> {unit}</span></div>) : <p className="text-sm text-dsub dark:text-sub mt-2">Not enough data yet — save more jobs/applications.</p>}</Card> }
  return <div className="space-y-4">
    <div><h1 className="text-2xl font-bold">Career Insights</h1><p className="text-sm text-dsub dark:text-sub">{i.method}</p></div>
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">{[['Jobs analyzed',i.jobs_analyzed],['Applications',a.applications_total],['Submitted',a.applications_submitted],['Response rate',a.response_rate!=null?a.response_rate+'%':'n/a']].map(([k,v]:any)=><Card key={k}><div className="text-xs text-mute">{k}</div><div className="text-2xl font-bold text-pgreen dark:text-neon mt-1">{v}</div></Card>)}</div>
    <Card><h2 className="font-semibold">Pipeline by status</h2><div className="flex flex-wrap gap-1.5 mt-2">{Object.entries(a.by_status).map(([k,v]:any)=><Badge key={k} tone={v>0?'green':'neutral'}>{k}: {v}</Badge>)}</div>
    <p className="text-xs text-mute mt-2">{a.note}</p></Card>
    <div className="grid lg:grid-cols-2 gap-4">
      <Row title="Most requested skills in your saved jobs" data={i.most_requested_skills} unit="listings"/>
      <Row title="Common missing skills (not in your profile)" data={i.common_missing_skills} unit="listings"/>
      <Row title="Sources producing interviews" data={i.sources_producing_interviews} unit="interviews"/>
      <Row title="Repeated document-review issues" data={i.repeated_review_issues} unit="findings"/>
    </div>
    {dismissed.length>0 && <button className="text-xs underline text-pgreen dark:text-neon" onClick={()=>{setDismissed([]);localStorage.removeItem('cp-dismissed')}}>Restore dismissed insights</button>}
  </div>
}

/* ---------------- Settings ---------------- */
function SettingsPage({toast,err,health}:any){
  const {pref,setPref}=useTheme()
  const [tab,setTab]=useState<'ai'|'general'|'privacy'|'sources'|'tasks'>('ai')
  const [cfg,setCfg]=useState<any>(null); const [key,setKey]=useState(''); const [usage,setUsage]=useState<any>(null); const [testing,setTesting]=useState(false)
  const [backups,setBackups]=useState<string[]>([]); const [confirmText,setConfirmText]=useState(''); const [showDelete,setShowDelete]=useState(false)
  const [tasksList,setTasksList]=useState<any[]>([]); const [srcHealth,setSrcHealth]=useState<any[]>([])
  const [sched,setSched]=useState<any>({frequency:'daily',time:'09:00',max_new:10,min_score:0,notify:true})
  async function load(){ try{ setCfg(await get('/api/v1/ai/config')); setUsage(await get('/api/v1/ai/usage')); setBackups(await get('/api/v1/privacy/backups')); setTasksList(await get('/api/v1/tasks')); setSrcHealth(await get('/api/v1/jobs/sources/health')); const s=await get('/api/v1/settings'); if(s.schedule) setSched(s.schedule) }catch(e){err(e)} }
  useEffect(()=>{ load() },[])
  const Tabs=([['ai',Cpu,'AI Provider'],['general',Settings,'General'],['sources',Compass,'Job Sources'],['tasks',Database,'Background Tasks'],['privacy',ShieldCheck,'Privacy & Data']] as const)
  return <div className="space-y-5">
    <div><h1 className="text-2xl font-bold">Settings</h1><p className="text-sm text-dsub dark:text-sub">Everything is stored locally. API keys go to your OS credential store when available, never into the database or frontend.</p></div>
    <div className="flex gap-1 flex-wrap" role="tablist">{Tabs.map(([t,Icon,l]:any)=><button key={t} role="tab" aria-selected={tab===t} onClick={()=>setTab(t)} className={`flex items-center gap-1.5 rounded-xl px-3 py-2 text-sm ${tab===t?'bg-neon text-black font-semibold':'border border-mist-line dark:border-ink-line'}`}><Icon size={14}/>{l}</button>)}</div>
    {tab==='ai' && cfg && <Card><h2 className="font-semibold">AI provider</h2>
      <p className="text-xs mt-1 text-amber-700 dark:text-yellow-300">🔒 {cfg.disclosure}</p>
      <div className="grid sm:grid-cols-2 gap-3 mt-4">
        <div><Label>Provider</Label><Select className="w-full" value={cfg.provider} onChange={(e:any)=>setCfg({...cfg,provider:e.target.value})}><option value="none">None — built-in generation (offline)</option><option value="ollama">Ollama (local models)</option><option value="openai">OpenAI-compatible API (cloud)</option></Select></div>
        <div><Label>Model (e.g. llama3.1, gpt-4o-mini)</Label><Input value={cfg.model} onChange={(e:any)=>setCfg({...cfg,model:e.target.value})}/></div>
        <div><Label>Endpoint</Label><Input value={cfg.endpoint} onChange={(e:any)=>setCfg({...cfg,endpoint:e.target.value})} placeholder={cfg.provider==='ollama'?'http://localhost:11434':'https://api.openai.com/v1'}/></div>
        <div><Label>API key {cfg.has_api_key?'(saved — type to replace)':'(not set)'}</Label><Input type="password" value={key} onChange={(e:any)=>setKey(e.target.value)} autoComplete="off"/></div>
        <div><Label>Temperature: {cfg.temperature}</Label><Input type="range" min="0" max="1" step="0.1" value={cfg.temperature} onChange={(e:any)=>setCfg({...cfg,temperature:parseFloat(e.target.value)})}/></div>
        <div><Label>Max output tokens</Label><Input type="number" value={cfg.max_tokens} onChange={(e:any)=>setCfg({...cfg,max_tokens:parseInt(e.target.value)||2048})}/></div>
        <div><Label>Timeout (seconds)</Label><Input type="number" value={cfg.timeout_seconds} onChange={(e:any)=>setCfg({...cfg,timeout_seconds:parseInt(e.target.value)||60})}/></div>
        <div><Label>Max retries (bounded, with backoff)</Label><Input type="number" min="0" max="5" value={cfg.max_retries} onChange={(e:any)=>setCfg({...cfg,max_retries:parseInt(e.target.value)||0})}/></div>
        <div><Label>Strategy model override (optional)</Label><Input value={cfg.task_models?.strategy||''} onChange={(e:any)=>setCfg({...cfg,task_models:{...cfg.task_models,strategy:e.target.value}})}/></div>
        <div><Label>Drafting model override (optional)</Label><Input value={cfg.task_models?.drafting||''} onChange={(e:any)=>setCfg({...cfg,task_models:{...cfg.task_models,drafting:e.target.value}})}/></div>
      </div>
      <div className="flex flex-wrap gap-2 mt-4">
        <Btn onClick={async()=>{ const r=await put('/api/v1/ai/config',{...cfg,api_key:key||null}); setKey(''); toast(`Saved${r.key_storage?` · key storage: ${r.key_storage}`:''}. Reload to refresh status.`); load() }}>Save AI settings</Btn>
        <Btn variant="ghost" disabled={testing} onClick={async()=>{ setTesting(true); try{ const r=await post('/api/v1/ai/test'); toast(r.ok?`Connection OK: ${r.detail}`:`Connection failed: ${r.detail}`, r.ok?'ok':'error') }finally{setTesting(false)} }}>{testing?<Spinner/>:null} Test connection</Btn>
        {cfg.has_api_key && <Btn variant="ghost" onClick={async()=>{ await del('/api/v1/ai/key'); toast('API key removed'); load() }}>Remove API key</Btn>}
      </div>
      <h3 className="font-semibold mt-6">Usage history</h3>
      <p className="text-xs text-mute">{usage?.note} Approx. total so far: ~{usage?.approx_total_tokens_estimate??0} tokens (estimate).</p>
      <div className="max-h-48 overflow-auto mt-2">{(usage?.records||[]).slice(0,15).map((r:any)=><p key={r.id} className="text-xs py-0.5">{String(r.created_at).slice(0,16).replace('T',' ')} · {r.task} · {r.provider}/{r.model} · {r.success?'✓':'✗ '+r.error}</p>)}{(usage?.records||[]).length===0&&<p className="text-sm text-dsub dark:text-sub">No AI requests yet.</p>}</div>
    </Card>}
    {tab==='general' && <div className="space-y-4"><Card><h2 className="font-semibold">Appearance</h2>
      <div className="flex gap-2 mt-3">{(['light','dark','system'] as const).map(t=><button key={t} aria-pressed={pref===t} onClick={()=>setPref(t)} className={`rounded-xl px-4 py-2 text-sm capitalize ${pref===t?'bg-neon text-black font-semibold':'border border-mist-line dark:border-ink-line'}`}>{t}</button>)}</div>
      <p className="text-xs text-mute mt-2">Default follows your OS until you choose. Preference persists across restarts and applies instantly, including charts, dialogs and inputs.</p></Card>
      <Card><h2 className="font-semibold">Scheduled discovery</h2>
      <p className="text-xs text-amber-700 dark:text-yellow-300 mt-1">⚠️ Honest limitation: scheduled searches run only while CareerPilot AI (or its backend) is open. A closed desktop app cannot search in the background.</p>
      <div className="grid sm:grid-cols-3 gap-3 mt-3"><div><Label>Frequency</Label><Select className="w-full" value={sched.frequency} onChange={(e:any)=>setSched({...sched,frequency:e.target.value})}><option>manual</option><option>daily</option><option>weekly</option></Select></div>
      <div><Label>Time</Label><Input type="time" value={sched.time} onChange={(e:any)=>setSched({...sched,time:e.target.value})}/></div>
      <div><Label>Max new listings</Label><Input type="number" value={sched.max_new} onChange={(e:any)=>setSched({...sched,max_new:parseInt(e.target.value)||10})}/></div></div>
      <Btn className="mt-3" onClick={async()=>{ await put('/api/v1/settings/schedule',sched); toast('Schedule saved (applies to saved searches while app is open)') }}>Save schedule</Btn></Card>
      <Card><h2 className="font-semibold">Local backend token</h2><p className="text-xs text-dsub dark:text-sub mt-1">The Electron app passes this automatically. For browser dev mode, paste the token from your data folder's <code className="font-mono">.api_token</code> file.</p><div className="mt-2"><TokenBox onDone={()=>toast('Token saved — reloading…') || setTimeout(()=>location.reload(),600)}/></div></Card>
    </div>}
    {tab==='sources' && <Card><h2 className="font-semibold">Job sources</h2>
      {srcHealth.map((s:any)=><div key={s.name} className="flex justify-between py-2 border-b border-mist-line dark:border-ink-line last:border-0 text-sm"><span><b>{s.name}</b><span className="block text-xs text-mute">{s.note}</span></span><Badge tone="green">{s.status}</Badge></div>)}
      <div className="text-sm mt-3 space-y-1"><p>• <b>Manual entry & URL import</b> always work — no account needed.</p>
      <p>• <b>Remotive</b> — free public API, remote jobs, no key.</p>
      <p>• <b>Greenhouse / Lever</b> — free public company boards; enter the company slug when searching.</p>
      <p className="text-xs text-mute">Boards like LinkedIn/Indeed require partner agreements and prohibit scraping — CareerPilot does not bypass logins, CAPTCHAs or anti-bot controls. Paste those job descriptions manually instead.</p></div>
    </Card>}
    {tab==='tasks' && <Card><h2 className="font-semibold">Background tasks</h2>{tasksList.length===0?<p className="text-sm mt-2 text-dsub dark:text-sub">No tasks yet. Job searches, imports and generation runs appear here with real status (no fake progress bars).</p>:
      tasksList.map((t:any)=><div key={t.id} className="flex justify-between gap-2 py-2 border-b border-mist-line dark:border-ink-line last:border-0 text-sm"><span><b>{t.name}</b><span className="block text-xs text-mute">{t.kind} · {String(t.created_at).slice(0,16).replace('T',' ')} {t.detail?`· ${t.detail}`:''}</span></span><Badge tone={t.status==='completed'?'green':t.status==='failed'?'red':'neutral'}>{t.status}</Badge></div>)}</Card>}
    {tab==='privacy' && <div className="space-y-4">
      <Card><h2 className="font-semibold">Your data</h2><p className="text-sm text-dsub dark:text-sub mt-1">Stored only in a local SQLite database{health?.database?` at ${health.database}`:''}. No telemetry, no silent uploads. Data leaves this machine only when: (1) you search public job APIs (search words only), (2) you import a job URL, or (3) you configure a cloud AI provider and generate documents.</p>
      <div className="flex flex-wrap gap-2 mt-3"><Btn variant="ghost" onClick={()=>download('/api/v1/privacy/export','careerpilot-export.json').catch(err)}><Download size={14}/> Export all my data (JSON)</Btn>
      <Btn variant="ghost" onClick={async()=>{ const r=await post('/api/v1/privacy/backup'); toast(`Backup created: ${r.backup_file}`); load() }}>Create database backup</Btn></div>
      {backups.length>0 && <div className="mt-3">{backups.map(b=><p key={b} className="text-sm py-0.5">🗄 {b} <button className="underline text-pgreen dark:text-neon ml-2" onClick={async()=>{ if(confirm(`Restore ${b}? Your current database is auto-saved first.`)){ await post(`/api/v1/privacy/restore/${b}`); toast('Restored — reloading…'); setTimeout(()=>location.reload(),700) } }}>restore</button></p>)}</div>}</Card>
      <Card className="border-red-400/50"><h2 className="font-semibold text-red-600 dark:text-red-400">Danger zone</h2>
      <p className="text-sm mt-1">Permanently delete your entire local profile, jobs, documents, applications and history. Create a backup or export first — this cannot be undone.</p>
      <div className="flex gap-2 mt-3"><Input placeholder="Type DELETE to confirm" value={confirmText} onChange={(e:any)=>setConfirmText(e.target.value)} className="max-w-60"/><Btn variant="danger" disabled={confirmText!=='DELETE'} onClick={()=>setShowDelete(true)}>Delete everything</Btn></div></Card>
      <Confirm open={showDelete} title="Delete ALL local data?" text="Your profile, CVs, cover letters, jobs, applications, interview sessions and reminders will be permanently erased from this computer." onCancel={()=>setShowDelete(false)} onConfirm={async()=>{ await post('/api/v1/privacy/delete-all',{confirm:'DELETE'}); setShowDelete(false); toast('All local data deleted'); setTimeout(()=>location.reload(),700) }}/>
    </div>}
  </div>
}
