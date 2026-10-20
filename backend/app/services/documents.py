import io, json, re
TEMPLATES={
 "ats":{"name":"ATS-Friendly","desc":"Single column, minimal decoration, safe text extraction."},
 "modern":{"name":"Modern Developer","desc":"Clean modern hierarchy with skills sidebar emphasis."},
 "fullstack":{"name":"Full-Stack Engineer","desc":"Projects and stack-forward layout."},
 "backend":{"name":"Backend Engineer","desc":"Systems, APIs and databases first."},
 "ai":{"name":"AI Engineer","desc":"ML projects and research emphasis."},
 "mobile":{"name":"Mobile Developer","desc":"Apps and platform skills first."},
 "graduate":{"name":"Graduate & Early Career","desc":"Education and projects first."},
 "academic":{"name":"Academic & Research","desc":"Publications, research and education first."},
}
SECTION_ORDER={"ats":["summary","experience","skills","projects","education","certifications"],"modern":["summary","skills","experience","projects","education","certifications"],"fullstack":["summary","projects","experience","skills","education","certifications"],"backend":["summary","experience","skills","projects","education","certifications"],"ai":["summary","projects","skills","experience","education","certifications"],"mobile":["summary","projects","experience","skills","education","certifications"],"graduate":["summary","education","projects","skills","experience","certifications"],"academic":["summary","education","experience","projects","skills","certifications"]}
def build_cv_content(profile:dict, strategy:dict|None=None, template:str="ats")->dict:
    p=profile.get('profile',{}); strategy=strategy or {}
    focus=set(s.lower() for s in (strategy.get('highlight_skills') or []))
    skills=sorted(profile.get('skills',[]),key=lambda s:(0 if s['name'].lower() in focus else 1, s.get('category',''), s['name']))
    sections=[]
    labels={"summary":"Professional Summary","experience":"Experience","skills":"Skills","projects":"Projects","education":"Education","certifications":"Certifications"}
    for key in SECTION_ORDER.get(template,SECTION_ORDER["ats"]):
        if key=="summary" and p.get('summary'): sections.append({"key":key,"heading":labels[key],"items":[{"text":strategy.get('tailored_summary') or p['summary']}]})
        elif key=="experience" and profile.get('experience'):
            items=[]
            for e in profile['experience']:
                bullets=list(e.get('achievements') or [])+([e['description']] if e.get('description') else [])
                items.append({"title":f"{e['title']} — {e['organization']}","meta":f"{e.get('start_date','')} – {'Present' if e.get('current') else e.get('end_date','')}".strip(" –"),"bullets":bullets})
            sections.append({"key":key,"heading":labels[key],"items":items})
        elif key=="skills" and skills:
            by={}
            for s in skills: by.setdefault(s.get('category') or 'General',[]).append(s['name'])
            sections.append({"key":key,"heading":labels[key],"items":[{"title":k,"text":", ".join(v)} for k,v in by.items()]})
        elif key=="projects" and profile.get('projects'):
            sections.append({"key":key,"heading":labels[key],"items":[{"title":pr['name'],"meta":", ".join(pr.get('technologies') or []),"bullets":list(filter(None,[pr.get('description'),pr.get('outcomes')]))} for pr in profile['projects']]})
        elif key=="education" and profile.get('education'):
            sections.append({"key":key,"heading":labels[key],"items":[{"title":f"{ed['qualification']} — {ed['institution']}","meta":ed.get('end_date',''),"text":ed.get('field','')} for ed in profile['education']]})
        elif key=="certifications" and profile.get('certifications'):
            sections.append({"key":key,"heading":labels[key],"items":[{"title":c['name'],"meta":c.get('issuer','')} for c in profile['certifications']]})
    return {"name":p.get('full_name',''),"headline":p.get('headline',''),"contact":{"email":p.get('email',''),"phone":p.get('phone',''),"location":", ".join(filter(None,[p.get('city',''),p.get('country','')])),"linkedin":p.get('linkedin',''),"github":p.get('github',''),"portfolio":p.get('portfolio','')},"template":template,"sections":sections}
def content_to_text(content:dict)->str:
    lines=[content.get('name',''),content.get('headline','')]
    c=content.get('contact') or {}; lines.append(" | ".join(filter(None,[c.get('email'),c.get('phone'),c.get('location'),c.get('linkedin'),c.get('github'),c.get('portfolio')])))
    for s in content.get('sections',[]):
        lines.append(f"\n{s['heading'].upper()}")
        for it in s.get('items',[]):
            if it.get('title'): lines.append(it['title']+((f"  ({it['meta']})") if it.get('meta') else ""))
            if it.get('text'): lines.append(it['text'])
            for b in it.get('bullets') or []: lines.append(f"• {b}")
    return "\n".join(lines).strip()
def render_docx(content:dict)->bytes:
    from docx import Document
    from docx.shared import Pt, RGBColor
    d=Document(); st=d.styles['Normal']; st.font.name='Calibri'; st.font.size=Pt(10.5)
    ats=content.get('template')=='ats'
    h=d.add_heading(content.get('name','Candidate'),level=0)
    if not ats:
        for r in h.runs: r.font.color.rgb=RGBColor(0x14,0x5C,0x22)
    if content.get('headline'): d.add_paragraph(content['headline']).runs[0].bold=True
    c=content.get('contact') or {}; d.add_paragraph(" | ".join(filter(None,[c.get('email'),c.get('phone'),c.get('location'),c.get('linkedin'),c.get('github'),c.get('portfolio')])))
    for s in content.get('sections',[]):
        d.add_heading(s['heading'],level=1)
        for it in s.get('items',[]):
            if it.get('title'): p=d.add_paragraph(); r=p.add_run(it['title']); r.bold=True; p.add_run((f"  ({it['meta']})") if it.get('meta') else "")
            if it.get('text'): d.add_paragraph(it['text'])
            for b in it.get('bullets') or []: d.add_paragraph(b,style='List Bullet')
    bio=io.BytesIO(); d.save(bio); return bio.getvalue()
def render_pdf(content:dict)->bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib.colors import HexColor
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from xml.sax.saxutils import escape
    bio=io.BytesIO(); doc=SimpleDocTemplate(bio,pagesize=A4,topMargin=14*mm,bottomMargin=14*mm,leftMargin=16*mm,rightMargin=16*mm,title=f"{content.get('name','CV')} CV",author=content.get('name',''))
    ss=getSampleStyleSheet(); green=HexColor("#145C22")
    name_st=ParagraphStyle('n',parent=ss['Title'],textColor=green if content.get('template')!='ats' else HexColor("#111111"),fontSize=20,spaceAfter=2)
    h1=ParagraphStyle('h1',parent=ss['Heading1'],fontSize=12,textColor=green,spaceBefore=10,spaceAfter=4,borderPadding=(0,0,2,0))
    body=ParagraphStyle('b',parent=ss['BodyText'],fontSize=9.5,leading=13)
    bold=ParagraphStyle('bb',parent=body,fontName='Helvetica-Bold',spaceBefore=4)
    story=[Paragraph(escape(content.get('name','Candidate')),name_st)]
    if content.get('headline'): story.append(Paragraph(f"<b>{escape(content['headline'])}</b>",body))
    c=content.get('contact') or {}; story.append(Paragraph(escape(" | ".join(filter(None,[c.get('email'),c.get('phone'),c.get('location'),c.get('linkedin'),c.get('github'),c.get('portfolio')]))),body))
    for s in content.get('sections',[]):
        story.append(Paragraph(escape(s['heading']),h1))
        for it in s.get('items',[]):
            if it.get('title'): story.append(Paragraph(escape(it['title']+((f" ({it['meta']})") if it.get('meta') else "")),bold))
            if it.get('text'): story.append(Paragraph(escape(it['text']),body))
            for b in it.get('bullets') or []: story.append(Paragraph("• "+escape(b),body))
        story.append(Spacer(1,4))
    doc.build(story); return bio.getvalue()
def render_latex(content:dict)->str:
    esc=lambda s:(s or "").replace("\\","").replace("%",r"\%").replace("&",r"\&").replace("#",r"\#").replace("_",r"\_")
    parts=[r"\documentclass[11pt]{article}",r"\usepackage[margin=2cm]{geometry}",r"\usepackage{hyperref}",r"\begin{document}",rf"\begin{{center}}{{\LARGE {esc(content.get('name',''))}}}\\{esc(content.get('headline',''))}\end{{center}}"]
    for s in content.get('sections',[]):
        parts.append(rf"\section*{{{esc(s['heading'])}}}")
        for it in s.get('items',[]):
            if it.get('title'): parts.append(rf"\textbf{{{esc(it['title'])}}}\\")
            if it.get('text'): parts.append(esc(it['text'])+"\\\\")
            if it.get('bullets'):
                parts.append(r"\begin{itemize}"); parts += [rf"\item {esc(b)}" for b in it['bullets']]; parts.append(r"\end{itemize}")
    parts.append(r"\end{document}"); return "\n".join(parts)
def validate_export(fmt:str,data:bytes)->bool:
    if not data: return False
    if fmt=="pdf": return data[:4]==b"%PDF"
    if fmt=="docx": return data[:2]==b"PK"
    return len(data)>0
