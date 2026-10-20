import re
from difflib import SequenceMatcher
from app.services.skills_taxonomy import KNOWN_SKILLS
def extract_skills(text: str) -> list[str]:
    t=(text or "").lower(); found=[]
    for s in KNOWN_SKILLS:
        if re.search(r'(?<![a-z0-9])'+re.escape(s.lower())+r'(?![a-z0-9])', t): found.append(s)
    return sorted(set(found))
def norm(s:str)->str: return re.sub(r'\s+',' ',(s or '').lower().strip())
def analyze_match(job: dict, profile: dict, weights: dict|None=None) -> dict:
    weights=weights or {"required_skills":40,"experience":25,"projects":15,"education_certs":10,"preferences":10}
    jd=f"{job.get('title','')} {job.get('description','')} {' '.join(job.get('requirements') or [])}"
    job_skills=job.get('skills') or extract_skills(jd)
    user_skills={norm(s['name']):s for s in profile.get('skills',[])}
    verified={k for k,v in user_skills.items() if v.get('verification_status')=='user_confirmed'}
    strong,partial,missing,unknown=[],[],[],[]
    for js in job_skills:
        k=norm(js)
        if k in verified: strong.append({"skill":js,"evidence":user_skills[k].get('evidence') or f"{user_skills[k].get('proficiency','')} — listed in verified profile","status":"confirmed"})
        elif k in user_skills: partial.append({"skill":js,"evidence":"In profile but not user-confirmed","status":"unverified"})
        else: missing.append({"skill":js,"evidence":"Not found in profile — this may mean missing data, not necessarily missing ability","status":"unknown"})
    exp_text=norm(" ".join([e.get('title','')+" "+e.get('description','')+" "+" ".join(e.get('tools') or []) for e in profile.get('experience',[])]))
    exp_hits=sum(1 for s in job_skills if norm(s) in exp_text)
    proj_text=norm(" ".join([p.get('name','')+" "+p.get('description','')+" "+" ".join(p.get('technologies') or []) for p in profile.get('projects',[])]))
    proj_hits=sum(1 for s in job_skills if norm(s) in proj_text)
    n=max(len(job_skills),1)
    required_ratio=(len(strong)+0.5*len(partial))/n if job_skills else 0.5
    exp_ratio=exp_hits/n if job_skills else 0.5; proj_ratio=proj_hits/n if job_skills else 0.5
    edu_ok=bool(profile.get('education')); cert_ok=bool(profile.get('certifications'))
    prefs=profile.get('profile',{}).get('preferences',{}) or {}
    pref_hits=[]; pref_misses=[]
    wp=prefs.get('workplace')
    if wp and job.get('workplace_type') and norm(wp)!=norm(job['workplace_type']) and 'any' not in norm(wp): pref_misses.append(f"Workplace: wants {wp}, job is {job['workplace_type']}")
    elif wp: pref_hits.append(f"Workplace aligns ({job.get('workplace_type') or 'unspecified'})")
    disqualifiers=[]
    sal_min=prefs.get('salary_min')
    if sal_min and job.get('salary_max') and job['salary_max']<float(sal_min): disqualifiers.append(f"Salary max {job['salary_max']} below your minimum {sal_min}")
    avoid=[norm(x) for x in (prefs.get('avoid') or [])]
    for a in avoid:
        if a and a in norm(jd): disqualifiers.append(f"Contains something you asked to avoid: {a}")
    total_w=sum(weights.values()) or 100
    breakdown={"required_skills":round(required_ratio*weights['required_skills'],1),"experience":round(exp_ratio*weights['experience'],1),"projects":round(proj_ratio*weights['projects'],1),"education_certs":round(((0.5 if edu_ok else 0)+(0.5 if cert_ok else 0))*weights['education_certs'],1),"preferences":round(max(0,1-0.5*len(pref_misses))*weights['preferences'],1)}
    score=round(sum(breakdown.values())/total_w*100)
    cat="Strong Match" if score>=70 else "Worth Considering" if score>=50 else "Stretch Opportunity" if score>=30 else "Low Match"
    suggestions=[]
    for m in missing[:6]: suggestions.append(f"If you genuinely have {m['skill']} experience, add it to your profile with evidence; otherwise consider a small project to build it.")
    if not profile.get('skills'): suggestions.append("Add skills to your profile — matching cannot work well without them.")
    rationale=f"Score from structured evidence: {len(strong)}/{len(job_skills)} required skills confirmed, {len(partial)} unverified, {len(missing)} not in profile. Experience mentions {exp_hits} and projects mention {proj_hits} of the required skills. Missing data is treated as unknown, not as proof you lack a skill."
    return {"score":score,"category":cat,"breakdown":breakdown,"weights":weights,"job_skills":job_skills,"strong_matches":strong,"partial_matches":partial,"missing":missing,"unknown":[{"item":"Skills not in profile","detail":"Treated as unknown, not confirmed mismatch"}] if missing else [],"potential_disqualifiers":disqualifiers,"preference_notes":pref_hits+pref_misses,"suggestions":suggestions,"rationale":rationale,"method":"structured-rules-v1 (not an AI opinion)"}
def completeness(profile: dict) -> dict:
    p=profile.get('profile',{})
    checks={"Name & headline":bool(p.get('full_name') and p.get('headline')),"Summary":bool(p.get('summary')),"Experience":bool(profile.get('experience')),"Education":bool(profile.get('education')),"Skills (5+)":len(profile.get('skills',[]))>=5,"Projects":bool(profile.get('projects')),"Certifications":bool(profile.get('certifications')),"Preferences":bool(p.get('preferences')),"Writing style":bool(p.get('writing_style'))}
    done=sum(checks.values()); return {"percent":round(done/len(checks)*100),"checks":checks,"missing":[k for k,v in checks.items() if not v]}
