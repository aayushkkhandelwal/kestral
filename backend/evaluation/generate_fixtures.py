"""
Generates reproducible, labeled evaluation video fixtures with exact ground-truth bounding box annotations.
Creates:
1. crossing_paths.mp4 & annotations/crossing_paths.json
2. disappear_reappear.mp4 & annotations/disappear_reappear.json
3. low_light_blur.mp4 & annotations/low_light_blur.json
"""

import os
import json
import cv2
import numpy as np

BASE_EVAL_DIR = os.path.dirname(os.path.abspath(__file__))
FIXTURES_DIR = os.path.join(BASE_EVAL_DIR, "fixtures")
ANNOTATIONS_DIR = os.path.join(BASE_EVAL_DIR, "annotations")
os.makedirs(FIXTURES_DIR, exist_ok=True)
os.makedirs(ANNOTATIONS_DIR, exist_ok=True)

def draw_person_avatar(frame, cx, cy, scale=1.0, light_factor=1.0, blur=False):
    """Draws a standardized human silhouette with head and shoulders for testing."""
    h, w = frame.shape[:2]
    pw = int(60 * scale)
    ph = int(140 * scale)

    x1 = max(0, cx - pw // 2)
    y1 = max(0, cy - ph // 2)
    x2 = min(w, cx + pw // 2)
    y2 = min(h, cy + ph // 2)

    body_color = (int(160 * light_factor), int(120 * light_factor), int(90 * light_factor))
    head_color = (int(210 * light_factor), int(180 * light_factor), int(150 * light_factor))

    # Body
    cv2.ellipse(frame, (cx, cy + int(20 * scale)), (int(pw * 0.45), int(ph * 0.35)), 0, 0, 360, body_color, -1)
    # Head
    head_cy = y1 + int(28 * scale)
    head_r = int(22 * scale)
    cv2.circle(frame, (cx, head_cy), head_r, head_color, -1)

    # Facial features (eyes, mouth)
    eye_color = (int(40 * light_factor), int(30 * light_factor), int(20 * light_factor))
    cv2.circle(frame, (cx - int(7 * scale), head_cy - int(3 * scale)), int(3 * scale), eye_color, -1)
    cv2.circle(frame, (cx + int(7 * scale), head_cy - int(3 * scale)), int(3 * scale), eye_color, -1)
    cv2.line(frame, (cx - int(6 * scale), head_cy + int(8 * scale)), (cx + int(6 * scale), head_cy + int(8 * scale)), eye_color, int(2 * scale))

    face_bbox = [cx - head_r, head_cy - head_r, cx + head_r, head_cy + head_r]
    person_bbox = [x1, y1, x2, y2]

    if blur:
        sub = frame[y1:y2, x1:x2]
        if sub.size > 0:
            frame[y1:y2, x1:x2] = cv2.GaussianBlur(sub, (15, 15), 0)

    return person_bbox, face_bbox

def generate_crossing_paths():
    """Two people walking in opposite directions and crossing paths at center."""
    video_path = os.path.join(FIXTURES_DIR, "crossing_paths.mp4")
    annot_path = os.path.join(ANNOTATIONS_DIR, "crossing_paths.json")

    w, h = 480, 360
    fps = 10.0
    num_frames = 30
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(video_path, fourcc, fps, (w, h))

    frames_annot = []

    for i in range(num_frames):
        frame = np.ones((h, w, 3), dtype=np.uint8) * 45
        # Background lines to simulate floor tiles
        for y in range(0, h, 60):
            cv2.line(frame, (0, y), (w, y), (60, 60, 60), 1)

        # Person 1 moving left to right
        p1_x = int(60 + (i / (num_frames - 1)) * 360)
        p1_y = 180
        p1_box, p1_face = draw_person_avatar(frame, p1_x, p1_y, scale=1.0)

        # Person 2 moving right to left
        p2_x = int(420 - (i / (num_frames - 1)) * 360)
        p2_y = 190
        p2_box, p2_face = draw_person_avatar(frame, p2_x, p2_y, scale=1.05)

        out.write(frame)

        frames_annot.append({
            "frame_idx": i,
            "timestamp_sec": round(i / fps, 2),
            "ground_truths": [
                {
                    "track_id": 1,
                    "bbox": p1_box,
                    "has_face": True,
                    "face_bbox": p1_face
                },
                {
                    "track_id": 2,
                    "bbox": p2_box,
                    "has_face": True,
                    "face_bbox": p2_face
                }
            ]
        })

    out.release()
    with open(annot_path, "w") as f:
        json.dump({"video_id": "BENCH_CROSSING_03", "resolution": [w, h], "frames": frames_annot}, f, indent=2)

def generate_disappear_reappear():
    """Person moves across, disappears behind an obstruction for 1 second, then re-emerges."""
    video_path = os.path.join(FIXTURES_DIR, "disappear_reappear.mp4")
    annot_path = os.path.join(ANNOTATIONS_DIR, "disappear_reappear.json")

    w, h = 480, 360
    fps = 10.0
    num_frames = 40
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(video_path, fourcc, fps, (w, h))

    frames_annot = []

    for i in range(num_frames):
        frame = np.ones((h, w, 3), dtype=np.uint8) * 40

        # Person disappears between frame 15 and 25 (1.0 second gap)
        is_visible = (i < 15 or i >= 25)
        gts = []

        if is_visible:
            px = int(80 + (i / (num_frames - 1)) * 320)
            py = 180
            p_box, p_face = draw_person_avatar(frame, px, py, scale=1.0)
            gts.append({
                "track_id": 1,
                "bbox": p_box,
                "has_face": True,
                "face_bbox": p_face
            })

        # Draw a pillar / obstruction at center
        cv2.rectangle(frame, (200, 40), (280, 340), (20, 20, 20), -1)
        cv2.rectangle(frame, (200, 40), (280, 340), (80, 80, 80), 2)

        out.write(frame)

        frames_annot.append({
            "frame_idx": i,
            "timestamp_sec": round(i / fps, 2),
            "ground_truths": gts
        })

    out.release()
    with open(annot_path, "w") as f:
        json.dump({"video_id": "BENCH_DISAPPEAR_04", "resolution": [w, h], "frames": frames_annot}, f, indent=2)

def generate_low_light_blur():
    """Person with varying illumination and motion blur to evaluate quality scoring and selection."""
    video_path = os.path.join(FIXTURES_DIR, "low_light_blur.mp4")
    annot_path = os.path.join(ANNOTATIONS_DIR, "low_light_blur.json")

    w, h = 480, 360
    fps = 10.0
    num_frames = 30
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(video_path, fourcc, fps, (w, h))

    frames_annot = []

    for i in range(num_frames):
        frame = np.ones((h, w, 3), dtype=np.uint8) * 15 # Very low light base

        # Middle frames have clear light, outer frames are dark and blurry
        if 12 <= i <= 18:
            light = 1.0 # Optimal well-lit face
            blur = False
            best_candidate = True
        elif i < 8:
            light = 0.25 # Under-exposed
            blur = True
            best_candidate = False
        else:
            light = 0.55
            blur = False
            best_candidate = False

        px = 240
        py = 180
        p_box, p_face = draw_person_avatar(frame, px, py, scale=1.1, light_factor=light, blur=blur)

        out.write(frame)

        frames_annot.append({
            "frame_idx": i,
            "timestamp_sec": round(i / fps, 2),
            "ground_truths": [
                {
                    "track_id": 1,
                    "bbox": p_box,
                    "has_face": True,
                    "face_bbox": p_face,
                    "is_optimal_evidence_candidate": best_candidate
                }
            ]
        })

    out.release()
    with open(annot_path, "w") as f:
        json.dump({"video_id": "BENCH_LOWLIGHT_05", "resolution": [w, h], "frames": frames_annot}, f, indent=2)

if __name__ == "__main__":
    generate_crossing_paths()
    generate_disappear_reappear()
    generate_low_light_blur()
    print("Benchmark video fixtures and ground truth annotations generated successfully!")
