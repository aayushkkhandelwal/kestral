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

    # 4. Evidence Faces Table (Biometric Database Indexing)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS evidence_faces (
        face_id TEXT PRIMARY KEY,
        task_id TEXT NOT NULL,
        track_id INTEGER NOT NULL,
        atm_id TEXT NOT NULL,
        location_name TEXT,
        timestamp_s REAL NOT NULL,
        wall_clock_time TEXT,
        face_image_url TEXT NOT NULL,
        full_frame_url TEXT NOT NULL,
        enhanced_image_url TEXT,
        composite_image_url TEXT,
        quality_score REAL NOT NULL,
        has_real_face INTEGER NOT NULL,
        embedding_json TEXT NOT NULL,
        created_at TEXT NOT NULL
    );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_faces_task ON evidence_faces(task_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_faces_atm ON evidence_faces(atm_id);")

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

# ---------------------------------------------------------------------------
# Evidence Face Operations (Biometric Indexing & Face Search)
# ---------------------------------------------------------------------------
def save_evidence_face(
    task_id: str,
    track_id: int,
    atm_id: str,
    location_name: str,
    timestamp_s: float,
    wall_clock_time: Optional[str],
    face_image_url: str,
    full_frame_url: str,
    quality_score: float,
    has_real_face: bool,
    embedding: List[float],
    enhanced_image_url: Optional[str] = None,
    composite_image_url: Optional[str] = None
) -> Dict[str, Any]:
    face_id = f"{task_id}_{track_id}"
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO evidence_faces (
            face_id, task_id, track_id, atm_id, location_name,
            timestamp_s, wall_clock_time, face_image_url, full_frame_url,
            enhanced_image_url, composite_image_url, quality_score,
            has_real_face, embedding_json, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(face_id) DO UPDATE SET
            atm_id=excluded.atm_id,
            location_name=excluded.location_name,
            timestamp_s=excluded.timestamp_s,
            wall_clock_time=excluded.wall_clock_time,
            face_image_url=excluded.face_image_url,
            full_frame_url=excluded.full_frame_url,
            enhanced_image_url=excluded.enhanced_image_url,
            composite_image_url=excluded.composite_image_url,
            quality_score=excluded.quality_score,
            has_real_face=excluded.has_real_face,
            embedding_json=excluded.embedding_json
    """, (
        face_id, task_id, track_id, atm_id, location_name,
        timestamp_s, wall_clock_time, face_image_url, full_frame_url,
        enhanced_image_url, composite_image_url, quality_score,
        1 if has_real_face else 0, json.dumps(embedding), now
    ))
    conn.commit()
    conn.close()
    return {"face_id": face_id, "status": "saved"}

def get_all_evidence_faces(atm_id: Optional[str] = None, limit: int = 500) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    if atm_id:
        cursor.execute("SELECT * FROM evidence_faces WHERE atm_id = ? ORDER BY timestamp_s DESC LIMIT ?", (atm_id, limit))
    else:
        cursor.execute("SELECT * FROM evidence_faces ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    results = []
    for r in rows:
        results.append({
            "face_id": r["face_id"],
            "task_id": r["task_id"],
            "track_id": r["track_id"],
            "atm_id": r["atm_id"],
            "location_name": r["location_name"] or "ATM Kiosk",
            "timestamp_s": r["timestamp_s"],
            "wall_clock_time": r["wall_clock_time"],
            "face_image_url": r["face_image_url"],
            "full_frame_url": r["full_frame_url"],
            "enhanced_image_url": r["enhanced_image_url"],
            "composite_image_url": r["composite_image_url"],
            "quality_score": r["quality_score"],
            "has_real_face": bool(r["has_real_face"]),
            "embedding": json.loads(r["embedding_json"])
        })
    return results

def backfill_existing_results():
    """Scans results directory and indexes any unindexed tracks into evidence_faces table."""
    import os
    from config import RESULTS_DIR
    if not os.path.exists(RESULTS_DIR):
        return
    for task_id in os.listdir(RESULTS_DIR):
        task_dir = os.path.join(RESULTS_DIR, task_id)
        if not os.path.isdir(task_dir):
            continue
        res_file = os.path.join(task_dir, "results.json")
        emb_file = os.path.join(task_dir, "embeddings.json")
        if not os.path.exists(res_file) or not os.path.exists(emb_file):
            continue
        try:
            with open(res_file, "r") as f:
                res_data = json.load(f)
            with open(emb_file, "r") as f:
                embeddings = json.load(f)
            atm_id = res_data.get("metadata", {}).get("atm_id", "ATM_CENTRAL_01")
            location_name = res_data.get("metadata", {}).get("location_name", "Central Branch Kiosk")
            base_time_str = res_data.get("metadata", {}).get("base_timestamp")
            
            for track in res_data.get("tracks", []):
                tid = track.get("track_id")
                str_tid = str(tid)
                if str_tid not in embeddings:
                    continue
                emb = embeddings[str_tid]
                ts = track.get("best_timestamp", 0.0)
                wall_clock = None
                if base_time_str:
                    try:
                        base_dt = datetime.datetime.fromisoformat(base_time_str.replace("Z", "+00:00"))
                        wall_clock = (base_dt + datetime.timedelta(seconds=ts)).isoformat()
                    except Exception:
                        wall_clock = None
                if not wall_clock:
                    wall_clock = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

                save_evidence_face(
                    task_id=task_id,
                    track_id=tid,
                    atm_id=atm_id,
                    location_name=location_name,
                    timestamp_s=ts,
                    wall_clock_time=wall_clock,
                    face_image_url=track.get("face_image_url", f"/results/{task_id}/track_{tid}_face.jpg"),
                    full_frame_url=track.get("full_frame_url", f"/results/{task_id}/track_{tid}_full.jpg"),
                    enhanced_image_url=f"/results/{task_id}/track_{tid}_enhanced.jpg" if os.path.exists(os.path.join(task_dir, f"track_{tid}_enhanced.jpg")) else None,
                    composite_image_url=f"/results/{task_id}/track_{tid}_composite.jpg" if os.path.exists(os.path.join(task_dir, f"track_{tid}_composite.jpg")) else None,
                    quality_score=track.get("best_score", 0.0),
                    has_real_face=track.get("has_real_face", True),
                    embedding=emb
                )
        except Exception:
            pass

# Ensure DB initialized on module load and backfilled
init_db()
backfill_existing_results()

