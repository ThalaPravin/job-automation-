import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_DIR = PROJECT_ROOT / "data"
DB_PATH = DB_DIR / "applications.db"

class Database:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS applications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_key TEXT UNIQUE,
                    company_name TEXT,
                    job_title TEXT,
                    job_url TEXT,
                    status TEXT,
                    pitch_note TEXT,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def is_already_applied(self, job_key: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM applications WHERE job_key = ?", (job_key,))
            return cursor.fetchone() is not None

    def record_application(
        self,
        job_key: str,
        company_name: str,
        job_title: str,
        job_url: str,
        status: str,
        pitch_note: str = ""
    ):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO applications (
                    job_key, company_name, job_title, job_url, status, pitch_note, applied_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                job_key,
                company_name,
                job_title,
                job_url,
                status,
                pitch_note,
                datetime.utcnow().isoformat()
            ))
            conn.commit()

    def get_all_applications(self, limit: int = 50) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT job_key, company_name, job_title, status, applied_at
                FROM applications
                ORDER BY applied_at DESC
                LIMIT ?
            """, (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_stats(self) -> Dict[str, int]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT status, COUNT(*) FROM applications GROUP BY status")
            counts = dict(cursor.fetchall())
            total = sum(counts.values())
            return {
                "total": total,
                "applied": counts.get("APPLIED", 0),
                "dry_run": counts.get("DRY_RUN", 0),
                "skipped": counts.get("SKIPPED", 0),
                "failed": counts.get("FAILED", 0),
            }
