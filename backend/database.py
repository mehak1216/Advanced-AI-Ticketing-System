from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pathlib import Path
import sqlite3
from datetime import datetime

SQLALCHEMY_DATABASE_URL = "sqlite:///./ticketing.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

REQUIRED_TICKET_COLUMNS = {
    "id",
    "title",
    "description",
    "category",
    "ai_summary",
    "severity",
    "sentiment",
    "resolution_path",
    "suggested_department",
    "suggested_employee_id",
    "confidence",
    "estimated_resolution_time",
    "status",
    "assignee_id",
    "auto_resolved",
    "auto_response",
    "feedback",
    "assigned_at",
    "picked_up_at",
    "resolved_at",
    "created_at",
    "updated_at",
}

def _db_path() -> Path:
    return Path(__file__).resolve().parent / "ticketing.db"

def ensure_schema():
    """
    Ensures the SQLite schema matches expected tables/columns.
    If not, it backs up the DB and lets the app recreate it.
    """
    db_path = _db_path()
    if not db_path.exists():
        return

    try:
        conn = sqlite3.connect(db_path, timeout=1)
    except sqlite3.OperationalError:
        return
    try:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tickets'")
        has_tickets = cur.fetchone() is not None

        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ticket_events'")
        has_events = cur.fetchone() is not None

        if not has_tickets:
            return

        cur.execute("PRAGMA table_info(tickets)")
        cols = {row[1] for row in cur.fetchall()}

        if not REQUIRED_TICKET_COLUMNS.issubset(cols) or not has_events:
            conn.close()
            ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
            backup = db_path.with_suffix(f".db.bak.{ts}")
            db_path.rename(backup)
    except sqlite3.OperationalError:
        return
    finally:
        try:
            conn.close()
        except Exception:
            pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
