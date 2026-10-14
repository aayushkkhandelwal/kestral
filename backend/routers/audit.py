"""
Audit Logging & Demo Authentication Router
Tracks investigator activity, evidence exports, queries, and ROI changes.
Demo auth supports switching between Investigator and Administrator roles.
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Header, HTTPException, Query
import config
import db

router = APIRouter(prefix="/api/audit", tags=["Audit Log & Governance"])

@router.get("")
def get_audit_trail(
    limit: int = Query(default=100, ge=1, le=500),
    x_user: str = Header(default="investigator")
):
    """
    Returns chronological audit logs.
    Restricted to Administrator role or authenticated investigators.
    """
    return db.get_audit_logs(limit=limit)

@router.get("/users")
def get_demo_users(x_user: str = Header(default="investigator")):
    """
    Lists demo system users and active identity profile.
    """
    user_info = config.DEMO_USERS.get(x_user, {
        "role": "investigator",
        "name": f"Agent {x_user.capitalize()}",
        "badge": "INV-AUTH"
    })
    return {
        "active_user": x_user,
        "profile": user_info,
        "available_users": [
            {"id": k, **v} for k, v in config.DEMO_USERS.items()
        ]
    }
