def dump(obj, exclude=()):
    if obj is None: return None
    out={}
    for c in obj.__table__.columns:
        if c.name in exclude: continue
        v=getattr(obj,c.name)
        out[c.name]=v.isoformat() if hasattr(v,"isoformat") and not isinstance(v,(str,int,float)) else v
    return out
def dumps(objs, exclude=()): return [dump(o,exclude) for o in objs]
def full_profile(db):
    from app.models import UserProfile, WorkExperience, Education, Skill, Project, Certification, Achievement
    p=db.query(UserProfile).first()
    if not p:
        p=UserProfile(); db.add(p); db.commit(); db.refresh(p)
    return {"profile":dump(p),"experience":dumps(db.query(WorkExperience).order_by(WorkExperience.sort_order,WorkExperience.id).all()),"education":dumps(db.query(Education).all()),"skills":dumps(db.query(Skill).all()),"projects":dumps(db.query(Project).all()),"certifications":dumps(db.query(Certification).all()),"achievements":dumps(db.query(Achievement).all())}
