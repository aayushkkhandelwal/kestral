import cv2
import os
import json
from services.identity_consolidator import IdentityConsolidator

c = IdentityConsolidator()
tracks_dir = os.path.join(os.path.dirname(__file__), "results", "fefab3ed")
json_path = os.path.join(tracks_dir, "results.json")

with open(json_path, "r", encoding="utf-8") as f:
    res = json.load(f)

tracks = res["tracks"]
print(f"Total tracks in fefab3ed: {len(tracks)}")

for i in range(len(tracks)):
    for j in range(i + 1, len(tracks)):
        t1 = tracks[i]
        t2 = tracks[j]
        id1 = t1["track_id"]
        id2 = t2["track_id"]

        f1 = cv2.imread(os.path.join(tracks_dir, f"track_{id1}_face.jpg"))
        f2 = cv2.imread(os.path.join(tracks_dir, f"track_{id2}_face.jpg"))
        full1 = cv2.imread(os.path.join(tracks_dir, f"track_{id1}_full.jpg"))
        full2 = cv2.imread(os.path.join(tracks_dir, f"track_{id2}_full.jpg"))

        d1 = {
            "first_seen_time": t1["first_seen_time"],
            "last_seen_time": t1["last_seen_time"],
            "best_full_frame": full1,
            "best_person_bbox": t1["person_bbox"],
            "best_face_crop": f1,
            "best_has_real_face": t1.get("has_real_face", False)
        }
        d2 = {
            "first_seen_time": t2["first_seen_time"],
            "last_seen_time": t2["last_seen_time"],
            "best_full_frame": full2,
            "best_person_bbox": t2["person_bbox"],
            "best_face_crop": f2,
            "best_has_real_face": t2.get("has_real_face", False)
        }

        # Check temporal overlap
        start1, end1 = d1["first_seen_time"], d1["last_seen_time"]
        start2, end2 = d2["first_seen_time"], d2["last_seen_time"]
        overlap = min(end1, end2) - max(start1, start2)

        # Check clothing similarity
        h1 = c._extract_clothing_hist(full1, t1["person_bbox"])
        h2 = c._extract_clothing_hist(full2, t2["person_bbox"])
        cloth_sim = 0.0
        if h1 is not None and h2 is not None:
            cloth_sim = max(0.0, 1.0 - float(cv2.compareHist(h1, h2, cv2.HISTCMP_BHATTACHARYYA)))

        # Check face similarity
        face_sim = 0.0
        if f1 is not None and f2 is not None and d1["best_has_real_face"] and d2["best_has_real_face"]:
            sig1 = c._extract_face_signature(f1)
            sig2 = c._extract_face_signature(f2)
            if sig1 and sig2:
                f_bhatt = cv2.compareHist(sig1[0], sig2[0], cv2.HISTCMP_BHATTACHARYYA)
                f_col = max(0.0, 1.0 - float(f_bhatt))
                f_struct = float(np.dot(sig1[1], sig2[1]))
                face_sim = 0.5 * f_col + 0.5 * max(0.0, f_struct)

        is_match, score, reason = c._compare_appearance(d1, d2)
        print(f"Compare #{id1} & #{id2} (overlap={overlap:.1f}s): cloth={cloth_sim:.2f}, face={face_sim:.2f} => match={is_match}, reason={reason}")
