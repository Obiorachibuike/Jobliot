def test_health(client): assert client.get("/api/v1/health").json()["status"]=="ok"
def test_token_required(client):
    import httpx
    r=client.get("/api/v1/profile",headers={"x-careerpilot-token":"wrong"}); assert r.status_code==401
def test_onboarding_persistence(client):
    client.put("/api/v1/profile",json={"full_name":"Ada Lovelace","headline":"Python Developer","summary":"Builds APIs with Python and FastAPI.","email":"Ada Lovelace@example.com"})
    client.post("/api/v1/skills",json={"name":"Python","category":"Backend","proficiency":"Advanced"})
    client.post("/api/v1/skills",json={"name":"FastAPI","category":"Backend"})
    client.post("/api/v1/skills",json={"name":"SQL","category":"Databases"})
    client.post("/api/v1/experience",json={"organization":"Acme","title":"Backend Developer","description":"Built Python APIs","achievements":["Shipped FastAPI service"],"tools":["Python"]})
    client.post("/api/v1/education",json={"institution":"Uni","qualification":"BSc CS"})
    client.post("/api/v1/projects",json={"name":"API Kit","description":"Python toolkit","technologies":["Python","FastAPI"]})
    p=client.get("/api/v1/profile").json()
    assert p["profile"]["full_name"]=="Ada Lovelace" and len(p["skills"])>=3 and p["completeness"]["percent"]>40
def test_job_match_and_dedup(client):
    job={"title":"Backend Developer","company":"Acme Corp","description":"We need Python, FastAPI and Kubernetes experience.","url":"https://example.com/job/1?utm_source=x"}
    r1=client.post("/api/v1/jobs",json=job).json(); r2=client.post("/api/v1/jobs",json=job).json()
    assert r2["was_duplicate"] is True
    m=client.post(f"/api/v1/jobs/{r1['id']}/analyze").json()
    assert "Python" in m["job_skills"] and any(x["skill"]=="Python" for x in m["strong_matches"])
    assert any(x["skill"]=="Kubernetes" for x in m["missing"]) and m["score"]>=0
def test_ssrf_blocks_localhost(client):
    r=client.post("/api/v1/jobs/import-url",json={"url":"http://localhost:8000/admin"}); assert r.status_code==400
    r=client.post("/api/v1/jobs/import-url",json={"url":"file:///etc/passwd"}); assert r.status_code==400
def test_studio_and_exports(client):
    jobs=client.get("/api/v1/jobs").json(); jid=jobs[0]["id"]
    pkg=client.post("/api/v1/studio/generate",json={"job_id":jid,"template":"ats","review_rounds":2}).json()
    assert pkg["tailored_cv"]["plain_text"] and pkg["cover_letter"]["plain_text"]
    assert "final" in pkg["tailored_cv"]["review"]
    cvid=pkg["tailored_cv"]["id"]
    pdf=client.get(f"/api/v1/documents/{cvid}/export/pdf"); assert pdf.content[:4]==b"%PDF"
    docx=client.get(f"/api/v1/documents/{cvid}/export/docx"); assert docx.content[:2]==b"PK"
    txt=client.get(f"/api/v1/documents/{cvid}/export/txt"); assert len(txt.content)>50
def test_reviewer_flags_unverified_skill(client):
    docs=client.get("/api/v1/documents").json(); d=docs[0]
    client.put(f"/api/v1/documents/{d['id']}",json={"plain_text":"I am an expert in Rust and improved revenue by 450%."})
    r=client.post(f"/api/v1/documents/{d['id']}/review").json()
    cats={f["category"] for f in r["findings"]}; assert "factual_accuracy" in cats and r["verdict"]=="revision_required"
def test_application_flow_and_analytics(client):
    a=client.post("/api/v1/applications",json={"company":"Acme Corp","title":"Backend Developer","status":"Applied"}).json()
    client.put(f"/api/v1/applications/{a['id']}",json={"status":"Interview","company":"Acme Corp","title":"Backend Developer"})
    an=client.get("/api/v1/analytics").json(); assert an["applications_total"]>=1 and an["interviews"]>=1
def test_interview_flow(client):
    jobs=client.get("/api/v1/jobs").json()
    s=client.post("/api/v1/interview/sessions",json={"job_id":jobs[0]["id"]}).json()
    assert len(s["questions"])>=5
    r=client.post(f"/api/v1/interview/sessions/{s['id']}/answer",json={"question_index":0,"answer":"I built a Python API at Acme. I implemented caching and shipped it, which improved response times for users. My role was lead developer and the result was a stable release."}).json()
    assert r["answers"][0]["evaluation"]["overall"]>0
def test_cv_import_txt(client):
    files={"file":("cv.txt","Alex Dev\ncand@example.com\nPython, FastAPI, SQL\nhttps://github.com/user","text/plain")}
    r=client.post("/api/v1/profile/import-cv",files=files).json()
    assert r["suggested"]["email"]["value"]=="cand@example.com" and "Python" in r["skills_detected"]
def test_backup_and_export(client):
    assert client.post("/api/v1/privacy/backup").json()["backup_file"].endswith(".db")
    assert len(client.get("/api/v1/privacy/backups").json())>=1
    assert client.get("/api/v1/privacy/export").status_code==200
def test_ai_failure_graceful(client):
    assert client.post("/api/v1/ai/test").json()["ok"] is False  # no provider configured -> clear error, no crash
def test_master_cv_separate(client):
    m=client.post("/api/v1/documents/master",json={"template":"modern"}).json()
    assert m["kind"]=="master_cv" and m["id"]!=client.get("/api/v1/documents?kind=tailored_cv").json()[0]["id"]
