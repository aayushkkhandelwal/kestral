"""
Biometric Face Search Router
Performs 128-dimensional cosine feature similarity matching across all historical evidence archives.
Mandatory note: Output indicates visual similarity only and requires human verification.
"""
import os
import json
from typing import List, Dict, Any, Optional
import cv2
import numpy as np
from fastapi import APIRouter, UploadFile, File, Query, HTTPException, Header

import config
import db
from services.face_detector import FaceDetector

router = APIRouter(prefix="/api/search", tags=["Biometric Face Search"])

_SEARCH_FACE_DETECTOR: Optional[FaceDetector] = None

def get_search_detector() -> FaceDetector:
    global _SEARCH_FACE_DETECTOR
    if _SEARCH_FACE_DETECTOR is None:
        _SEARCH_FACE_DETECTOR = FaceDetector()
    return _SEARCH_FACE_DETECTOR

def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(np.dot(v1, v2) / (norm1 * norm2))

@router.post("/face")
async def search_face_similarity(
    file: UploadFile = File(...),
    top_k: int = Query(default=5, ge=1, le=20),
    x_user: str = Header(default="investigator")
):
    """
    Compares probe facial image against all indexed evidence tracks using SFace feature vectors.
    Returns ranked candidate list with similarity scores.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Empty image upload")

    contents = await file.read()
    np_arr = np.frombuffer(contents, np.uint8)
    probe_img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if probe_img is None or probe_img.size == 0:
        raise HTTPException(status_code=400, detail="Could not decode uploaded probe image")

    detector = get_search_detector()
    h, w = probe_img.shape[:2]

    # Extract probe face embedding
    probe_emb: Optional[np.ndarray] = None

    # 1. Try detecting face with YuNet
    face_info = detector.detect_face_in_person(probe_img, [0, 0, w, h])
    if face_info and face_info.get("embedding"):
        probe_emb = np.array(face_info["embedding"], dtype=np.float32)

    # 2. If already a cropped face, extract feature directly
    if probe_emb is None and detector.sface is not None:
        try:
            resized_probe = cv2.resize(probe_img, (112, 112))
            feat = detector.sface.feature(resized_probe)
            norm = np.linalg.norm(feat)
            if norm > 0:
                probe_emb = (feat / norm).flatten()
        except Exception:
            pass

    # 3. If SFace is unavailable or failed, fallback to color-spatial feature vector
    if probe_emb is None:
        resized_probe = cv2.resize(probe_img, (64, 64))
        probe_emb = cv2.cvtColor(resized_probe, cv2.COLOR_BGR2GRAY).flatten().astype(np.float32)
        probe_emb /= max(1.0, np.linalg.norm(probe_emb))

    candidates: List[Dict[str, Any]] = []

    # Iterate through all task results in RESULTS_DIR
    if os.path.exists(config.RESULTS_DIR):
        for task_id in os.listdir(config.RESULTS_DIR):
            task_dir = os.path.join(config.RESULTS_DIR, task_id)
            if not os.path.isdir(task_dir):
                continue

            results_json = os.path.join(task_dir, "results.json")
            embeddings_json = os.path.join(task_dir, "embeddings.json")

            if not os.path.exists(results_json):
                continue

            try:
                with open(results_json, "r") as f:
                    res_data = json.load(f)
            except Exception:
                continue

            # Load saved embeddings if present
            task_embeddings: Dict[str, List[float]] = {}
            if os.path.exists(embeddings_json):
                try:
                    with open(embeddings_json, "r") as f:
                        task_embeddings = json.load(f)
                except Exception:
                    pass

            for track in res_data.get("tracks", []):
                tid = track.get("track_id")
                face_url = track.get("face_image_url")
                crop_filename = f"track_{tid}_face.jpg"
                crop_path = os.path.join(task_dir, crop_filename)

                cand_emb: Optional[np.ndarray] = None

                # Check precomputed embeddings
                str_tid = str(tid)
                if str_tid in task_embeddings:
                    cand_emb = np.array(task_embeddings[str_tid], dtype=np.float32)
                elif os.path.exists(crop_path):
                    cand_img = cv2.imread(crop_path)
                    if cand_img is not None and cand_img.size > 0:
                        if detector.sface is not None:
                            try:
                                rz = cv2.resize(cand_img, (112, 112))
                                feat = detector.sface.feature(rz)
                                norm = np.linalg.norm(feat)
                                if norm > 0:
                                    cand_emb = (feat / norm).flatten()
                            except Exception:
                                pass
                        if cand_emb is None:
                            rz = cv2.resize(cand_img, (64, 64))
                            cand_emb = cv2.cvtColor(rz, cv2.COLOR_BGR2GRAY).flatten().astype(np.float32)
                            cand_emb /= max(1.0, np.linalg.norm(cand_emb))

                if cand_emb is not None and len(cand_emb) == len(probe_emb):
                    sim = cosine_similarity(probe_emb, cand_emb)
                    # Normalize cosine sim to 0..1 scale
                    norm_sim = round(max(0.0, min(1.0, (sim + 1.0) / 2.0 if sim < 1.0 else sim)), 3)
                    candidates.append({
                        "task_id": task_id,
                        "track_id": tid,
                        "similarity": norm_sim,
                        "face_image_url": face_url,
                        "quality_score": track.get("best_score", 0.0),
                        "timestamp": track.get("best_timestamp", 0.0),
                        "note": "similarity only; needs human review"
                    })

    # Sort descending by similarity
    candidates.sort(key=lambda x: x["similarity"], reverse=True)
    top_matches = candidates[:top_k]

    db.log_audit(
        username=x_user,
        role="investigator",
        action="FACE_SEARCH",
        detail=f"Searched probe image ({file.filename}) against evidence archive; returned {len(top_matches)} matches"
    )

    return top_matches
