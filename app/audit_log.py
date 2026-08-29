import sqlite3
import os
from typing import List
from app.models import AuditRecord

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "audit_log.db")

def init_db():
    """Initializes the SQLite database and creates the audit_records table if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_records (
                id TEXT PRIMARY KEY,
                cart_id TEXT,
                record_json TEXT,
                timestamp TEXT
            )
        """)
        conn.commit()
    finally:
        conn.close()

def save_record(record: AuditRecord) -> None:
    """Saves an AuditRecord to the SQLite database, serializing it to JSON."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO audit_records (id, cart_id, record_json, timestamp) VALUES (?, ?, ?, ?)",
            (record.id, record.cart_id, record.model_dump_json(), record.timestamp)
        )
        conn.commit()
    finally:
        conn.close()

def get_all_records() -> List[AuditRecord]:
    """Retrieves all AuditRecords from the SQLite database, ordered by timestamp."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT record_json FROM audit_records ORDER BY timestamp ASC")
        rows = cursor.fetchall()
    finally:
        conn.close()
    
    records = []
    for (record_json,) in rows:
        records.append(AuditRecord.model_validate_json(record_json))
    return records
