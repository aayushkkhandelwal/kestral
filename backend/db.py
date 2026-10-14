"""
SQLite Database Layer for Kestral Surveillance Engine
Stores ATM ROIs, Transactions with Linking Results, and Investigator Audit Logs.
"""
import sqlite3
import json
import datetime
from typing import Dict, Any, List, Optional
from config import DATABASE_PATH

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes database schema if not present."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. ROI Table (ATM surveillance zones)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS rois (
        atm_id TEXT PRIMARY KEY,
        polygon_json TEXT NOT NULL,
        frame_width INTEGER NOT NULL,
        frame_height INTEGER NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """)

    # 2. Transactions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        txn_id TEXT PRIMARY KEY,
        atm_id TEXT NOT NULL,
        task_id TEXT NOT NULL,
        start_s REAL NOT NULL,
        end_s REAL NOT NULL,
        linked_track_id INTEGER,
        confidence REAL DEFAULT 0.0,
        ambiguous INTEGER DEFAULT 0,
        candidates_json TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """)

    # 3. Audit Log Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts TEXT NOT NULL,
        username TEXT NOT NULL,
        role TEXT NOT NULL,
        action TEXT NOT NULL,
        detail TEXT
    );
    """)

    conn.commit()
    conn.close()

# ---------------------------------------------------------------------------
# ROI Operations
# ---------------------------------------------------------------------------
def save_roi(atm_id: str, polygon: List[List[float]], frame_width: int, frame_height: int) -> Dict[str, Any]:
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO rois (atm_id, polygon_json, frame_width, frame_height, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(atm_id) DO UPDATE SET
            polygon_json=excluded.polygon_json,
            frame_width=excluded.frame_width,
            frame_height=excluded.frame_height,
            updated_at=excluded.updated_at
    """, (atm_id, json.dumps(polygon), frame_width, frame_height, now, now))
    conn.commit()
    conn.close()
    return {
        "atm_id": atm_id,
        "polygon": polygon,
        "frame_width": frame_width,
        "frame_height": frame_height,
        "updated_at": now
    }

def get_roi(atm_id: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM rois WHERE atm_id = ?", (atm_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "atm_id": row["atm_id"],
        "polygon": json.loads(row["polygon_json"]),
        "frame_width": row["frame_width"],
        "frame_height": row["frame_height"],
        "updated_at": row["updated_at"]
    }

# ---------------------------------------------------------------------------
# Transaction Operations
# ---------------------------------------------------------------------------
def save_transaction(
    txn_id: str,
    atm_id: str,
    task_id: str,
    start_s: float,
    end_s: float,
    link_result: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    linked_track = link_result.get("track_id") if link_result else None
    confidence = link_result.get("confidence", 0.0) if link_result else 0.0
    ambiguous = 1 if (link_result and link_result.get("ambiguous", False)) else 0
    candidates = json.dumps(link_result.get("candidates", [])) if link_result else "[]"

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO transactions (
            txn_id, atm_id, task_id, start_s, end_s,
            linked_track_id, confidence, ambiguous, candidates_json,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(txn_id) DO UPDATE SET
            atm_id=excluded.atm_id,
            task_id=excluded.task_id,
            start_s=excluded.start_s,
            end_s=excluded.end_s,
            linked_track_id=excluded.linked_track_id,
            confidence=excluded.confidence,
            ambiguous=excluded.ambiguous,
            candidates_json=excluded.candidates_json,
            updated_at=excluded.updated_at
    """, (txn_id, atm_id, task_id, start_s, end_s, linked_track, confidence, ambiguous, candidates, now, now))
    conn.commit()
    conn.close()

    return {
        "txn_id": txn_id,
        "atm_id": atm_id,
        "task_id": task_id,
        "start_s": start_s,
        "end_s": end_s,
        "track_id": linked_track,
        "confidence": confidence,
        "ambiguous": bool(ambiguous),
        "candidates": json.loads(candidates),
        "created_at": now,
        "updated_at": now
    }

def get_transaction(txn_id: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM transactions WHERE txn_id = ?", (txn_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "txn_id": row["txn_id"],
        "atm_id": row["atm_id"],
        "task_id": row["task_id"],
        "start_s": row["start_s"],
        "end_s": row["end_s"],
        "track_id": row["linked_track_id"],
        "confidence": row["confidence"],
        "ambiguous": bool(row["ambiguous"]),
        "candidates": json.loads(row["candidates_json"] or "[]"),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"]
    }

def list_transactions(
    atm_id: Optional[str] = None,
    task_id: Optional[str] = None,
    ambiguous: Optional[bool] = None
) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM transactions WHERE 1=1"
    params = []

    if atm_id:
        query += " AND atm_id = ?"
        params.append(atm_id)
    if task_id:
        query += " AND task_id = ?"
        params.append(task_id)
    if ambiguous is not None:
        query += " AND ambiguous = ?"
        params.append(1 if ambiguous else 0)

    query += " ORDER BY created_at DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    results = []
    for row in rows:
        results.append({
            "txn_id": row["txn_id"],
            "atm_id": row["atm_id"],
            "task_id": row["task_id"],
            "start_s": row["start_s"],
            "end_s": row["end_s"],
            "track_id": row["linked_track_id"],
            "confidence": row["confidence"],
            "ambiguous": bool(row["ambiguous"]),
            "candidates": json.loads(row["candidates_json"] or "[]"),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"]
        })
    return results

# ---------------------------------------------------------------------------
# Audit Log Operations
# ---------------------------------------------------------------------------
def log_audit(username: str, role: str, action: str, detail: str = ""):
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO audit_logs (ts, username, role, action, detail)
        VALUES (?, ?, ?, ?, ?)
    """, (now, username, role, action, detail))
    conn.commit()
    conn.close()

def get_audit_logs(limit: int = 100) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM audit_logs ORDER BY id DESC LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()

    logs = []
    for r in rows:
        logs.append({
            "id": r["id"],
            "ts": r["ts"],
            "user": r["username"],
            "role": r["role"],
            "action": r["action"],
            "detail": r["detail"]
        })
    return logs

# Ensure DB initialized on module load
init_db()
