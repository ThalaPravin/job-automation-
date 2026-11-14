import sqlite3
import os
from datetime import datetime
from typing import Dict, Any, Optional

def get_connection(db_path: str = "data/naukri_history.db") -> sqlite3.Connection:
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: str = "data/naukri_history.db") -> None:
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS applied_jobs (
            job_id TEXT PRIMARY KEY,
            title TEXT,
            company TEXT,
            experience TEXT,
            location TEXT,
            job_url TEXT,
            apply_type TEXT,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS profile_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT,
            status TEXT,
            message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def is_job_processed(job_id: str, db_path: str = "data/naukri_history.db") -> bool:
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM applied_jobs WHERE job_id = ?", (job_id,))
    row = cursor.fetchone()
    conn.close()
    return row is not None

def record_job(
    job_id: str,
    title: str,
    company: str,
    experience: str,
    location: str,
    job_url: str,
    apply_type: str,
    status: str,
    db_path: str = "data/naukri_history.db"
) -> None:
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO applied_jobs (
            job_id, title, company, experience, location, job_url, apply_type, status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (job_id, title, company, experience, location, job_url, apply_type, status, datetime.now()))
    conn.commit()
    conn.close()

def record_profile_event(
    action: str,
    status: str,
    message: str,
    db_path: str = "data/naukri_history.db"
) -> None:
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO profile_events (action, status, message, created_at)
        VALUES (?, ?, ?, ?)
    """, (action, status, message, datetime.now()))
    conn.commit()
    conn.close()

def get_today_direct_apply_count(db_path: str = "data/naukri_history.db") -> int:
    conn = get_connection(db_path)
    cursor = conn.cursor()
    today_date = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("""
        SELECT COUNT(*) FROM applied_jobs 
        WHERE apply_type = 'DIRECT' 
          AND status = 'APPLIED' 
          AND date(created_at) = date(?)
    """, (today_date,))
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_today_external_count(db_path: str = "data/naukri_history.db") -> int:
    conn = get_connection(db_path)
    cursor = conn.cursor()
    today_date = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("""
        SELECT COUNT(*) FROM applied_jobs 
        WHERE apply_type = 'EXTERNAL' 
          AND status = 'SAVED_TO_CSV' 
          AND date(created_at) = date(?)
    """, (today_date,))
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_total_stats(db_path: str = "data/naukri_history.db") -> Dict[str, Any]:
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM applied_jobs WHERE apply_type = 'DIRECT' AND status = 'APPLIED'")
    total_direct = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM applied_jobs WHERE apply_type = 'EXTERNAL' AND status = 'SAVED_TO_CSV'")
    total_external = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM applied_jobs")
    total_processed = cursor.fetchone()[0]
    conn.close()
    return {
        "total_direct_applied": total_direct,
        "total_external_saved": total_external,
        "total_jobs_tracked": total_processed
    }
