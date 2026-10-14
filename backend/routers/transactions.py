"""
Transactions & Biometric Linking Router
Links ATM cash transactions to tracked video subjects based on spatiotemporal dwell analysis.
"""
import os
import json
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Header, Query
from pydantic import BaseModel, Field

import config
import db
from services.linking import compute_transaction_link

router = APIRouter(prefix="/api/transactions", tags=["Transactions"])

class CreateTransactionRequest(BaseModel):
    txn_id: str = Field(..., description="Unique transaction ID (e.g. TXN-1001)")
    atm_id: str = Field(..., description="Identifier of the ATM terminal")
    task_id: str = Field(..., description="ID of the processed video task")
    start_s: float = Field(..., description="Transaction start timestamp in video seconds")
    end_s: float = Field(..., description="Transaction end timestamp in video seconds")

def load_task_tracks(task_id: str) -> List[Dict[str, Any]]:
    """Loads processed track trajectories from results.json."""
    results_path = os.path.join(config.RESULTS_DIR, task_id, "results.json")
    if not os.path.exists(results_path):
        return []
    try:
        with open(results_path, "r") as f:
            data = json.load(f)
            return data.get("tracks", [])
    except Exception:
        return []

@router.post("")
def create_transaction(
    payload: CreateTransactionRequest,
    x_user: str = Header(default="investigator")
):
    """
    Registers a new transaction and links it with the video track having the highest dwell
    time inside the ATM interaction polygon.
    """
    if payload.end_s <= payload.start_s:
        raise HTTPException(status_code=400, detail="end_s must be greater than start_s")

    tracks = load_task_tracks(payload.task_id)
    roi = db.get_roi(payload.atm_id)
    roi_polygon = roi.get("polygon") if roi else None

    # Compute spatiotemporal link
    link_result = compute_transaction_link(
        txn_id=payload.txn_id,
        task_id=payload.task_id,
        start_s=payload.start_s,
        end_s=payload.end_s,
        tracks=tracks,
        roi_polygon=roi_polygon
    )

    saved_txn = db.save_transaction(
        txn_id=payload.txn_id,
        atm_id=payload.atm_id,
        task_id=payload.task_id,
        start_s=payload.start_s,
        end_s=payload.end_s,
        link_result=link_result
    )

    db.log_audit(
        username=x_user,
        role="investigator",
        action="CREATE_TRANSACTION",
        detail=f"Created {payload.txn_id} linked to track #{link_result.get('track_id')} (conf={link_result.get('confidence')})"
    )

    return saved_txn

@router.get("")
def list_transactions(
    atm_id: Optional[str] = Query(default=None),
    task_id: Optional[str] = Query(default=None),
    ambiguous: Optional[bool] = Query(default=None)
):
    """
    Returns filtered list of transactions with their link status and confidence.
    """
    return db.list_transactions(atm_id=atm_id, task_id=task_id, ambiguous=ambiguous)

@router.get("/{txn_id}")
def get_transaction(txn_id: str):
    """
    Fetches detailed linking data for a specific transaction.
    """
    txn = db.get_transaction(txn_id)
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return txn

@router.post("/{txn_id}/relink")
def relink_transaction(
    txn_id: str,
    x_user: str = Header(default="investigator")
):
    """
    Recomputes transaction association using the latest ROI polygon and trajectories.
    """
    txn = db.get_transaction(txn_id)
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")

    tracks = load_task_tracks(txn["task_id"])
    roi = db.get_roi(txn["atm_id"])
    roi_polygon = roi.get("polygon") if roi else None

    link_result = compute_transaction_link(
        txn_id=txn["txn_id"],
        task_id=txn["task_id"],
        start_s=txn["start_s"],
        end_s=txn["end_s"],
        tracks=tracks,
        roi_polygon=roi_polygon
    )

    updated_txn = db.save_transaction(
        txn_id=txn["txn_id"],
        atm_id=txn["atm_id"],
        task_id=txn["task_id"],
        start_s=txn["start_s"],
        end_s=txn["end_s"],
        link_result=link_result
    )

    db.log_audit(
        username=x_user,
        role="investigator",
        action="RELINK_TRANSACTION",
        detail=f"Relinked {txn_id} -> track #{link_result.get('track_id')}"
    )

    return updated_txn
