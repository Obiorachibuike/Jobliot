import os
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATA_DIR = Path(os.environ.get("CAREERPILOT_DATA_DIR", Path.home()/".careerpilot"))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = Path(os.environ.get("CAREERPILOT_DB", DATA_DIR/"careerpilot.db"))
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
@event.listens_for(engine, "connect")
def _fk(dbapi_conn, _):
    cur = dbapi_conn.cursor(); cur.execute("PRAGMA foreign_keys=ON"); cur.execute("PRAGMA journal_mode=WAL"); cur.close()
SessionLocal = sessionmaker(bind=engine, autoflush=False)
class Base(DeclarativeBase): pass
def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()
def init_db():
    from app import models  # noqa
    Base.metadata.create_all(bind=engine)
