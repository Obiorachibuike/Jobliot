import hashlib, re, httpx
from urllib.parse import urlparse, parse_qsl, urlencode
from bs4 import BeautifulSoup
from app.core.security import validate_public_url
from app.services.matching import extract_skills

def normalize_url(u:str)->str:
    if not u: return ""
    p=urlparse(u); q=[(k,v) for k,v in parse_qsl(p.query) if k.lower() not in ("utm_source","utm_medium","utm_campaign","ref","source")]
    return p._replace(fragment="",query=urlencode(q)).geturl().rstrip("/").lower()
def fingerprint(title,company,url,source_id="")->str:
    base=source_id or normalize_url(url) or f"{title}|{company}"
    return hashlib.sha256(f"{title.strip().lower()}|{company.strip().lower()}|{base}".encode()).hexdigest()

class JobSource:
    name="base"
    async def search(self, query:str, filters:dict)->tuple[list[dict],str]: return [],"not implemented"

class GreenhouseSource(JobSource):
    """Public Greenhouse Job Board API (no key): https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true"""
    name="Greenhouse"
    async def search(self, query, filters):
        board=(filters.get("board") or "").strip()
        if not board: return [],"Greenhouse needs a company board token (e.g. 'stripe'). Enter it in the board field."
        try:
            async with httpx.AsyncClient(timeout=20) as c:
                r=await c.get(f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs",params={"content":"true"}); r.raise_for_status()
                jobs=r.json().get("jobs",[])
        except Exception as e: return [],f"Greenhouse request failed: {e}"
        out=[]; q=(query or "").lower()
        import html
        for j in jobs:
            title=j.get("title",""); desc=BeautifulSoup(html.unescape(j.get("content") or ""),"html.parser").get_text("\n")
            if q and q not in (title+" "+desc).lower(): continue
            out.append({"title":title,"company":(j.get("company_name") or board),"location":(j.get("location") or {}).get("name","") if isinstance(j.get("location"),dict) else str(j.get("location") or ""),"description":desc[:12000],"url":j.get("absolute_url",""),"source":"Greenhouse","source_id":str(j.get("id","")),"skills":extract_skills(desc),"published_at":j.get("updated_at","")})
        return out[:50],""

class LeverSource(JobSource):
    """Public Lever Postings API (no key): https://api.lever.co/v0/postings/{company}?mode=json"""
    name="Lever"
    async def search(self, query, filters):
        company=(filters.get("board") or "").strip()
        if not company: return [],"Lever needs a company slug (e.g. 'netflix'). Enter it in the board field."
        try:
            async with httpx.AsyncClient(timeout=20) as c:
                r=await c.get(f"https://api.lever.co/v0/postings/{company}",params={"mode":"json"}); r.raise_for_status(); jobs=r.json()
        except Exception as e: return [],f"Lever request failed: {e}"
        out=[]; q=(query or "").lower()
        for j in jobs or []:
            title=j.get("text",""); desc=j.get("descriptionPlain") or BeautifulSoup(j.get("description") or "","html.parser").get_text("\n")
            if q and q not in (title+" "+desc).lower(): continue
            cats=j.get("categories") or {}
            out.append({"title":title,"company":company,"location":cats.get("location",""),"workplace_type":cats.get("commitment","") and ("Remote" if "remote" in str(cats.get("location","")).lower() else ""),"employment_type":cats.get("commitment",""),"description":desc[:12000],"url":j.get("hostedUrl",""),"source":"Lever","source_id":str(j.get("id","")),"skills":extract_skills(desc)})
        return out[:50],""

class RemotiveSource(JobSource):
    """Remotive public API (no key): https://remotive.com/api/remote-jobs"""
    name="Remotive"
    async def search(self, query, filters):
        try:
            async with httpx.AsyncClient(timeout=20) as c:
                r=await c.get("https://remotive.com/api/remote-jobs",params={"search":query or "", "limit":30}); r.raise_for_status(); jobs=r.json().get("jobs",[])
        except Exception as e: return [],f"Remotive request failed: {e}"
        out=[]
        for j in jobs:
            desc=BeautifulSoup(j.get("description") or "","html.parser").get_text("\n")[:12000]
            out.append({"title":j.get("title",""),"company":j.get("company_name",""),"location":j.get("candidate_required_location","Remote"),"workplace_type":"Remote","employment_type":j.get("job_type",""),"description":desc,"url":j.get("url",""),"source":"Remotive","source_id":str(j.get("id","")),"skills":list(set((j.get("tags") or [])+extract_skills(desc)))[:20],"published_at":j.get("publication_date","")})
        return out,""

SOURCES={"Greenhouse":GreenhouseSource(),"Lever":LeverSource(),"Remotive":RemotiveSource()}

async def fetch_job_url(url:str)->tuple[dict,str]:
    ok,msg=validate_public_url(url)
    if not ok: return {},msg
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=False) as c:
            current=url
            for _ in range(4):
                r=await c.get(current,headers={"User-Agent":"CareerPilotAI/1.0 (personal job import)"})
                if r.status_code in (301,302,303,307,308):
                    loc=r.headers.get("location","")
                    if not loc.startswith("http"): return {},"Unsupported redirect"
                    ok2,m2=validate_public_url(loc)
                    if not ok2: return {},f"Redirect blocked: {m2}"
                    current=loc; continue
                break
            r.raise_for_status()
            if len(r.content)>2_000_000: return {},"Page too large (>2MB)"
            ctype=r.headers.get("content-type","")
            if "html" not in ctype and "text" not in ctype: return {},f"Unsupported content type: {ctype}"
    except Exception as e: return {},f"Could not fetch page: {e}. Paste the job description manually instead."
    soup=BeautifulSoup(r.text,"html.parser")
    for t in soup(["script","style","nav","footer","header"]): t.decompose()
    title=(soup.title.string.strip() if soup.title and soup.title.string else "")
    h1=soup.find("h1");  title=(h1.get_text(strip=True) if h1 else title) or "Untitled role"
    text=re.sub(r'\n{3,}','\n\n',soup.get_text("\n")).strip()[:15000]
    return {"title":title[:240],"company":"","description":text,"url":url,"source":"URL Import","skills":extract_skills(text),"status":"unverified"},""
