"""
ATM ROI Polygon Management Router
Allows investigators to configure and retrieve designated ATM interaction zones for surveillance cameras.
"""
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel, Field
import db

router = APIRouter(prefix="/api/rois", tags=["ROIs"])

class ROIRequest(BaseModel):
    polygon: List[List[float]] = Field(..., description="List of [x, y] coordinates in original frame pixels")
    frame_width: int = Field(default=1280, description="Reference video frame width")
    frame_height: int = Field(default=720, description="Reference video frame height")

@router.put("/{atm_id}")
def update_roi(
    atm_id: str,
    payload: ROIRequest,
    x_user: str = Header(default="investigator")
):
    """
    Saves or updates the surveillance interaction polygon for a specific ATM.
    """
    if len(payload.polygon) < 3:
        raise HTTPException(status_code=400, detail="Polygon must contain at least 3 points")

    result = db.save_roi(
        atm_id=atm_id,
        polygon=payload.polygon,
        frame_width=payload.frame_width,
        frame_height=payload.frame_height
    )
    db.log_audit(
        username=x_user,
        role="investigator",
        action="UPDATE_ROI",
        detail=f"Updated ATM zone for {atm_id} with {len(payload.polygon)} vertices"
    )
    return result

@router.get("/{atm_id}")
def get_roi(atm_id: str):
    """
    Retrieves the surveillance polygon for an ATM. Returns default bounding box if none set.
    """
    roi = db.get_roi(atm_id)
    if roi:
        return roi

    # Return sensible default zone centered on 1280x720 frame
    return {
        "atm_id": atm_id,
        "polygon": [
            [380, 260],
            [900, 260],
            [960, 710],
            [320, 710]
        ],
        "frame_width": 1280,
        "frame_height": 720,
        "updated_at": None,
        "is_default": True
    }
