import io, json, os, shutil, zipfile
from datetime import datetime, timezone
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.db import get_db, init_db, DB_PATH, DATA_DIR
from app import models as M
from app.serializers import dump, dumps, full_profile
from app.core.security import get_api_token, store_api_key, clear_api_key, get_stored_api_key
from app.services.matching import analyze_match, completeness, extract_skills
from app.services import documents as docsvc
from app.services import agents
from app.jobs.sources import SOURCES, fetch_job_url, normalize_url, fingerprint

app=FastAPI(title="CareerPilot AI API",version="1.0.0",docs_url="/api/docs",openapi_url="/api/openapi.json")
app.add_middleware(CORSMiddleware,allow_origins=["http://localhost:5173","http://127.0.0.1:5173","app://careerpilot"],allow_credentials=False,allow_methods=["*"],allow_headers=["*"])
@app.middleware("http")
async def token_guard(request: Request, call_next):
    if request.url.path in ("/api/v1/health",) or request.method=="OPTIONS": return await call_next(request)
    if request.headers.get("x-careerpilot-token")!=get_api_token():
        return JSONResponse({"detail":"Missing or invalid local API token"},status_code=401)
    return await call_next(request)
@app.on_event("startup")
def _startup():
    init_db()
    from app.db import SessionLocal
    db=SessionLocal()
    if not db.query(M.AIProviderConfig).first(): db.add(M.AIProviderConfig())
    db.query(M.BackgroundTask).filter(M.BackgroundTask.status.in_(["queued","running"])).update({"status":"failed","detail":"Interrupted by application restart"})
    db.commit(); db.close()
def task(db,name,kind,status="completed",detail="",result=None):
    t=M.BackgroundTask(name=name,kind=kind,status=status,detail=detail,result=result or {},started_at=datetime.now(timezone.utc),finished_at=datetime.now(timezone.utc) if status in("completed","failed") else None)
    db.add(t); db.commit(); db.refresh(t); return t
def get_or_404(db,model,id):
    o=db.get(model,id)
    if not o: raise HTTPException(404,"Not found")
    return o

class ProfileIn(BaseModel):
    full_name:str=""; headline:str=""; email:str=""; phone:str=""; city:str=""; country:str=""
    linkedin:str=""; github:str=""; portfolio:str=""; summary:str=""; objectives:list=[]
    show_on_cv:dict={}; preferences:dict={}; writing_style:dict={}; onboarding_step:int|None=None; onboarding_complete:bool|None=None
class ExpIn(BaseModel):
    organization:str; title:str; employment_type:str="Full-time"; start_date:str=""; end_date:str=""; current:bool=False; location:str=""; description:str=""; achievements:list=[]; tools:list=[]; verification_status:str="user_confirmed"
class EduIn(BaseModel):
    institution:str; qualification:str; field:str=""; start_date:str=""; end_date:str=""; current:bool=False; coursework:list=[]; achievements:str=""; verification_status:str="user_confirmed"
class SkillIn(BaseModel):
    name:str; category:str="General"; proficiency:str="Intermediate"; years:float|None=None; last_used:str=""; evidence:str=""; verification_status:str="user_confirmed"
class ProjectIn(BaseModel):
    name:str; description:str=""; problem:str=""; technologies:list=[]; responsibilities:str=""; outcomes:str=""; repo_url:str=""; demo_url:str=""; is_public:bool=True; verification_status:str="user_confirmed"
class CertIn(BaseModel):
    name:str; issuer:str=""; issue_date:str=""; expiry_date:str=""; credential_url:str=""; credential_id:str=""; verification_status:str="user_confirmed"
class AchIn(BaseModel):
    kind:str="award"; title:str; description:str=""; date:str=""; verification_status:str="user_confirmed"
class JobIn(BaseModel):
    title:str; company:str; location:str=""; workplace_type:str=""; employment_type:str=""; salary_min:float|None=None; salary_max:float|None=None; salary_currency:str=""
    description:str=""; requirements:list=[]; skills:list=[]; source:str="Manual"; source_id:str=""; url:str=""; published_at:str=""; closing_date:str=""; experience_level:str=""; industry:str=""
class AppIn(BaseModel):
    job_id:int|None=None; company:str=""; title:str=""; status:str="Saved"; source:str="Manual"; application_url:str=""; deadline:str=""; date_applied:str=""
    cv_document_id:int|None=None; cover_letter_id:int|None=None; recruiter_name:str=""; recruiter_email:str=""; interview_dates:list=[]; follow_up_date:str=""; notes:str=""; outcome:str=""; feedback:str=""

# ---------- health / settings ----------
@app.get("/api/v1/health")
def health(db:Session=Depends(get_db)):
    cfg=db.query(M.AIProviderConfig).first()
    return {"status":"ok","version":"1.0.0","ai_provider":cfg.provider if cfg else "none","ai_model":cfg.model if cfg else "","database":str(DB_PATH)}
@app.get("/api/v1/settings")
def get_settings(db:Session=Depends(get_db)):
    rows=db.query(M.AppSettings).all(); return {r.key:r.value for r in rows}
@app.put("/api/v1/settings/{key}")
def put_settings(key:str, body:dict, db:Session=Depends(get_db)):
    r=db.query(M.AppSettings).filter_by(key=key).first()
    if not r: r=M.AppSettings(key=key); db.add(r)
    r.value=body; db.commit(); return {"key":key,"value":body}
# ---------- profile CRUD ----------
@app.get("/api/v1/profile")
def profile(db:Session=Depends(get_db)): d=full_profile(db); d["completeness"]=completeness(d); return d
@app.put("/api/v1/profile")
def update_profile(body:ProfileIn, db:Session=Depends(get_db)):
    p=db.query(M.UserProfile).first() or M.UserProfile(); db.add(p)
    for k,v in body.model_dump().items():
        if v is not None: setattr(p,k,v)
    db.commit(); db.refresh(p); return dump(p)
def _crud(model, schema):
    def create(body:schema, db:Session=Depends(get_db)):  # type: ignore
        o=model(**body.model_dump()); db.add(o); db.commit(); db.refresh(o); return dump(o)
    return create
@app.post("/api/v1/experience")
def add_exp(body:ExpIn,db:Session=Depends(get_db)): return _crud(M.WorkExperience,ExpIn)(body,db)
@app.put("/api/v1/experience/{id}")
def upd_exp(id:int,body:ExpIn,db:Session=Depends(get_db)):
    o=get_or_404(db,M.WorkExperience,id)
    for k,v in body.model_dump().items(): setattr(o,k,v)
    db.commit(); return dump(o)
@app.delete("/api/v1/experience/{id}")
def del_exp(id:int,db:Session=Depends(get_db)): db.delete(get_or_404(db,M.WorkExperience,id)); db.commit(); return {"deleted":True}
@app.post("/api/v1/education")
def add_edu(body:EduIn,db:Session=Depends(get_db)): return _crud(M.Education,EduIn)(body,db)
@app.put("/api/v1/education/{id}")
def upd_edu(id:int,body:EduIn,db:Session=Depends(get_db)):
    o=get_or_404(db,M.Education,id)
    for k,v in body.model_dump().items(): setattr(o,k,v)
    db.commit(); return dump(o)
@app.delete("/api/v1/education/{id}")
def del_edu(id:int,db:Session=Depends(get_db)): db.delete(get_or_404(db,M.Education,id)); db.commit(); return {"deleted":True}
@app.post("/api/v1/skills")
def add_skill(body:SkillIn,db:Session=Depends(get_db)):
    ex=db.query(M.Skill).filter_by(name=body.name,category=body.category).first()
    if ex:
        for k,v in body.model_dump().items(): setattr(ex,k,v)
        db.commit(); return dump(ex)
    return _crud(M.Skill,SkillIn)(body,db)
@app.delete("/api/v1/skills/{id}")
def del_skill(id:int,db:Session=Depends(get_db)): db.delete(get_or_404(db,M.Skill,id)); db.commit(); return {"deleted":True}
@app.post("/api/v1/projects")
def add_proj(body:ProjectIn,db:Session=Depends(get_db)): return _crud(M.Project,ProjectIn)(body,db)
@app.put("/api/v1/projects/{id}")
def upd_proj(id:int,body:ProjectIn,db:Session=Depends(get_db)):
    o=get_or_404(db,M.Project,id)
    for k,v in body.model_dump().items(): setattr(o,k,v)
    db.commit(); return dump(o)
@app.delete("/api/v1/projects/{id}")
def del_proj(id:int,db:Session=Depends(get_db)): db.delete(get_or_404(db,M.Project,id)); db.commit(); return {"deleted":True}
@app.post("/api/v1/certifications")
def add_cert(body:CertIn,db:Session=Depends(get_db)): return _crud(M.Certification,CertIn)(body,db)
@app.delete("/api/v1/certifications/{id}")
def del_cert(id:int,db:Session=Depends(get_db)): db.delete(get_or_404(db,M.Certification,id)); db.commit(); return {"deleted":True}
@app.post("/api/v1/achievements")
def add_ach(body:AchIn,db:Session=Depends(get_db)): return _crud(M.Achievement,AchIn)(body,db)
@app.delete("/api/v1/achievements/{id}")
def del_ach(id:int,db:Session=Depends(get_db)): db.delete(get_or_404(db,M.Achievement,id)); db.commit(); return {"deleted":True}
# ---------- CV import ----------
@app.post("/api/v1/profile/import-cv")
async def import_cv(file:UploadFile=File(...), db:Session=Depends(get_db)):
    raw=await file.read()
    if len(raw)>10_000_000: raise HTTPException(413,"File too large (max 10MB)")
    name=(file.filename or "").lower(); text=""
    try:
        if name.endswith(".pdf"):
            from pypdf import PdfReader
            text="\n".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(raw)).pages)
        elif name.endswith(".docx"):
            from docx import Document as Dx
            text="\n".join(p.text for p in Dx(io.BytesIO(raw)).paragraphs)
        elif name.endswith(".txt"): text=raw.decode("utf-8",errors="ignore")
        else: raise HTTPException(400,"Unsupported format. Use PDF, DOCX or TXT.")
    except HTTPException: raise
    except Exception as e: raise HTTPException(400,f"Could not read file: {e}")
    import re
    emails=re.findall(r'[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}',text); phones=re.findall(r'\+?\d[\d\s\-()]{7,}\d',text)
    urls=re.findall(r'https?://\S+',text)
    lines=[l.strip() for l in text.splitlines() if l.strip()]
    guess_name=lines[0][:80] if lines and len(lines[0])<80 else ""
    result={"text":text[:20000],"suggested":{"full_name":{"value":guess_name,"uncertain":True},"email":{"value":emails[0] if emails else "","uncertain":False},"phone":{"value":phones[0].strip() if phones else "","uncertain":True},"linkedin":{"value":next((u for u in urls if "linkedin" in u),""),"uncertain":False},"github":{"value":next((u for u in urls if "github" in u),""),"uncertain":False}},"skills_detected":extract_skills(text),"note":"Review every field. Nothing is saved until you approve it in the UI. Detected skills are unverified until you confirm them."}
    task(db,f"CV import: {file.filename}","cv_import","completed","Extracted for review",{"chars":len(text)})
    return result
class ApproveImport(BaseModel):
    fields:dict={}; skills:list[str]=[]
@app.post("/api/v1/profile/approve-import")
def approve_import(body:ApproveImport, db:Session=Depends(get_db)):
    p=db.query(M.UserProfile).first() or M.UserProfile(); db.add(p)
    for k in ("full_name","email","phone","linkedin","github","headline","summary"):
        if body.fields.get(k): setattr(p,k,body.fields[k])
    added=0
    for s in body.skills:
        if not db.query(M.Skill).filter_by(name=s).first():
            db.add(M.Skill(name=s,category="Imported",verification_status="unverified")); added+=1
    db.commit(); return {"saved":True,"skills_added_as_unverified":added}
# ---------- jobs ----------
def save_job(db, data:dict, profile_data:dict):
    fp=fingerprint(data.get('title',''),data.get('company',''),data.get('url',''),data.get('source_id',''))
    ex=db.query(M.JobListing).filter_by(fingerprint=fp).first()
    if ex: return ex,False
    if not data.get('skills'): data['skills']=extract_skills(data.get('description',''))
    j=M.JobListing(**{k:data.get(k) for k in JobIn.model_fields},normalized_url=normalize_url(data.get('url','')),fingerprint=fp)
    j.match=analyze_match(dump(j) | {"description":j.description,"skills":j.skills},profile_data)
    db.add(j); db.commit(); db.refresh(j); return j,True
@app.get("/api/v1/jobs")
def list_jobs(q:str="",source:str="",workplace:str="",min_score:int=0,db:Session=Depends(get_db)):
    rows=db.query(M.JobListing).order_by(M.JobListing.discovered_at.desc()).all(); out=[]
    for j in rows:
        d=dump(j)
        if q and q.lower() not in (j.title+" "+j.company+" "+j.description).lower(): continue
        if source and j.source!=source: continue
        if workplace and (j.workplace_type or "").lower()!=workplace.lower(): continue
        if (j.match or {}).get('score',0)<min_score: continue
        out.append(d)
    return out
@app.get("/api/v1/jobs/{id}")
def get_job(id:int,db:Session=Depends(get_db)): return dump(get_or_404(db,M.JobListing,id))
@app.post("/api/v1/jobs")
def create_job(body:JobIn,db:Session=Depends(get_db)):
    j,created=save_job(db,body.model_dump(),full_profile(db))
    return {**dump(j),"was_duplicate":not created}
@app.delete("/api/v1/jobs/{id}")
def del_job(id:int,db:Session=Depends(get_db)): db.delete(get_or_404(db,M.JobListing,id)); db.commit(); return {"deleted":True}
@app.post("/api/v1/jobs/{id}/analyze")
def analyze_job(id:int,db:Session=Depends(get_db)):
    j=get_or_404(db,M.JobListing,id); j.match=analyze_match(dump(j),full_profile(db)); db.commit(); return j.match
class UrlIn(BaseModel): url:str
@app.post("/api/v1/jobs/import-url")
async def import_url(body:UrlIn,db:Session=Depends(get_db)):
    data,err=await fetch_job_url(body.url)
    if err: raise HTTPException(400,err)
    return data
class SearchIn(BaseModel): query:str=""; source:str="Remotive"; board:str=""
@app.post("/api/v1/jobs/search")
async def search_jobs(body:SearchIn,db:Session=Depends(get_db)):
    src=SOURCES.get(body.source)
    if not src: raise HTTPException(400,f"Unknown source. Available: {', '.join(SOURCES)}")
    results,err=await src.search(body.query,{"board":body.board})
    if err and not results:
        task(db,f"Job search ({body.source})","job_search","failed",err); raise HTTPException(502,err)
    prof=full_profile(db); saved=[]; dup=0
    for r in results:
        j,created=save_job(db,r,prof)
        if created: saved.append(dump(j))
        else: dup+=1
    task(db,f"Job search ({body.source}): {body.query}","job_search","completed",f"{len(saved)} new, {dup} duplicates skipped",{"new":len(saved)})
    return {"jobs":saved,"duplicates_skipped":dup,"source":body.source}
@app.get("/api/v1/jobs/sources/health")
def sources_health():
    return [{"name":n,"requires_key":False,"status":"available (tested via public API)","note":"Greenhouse/Lever need a company board/slug; Remotive needs no configuration."} for n in SOURCES]
@app.get("/api/v1/saved-searches")
def saved_searches(db:Session=Depends(get_db)): return dumps(db.query(M.SavedSearch).all())
class SavedSearchIn(BaseModel): name:str; filters:dict={}; schedule:dict={}
@app.post("/api/v1/saved-searches")
def add_saved(body:SavedSearchIn,db:Session=Depends(get_db)):
    o=M.SavedSearch(**body.model_dump()); db.add(o); db.commit(); db.refresh(o); return dump(o)
@app.delete("/api/v1/saved-searches/{id}")
def del_saved(id:int,db:Session=Depends(get_db)): db.delete(get_or_404(db,M.SavedSearch,id)); db.commit(); return {"deleted":True}
# ---------- documents & studio ----------
def snapshot(db, doc, note=""):
    v=max([x.version for x in doc.versions],default=0)+1
    db.add(M.DocumentVersion(document_id=doc.id,version=v,plain_text=doc.plain_text,content=doc.content,note=note)); db.commit(); return v
def doc_dump(doc):
    d=dump(doc); d["versions"]=[{"id":v.id,"version":v.version,"note":v.note,"created_at":v.created_at.isoformat() if v.created_at else None,"plain_text":v.plain_text} for v in doc.versions]; return d
@app.get("/api/v1/documents/templates")
def templates(): return [{"key":k,**v} for k,v in docsvc.TEMPLATES.items()]
@app.get("/api/v1/documents")
def list_docs(kind:str="",db:Session=Depends(get_db)):
    q=db.query(M.Document).order_by(M.Document.updated_at.desc())
    if kind: q=q.filter_by(kind=kind)
    return [doc_dump(d) for d in q.all()]
@app.get("/api/v1/documents/{id}")
def get_doc(id:int,db:Session=Depends(get_db)): return doc_dump(get_or_404(db,M.Document,id))
class MasterIn(BaseModel): template:str="ats"
@app.post("/api/v1/documents/master")
def build_master(body:MasterIn,db:Session=Depends(get_db)):
    prof=full_profile(db); content=docsvc.build_cv_content(prof,None,body.template); text=docsvc.content_to_text(content)
    doc=db.query(M.Document).filter_by(kind="master_cv").first()
    if not doc: doc=M.Document(kind="master_cv",title="Master CV"); db.add(doc); db.flush()
    doc.template=body.template; doc.content=content; doc.plain_text=text; doc.status="draft"; db.commit(); db.refresh(doc); snapshot(db,doc,"Built from career profile"); return doc_dump(doc)
class DocUpdate(BaseModel): plain_text:str|None=None; content:dict|None=None; title:str|None=None; status:str|None=None; template:str|None=None
@app.put("/api/v1/documents/{id}")
def upd_doc(id:int,body:DocUpdate,db:Session=Depends(get_db)):
    doc=get_or_404(db,M.Document,id)
    if body.status=="approved" and (doc.review or {}).get("verdict")=="revision_required":
        raise HTTPException(400,"Cannot approve: unresolved critical factual findings. Fix them or re-run review.")
    for k,v in body.model_dump().items():
        if v is not None: setattr(doc,k,v)
    if body.content is not None and body.plain_text is None: doc.plain_text=docsvc.content_to_text(doc.content)
    db.commit(); snapshot(db,doc,"Edited"); return doc_dump(doc)
@app.delete("/api/v1/documents/{id}")
def del_doc(id:int,db:Session=Depends(get_db)): db.delete(get_or_404(db,M.Document,id)); db.commit(); return {"deleted":True}
@app.post("/api/v1/documents/{id}/restore/{version}")
def restore_doc(id:int,version:int,db:Session=Depends(get_db)):
    doc=get_or_404(db,M.Document,id); v=next((x for x in doc.versions if x.version==version),None)
    if not v: raise HTTPException(404,"Version not found")
    doc.plain_text=v.plain_text; doc.content=v.content; db.commit(); snapshot(db,doc,f"Restored v{version}"); return doc_dump(doc)
class StudioIn(BaseModel): job_id:int; template:str="ats"; cover_length:str="standard"; review_rounds:int=2; strategy_override:dict|None=None
@app.post("/api/v1/studio/strategy")
async def studio_strategy(body:StudioIn,db:Session=Depends(get_db)):
    job=get_or_404(db,M.JobListing,body.job_id); prof=full_profile(db)
    match=job.match or analyze_match(dump(job),prof)
    return await agents.strategist(db,prof,dump(job),match)
@app.post("/api/v1/studio/generate")
async def studio_generate(body:StudioIn,db:Session=Depends(get_db)):
    job=get_or_404(db,M.JobListing,body.job_id); prof=full_profile(db)
    match=job.match or analyze_match(dump(job),prof); job.match=match
    strategy=body.strategy_override or await agents.strategist(db,prof,dump(job),match)
    content=docsvc.build_cv_content(prof,strategy,body.template); cv_text=docsvc.content_to_text(content)
    cl_text,src=await agents.draft_cover_letter(db,prof,dump(job),strategy,body.cover_length)
    out={}
    for kind,title,text,cnt in [("tailored_cv",f"CV — {job.title} @ {job.company}",cv_text,content),("cover_letter",f"Cover letter — {job.title} @ {job.company}",cl_text,{"plain":cl_text})]:
        doc=M.Document(kind=kind,title=title,job_id=job.id,template=body.template,status="under_review",content=cnt,plain_text=text,strategy=strategy)
        db.add(doc); db.flush()
        review=agents.review_document(text,prof,dump(job),match)
        rounds=[review]
        for _ in range(max(body.review_rounds-1,0)):
            if review["verdict"]=="ready_for_approval": break
            new_text,changes=agents.revise_text(doc.plain_text,review)
            if new_text==doc.plain_text: break
            doc.plain_text=new_text; review=agents.review_document(new_text,prof,dump(job),match); review["changes_applied"]=changes; rounds.append(review)
        doc.review={"rounds":rounds,"final":review,"drafted_by":src}
        doc.status=review["verdict"]; db.commit(); db.refresh(doc); snapshot(db,doc,"Generated + reviewed"); out[kind]=doc_dump(doc)
    task(db,f"Application package: {job.title}","document_generation","completed",f"CV + cover letter via {src}",{})
    return {"strategy":strategy,"match":match,**out}
@app.post("/api/v1/documents/{id}/review")
def review_doc(id:int,db:Session=Depends(get_db)):
    doc=get_or_404(db,M.Document,id); prof=full_profile(db)
    job=db.get(M.JobListing,doc.job_id) if doc.job_id else None
    match=(job.match if job else {}) or {}
    r=agents.review_document(doc.plain_text,prof,dump(job) if job else {},match)
    doc.review={**(doc.review or {}),"final":r}; doc.status=r["verdict"] if doc.status!="approved" else doc.status; db.commit(); return r
@app.post("/api/v1/documents/{id}/revise")
def revise_doc(id:int,db:Session=Depends(get_db)):
    doc=get_or_404(db,M.Document,id); review=(doc.review or {}).get("final") or {}
    if not review: raise HTTPException(400,"Run a review first")
    new_text,changes=agents.revise_text(doc.plain_text,review); doc.plain_text=new_text; db.commit(); snapshot(db,doc,"Auto-revision (safe fixes only)")
    return {"plain_text":new_text,"changes":changes}
@app.get("/api/v1/documents/{id}/export/{fmt}")
def export_doc(id:int,fmt:str,db:Session=Depends(get_db)):
    doc=get_or_404(db,M.Document,id)
    content=doc.content if doc.content and doc.content.get("sections") else None
    if fmt=="txt": data=doc.plain_text.encode(); media="text/plain"; fn=f"{doc.title}.txt"
    elif fmt=="tex":
        if not content: raise HTTPException(400,"LaTeX export needs a structured CV document")
        data=docsvc.render_latex(content).encode(); media="application/x-tex"; fn=f"{doc.title}.tex"
    elif fmt in ("pdf","docx"):
        if content: data=docsvc.render_pdf(content) if fmt=="pdf" else docsvc.render_docx(content)
        else:
            c={"name":doc.title,"headline":"","contact":{},"template":"ats","sections":[{"key":"body","heading":"","items":[{"text":p} for p in doc.plain_text.split("\n\n")]}]}
            data=docsvc.render_pdf(c) if fmt=="pdf" else docsvc.render_docx(c)
        media="application/pdf" if fmt=="pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"; fn=f"{doc.title}.{fmt}"
    else: raise HTTPException(400,"Format must be pdf, docx, txt or tex")
    if not docsvc.validate_export(fmt,data): raise HTTPException(500,"Export validation failed — file was not generated correctly")
    doc.status="exported" if doc.status!="approved" else doc.status; db.commit()
    safe="".join(ch if ch.isalnum() or ch in " ._-" else "_" for ch in fn)
    return Response(content=data,media_type=media,headers={"Content-Disposition":f'attachment; filename="{safe}"'})
# ---------- applications ----------
STATUSES=["Saved","Planning","Documents in Progress","Ready to Apply","Applied","Assessment","Interview","Offer","Rejected","Withdrawn","Closed"]
@app.get("/api/v1/applications/statuses")
def app_statuses(): return STATUSES
@app.get("/api/v1/applications")
def list_apps(status:str="",q:str="",db:Session=Depends(get_db)):
    rows=db.query(M.Application).order_by(M.Application.updated_at.desc()).all(); out=[]
    for a in rows:
        if status and a.status!=status: continue
        if q and q.lower() not in (a.title+" "+a.company).lower(): continue
        d=dump(a); d["events"]=[{"id":e.id,"event_type":e.event_type,"detail":e.detail,"created_at":e.created_at.isoformat() if e.created_at else None} for e in a.events]
        j=db.get(M.JobListing,a.job_id) if a.job_id else None; d["match_score"]=(j.match or {}).get("score") if j else None
        out.append(d)
    return out
@app.post("/api/v1/applications")
def add_app(body:AppIn,db:Session=Depends(get_db)):
    if body.job_id:
        j=get_or_404(db,M.JobListing,body.job_id)
        body.company=body.company or j.company; body.title=body.title or j.title; body.source=body.source or j.source; body.application_url=body.application_url or j.url
    a=M.Application(**body.model_dump()); db.add(a); db.flush(); db.add(M.ApplicationEvent(application_id=a.id,event_type="created",detail=f"Status: {a.status}")); db.commit(); db.refresh(a); return dump(a)
@app.put("/api/v1/applications/{id}")
def upd_app(id:int,body:AppIn,db:Session=Depends(get_db)):
    a=get_or_404(db,M.Application,id); old=a.status
    for k,v in body.model_dump().items():
        if v not in (None,"") or k in ("notes","feedback"): setattr(a,k,v)
    if old!=a.status: db.add(M.ApplicationEvent(application_id=a.id,event_type="status_change",detail=f"{old} → {a.status}"))
    db.commit(); return dump(a)
@app.delete("/api/v1/applications/{id}")
def del_app(id:int,db:Session=Depends(get_db)): db.delete(get_or_404(db,M.Application,id)); db.commit(); return {"deleted":True}
@app.get("/api/v1/analytics")
def analytics(db:Session=Depends(get_db)):
    apps=db.query(M.Application).all(); jobs=db.query(M.JobListing).all()
    applied=[a for a in apps if a.status in ("Applied","Assessment","Interview","Offer","Rejected")]
    interviews=[a for a in apps if a.status in ("Interview","Offer")]; offers=[a for a in apps if a.status=="Offer"]
    by_status={s:len([a for a in apps if a.status==s]) for s in STATUSES}
    by_source={}
    for j in jobs: by_source[j.source]=by_source.get(j.source,0)+1
    return {"opportunities_discovered":len(jobs),"applications_total":len(apps),"applications_submitted":len(applied),"interviews":len(interviews),"offers":len(offers),"response_rate":round(len(interviews)/len(applied)*100,1) if applied else None,"by_status":by_status,"jobs_by_source":by_source,"note":"Computed only from your stored records. Empty database = empty stats (nothing is fabricated)."}
@app.get("/api/v1/insights")
def insights(db:Session=Depends(get_db)):
    jobs=db.query(M.JobListing).all(); apps=db.query(M.Application).all()
    from collections import Counter
    req=Counter(); miss=Counter()
    for j in jobs:
        for s in (j.skills or []): req[s]+=1
        for m in (j.match or {}).get("missing",[]): miss[m["skill"]]+=1
    src_interviews=Counter(a.source for a in apps if a.status in ("Interview","Offer"))
    reviews=db.query(M.Document).all(); cats=Counter()
    for d in reviews:
        for f in ((d.review or {}).get("final") or {}).get("findings",[]): cats[f["category"]]+=1
    return {"most_requested_skills":req.most_common(10),"common_missing_skills":miss.most_common(10),"sources_producing_interviews":src_interviews.most_common(),"repeated_review_issues":cats.most_common(),"method":"Counts over your stored jobs/applications/documents. Correlation is not causation — treat as prompts to investigate, not proof.","jobs_analyzed":len(jobs)}
# ---------- interview ----------
class InterviewIn(BaseModel): job_id:int|None=None; title:str=""
@app.post("/api/v1/interview/sessions")
def new_session(body:InterviewIn,db:Session=Depends(get_db)):
    prof=full_profile(db); job=db.get(M.JobListing,body.job_id) if body.job_id else None
    jd=dump(job) if job else {"title":body.title or "General practice","description":""}
    match=(job.match if job else {}) or {}
    s=M.InterviewSession(job_id=body.job_id,title=body.title or (f"{job.title} @ {job.company}" if job else "General practice"),questions=agents.interview_questions(prof,jd,match))
    db.add(s); db.commit(); db.refresh(s); return dump(s)
@app.get("/api/v1/interview/sessions")
def list_sessions(db:Session=Depends(get_db)): return dumps(db.query(M.InterviewSession).order_by(M.InterviewSession.created_at.desc()).all())
class AnswerIn(BaseModel): question_index:int; answer:str
@app.post("/api/v1/interview/sessions/{id}/answer")
def answer(id:int,body:AnswerIn,db:Session=Depends(get_db)):
    s=get_or_404(db,M.InterviewSession,id)
    if body.question_index>=len(s.questions): raise HTTPException(400,"Question index out of range")
    q=s.questions[body.question_index]; ev=agents.evaluate_answer(q,body.answer)
    answers=list(s.answers or []); answers=[a for a in answers if a.get("question_index")!=body.question_index]
    answers.append({"question_index":body.question_index,"question":q["question"],"answer":body.answer,"evaluation":ev}); s.answers=answers
    if len(answers)>=len(s.questions):
        s.status="completed"; s.summary={"average_score":round(sum(a["evaluation"]["overall"] for a in answers)/len(answers),1),"answered":len(answers),"total":len(s.questions),"advice":"Re-practise your lowest-scoring answers aloud using real examples."}
    db.commit(); db.refresh(s); return dump(s)
@app.delete("/api/v1/interview/sessions/{id}")
def del_session(id:int,db:Session=Depends(get_db)): db.delete(get_or_404(db,M.InterviewSession,id)); db.commit(); return {"deleted":True}
# ---------- reminders, tasks, ai, privacy ----------
class ReminderIn(BaseModel): title:str; kind:str="follow_up"; due_at:str; timezone:str="UTC"; application_id:int|None=None; notes:str=""; done:bool=False
@app.get("/api/v1/reminders")
def reminders(db:Session=Depends(get_db)): return dumps(db.query(M.Reminder).order_by(M.Reminder.due_at).all())
@app.post("/api/v1/reminders")
def add_rem(body:ReminderIn,db:Session=Depends(get_db)):
    o=M.Reminder(**body.model_dump()); db.add(o); db.commit(); db.refresh(o); return dump(o)
@app.put("/api/v1/reminders/{id}")
def upd_rem(id:int,body:ReminderIn,db:Session=Depends(get_db)):
    o=get_or_404(db,M.Reminder,id)
    for k,v in body.model_dump().items(): setattr(o,k,v)
    db.commit(); return dump(o)
@app.delete("/api/v1/reminders/{id}")
def del_rem(id:int,db:Session=Depends(get_db)): db.delete(get_or_404(db,M.Reminder,id)); db.commit(); return {"deleted":True}
@app.get("/api/v1/tasks")
def tasks(db:Session=Depends(get_db)): return dumps(db.query(M.BackgroundTask).order_by(M.BackgroundTask.created_at.desc()).limit(50).all())
@app.post("/api/v1/tasks/{id}/cancel")
def cancel_task(id:int,db:Session=Depends(get_db)):
    t=get_or_404(db,M.BackgroundTask,id)
    if t.status in ("queued","running"): t.status="cancelled"
    db.commit(); return dump(t)
class AIIn(BaseModel):
    provider:str="none"; model:str=""; endpoint:str=""; temperature:float=0.3; max_tokens:int=2048; timeout_seconds:int=60; max_retries:int=2; task_models:dict={}; monthly_token_budget:int|None=None; api_key:str|None=None
@app.get("/api/v1/ai/config")
def ai_config(db:Session=Depends(get_db)):
    c=db.query(M.AIProviderConfig).first(); d=dump(c); d["is_local"]=c.provider=="ollama"; d["disclosure"]="Local (Ollama): data stays on this machine." if c.provider=="ollama" else ("Cloud provider: profile/job text you send for generation leaves this machine." if c.provider!="none" else "No AI provider — built-in non-AI generation is used; nothing leaves this machine.")
    return d
@app.put("/api/v1/ai/config")
def upd_ai(body:AIIn,db:Session=Depends(get_db)):
    c=db.query(M.AIProviderConfig).first() or M.AIProviderConfig(); db.add(c)
    for k,v in body.model_dump(exclude={"api_key"}).items(): setattr(c,k,v)
    storage=""
    if body.api_key: storage=store_api_key(body.api_key); c.has_api_key=True
    db.commit(); return {**dump(c),"key_storage":storage}
@app.delete("/api/v1/ai/key")
def rm_key(db:Session=Depends(get_db)):
    clear_api_key(); c=db.query(M.AIProviderConfig).first()
    if c: c.has_api_key=False; db.commit()
    return {"removed":True}
@app.post("/api/v1/ai/test")
async def ai_test(db:Session=Depends(get_db)):
    from app.ai.provider import test_connection
    return await test_connection(db)
@app.get("/api/v1/ai/usage")
def ai_usage(db:Session=Depends(get_db)):
    rows=db.query(M.AIUsageRecord).order_by(M.AIUsageRecord.created_at.desc()).limit(100).all()
    total_chars=sum(r.prompt_chars+r.completion_chars for r in rows)
    return {"records":dumps(rows),"approx_total_tokens_estimate":round(total_chars/4),"note":"Token counts are a rough chars/4 estimate. Exact cost depends on your provider's pricing — check your provider dashboard."}
@app.get("/api/v1/dashboard")
def dashboard(db:Session=Depends(get_db)):
    prof=full_profile(db); jobs=db.query(M.JobListing).order_by(M.JobListing.discovered_at.desc()).all()
    top=sorted(jobs,key=lambda j:-(j.match or {}).get("score",0))[:5]
    upcoming=db.query(M.Reminder).filter_by(done=False).order_by(M.Reminder.due_at).limit(5).all()
    return {"profile_name":prof["profile"].get("full_name",""),"onboarding_complete":bool(prof["profile"].get("onboarding_complete")),"completeness":completeness(prof),"new_jobs":len(jobs),"top_matches":dumps(top),"applications_in_progress":db.query(M.Application).filter(M.Application.status.notin_(["Rejected","Withdrawn","Closed"])).count(),"upcoming_reminders":dumps(upcoming),"recent_documents":dumps(db.query(M.Document).order_by(M.Document.updated_at.desc()).limit(5).all()),"recent_tasks":dumps(db.query(M.BackgroundTask).order_by(M.BackgroundTask.created_at.desc()).limit(5).all()),"analytics":analytics(db)}
@app.get("/api/v1/privacy/export")
def export_all(db:Session=Depends(get_db)):
    data={"profile":full_profile(db),"jobs":dumps(db.query(M.JobListing).all()),"applications":dumps(db.query(M.Application).all()),"documents":[{"id":d.id,"kind":d.kind,"title":d.title,"plain_text":d.plain_text} for d in db.query(M.Document).all()],"interview_sessions":dumps(db.query(M.InterviewSession).all()),"reminders":dumps(db.query(M.Reminder).all()),"exported_at":datetime.now(timezone.utc).isoformat()}
    return Response(content=json.dumps(data,indent=2),media_type="application/json",headers={"Content-Disposition":'attachment; filename="careerpilot-export.json"'})
@app.post("/api/v1/privacy/backup")
def backup(db:Session=Depends(get_db)):
    dest=DATA_DIR/"backups"; dest.mkdir(exist_ok=True)
    name=f"backup-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}.db"
    db.commit(); shutil.copy2(DB_PATH,dest/name)
    return {"backup_file":name,"location":str(dest)}
@app.get("/api/v1/privacy/backups")
def list_backups():
    dest=DATA_DIR/"backups"; return sorted([p.name for p in dest.glob("*.db")]) if dest.exists() else []
@app.post("/api/v1/privacy/restore/{name}")
def restore(name:str):
    src=DATA_DIR/"backups"/Path(name).name
    if not src.exists(): raise HTTPException(404,"Backup not found")
    from app.db import engine
    engine.dispose(); shutil.copy2(DB_PATH,DATA_DIR/"backups"/"pre-restore-auto.db"); shutil.copy2(src,DB_PATH)
    return {"restored":name,"note":"Previous database saved as pre-restore-auto.db. Restart the app if data looks stale."}
class DeleteAllIn(BaseModel): confirm:str=""
@app.post("/api/v1/privacy/delete-all")
def delete_all(body:DeleteAllIn,db:Session=Depends(get_db)):
    if body.confirm!="DELETE": raise HTTPException(400,'Type DELETE to confirm. This permanently erases your local profile, jobs, documents and applications.')
    for model in [M.ApplicationEvent,M.Application,M.DocumentVersion,M.Document,M.InterviewSession,M.Reminder,M.BackgroundTask,M.SavedSearch,M.JobListing,M.WorkExperience,M.Education,M.Skill,M.Project,M.Certification,M.Achievement,M.UserProfile]:
        db.query(model).delete()
    db.commit(); return {"deleted":True}
