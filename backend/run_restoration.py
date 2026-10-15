import os
import cv2
import shutil
import sys
sys.path.insert(0, ".")

from services.image_enhancer import ForensicImageEnhancer

enhancer = ForensicImageEnhancer(
    clahe_clip_limit=1.25,
    sharpen_amount=0.65,
    sharpen_sigma=1.4,
    edge_threshold=12.0
)

results_dir = r"results/74d46b67"
artifact_dir = r"C:\Users\aayus\.gemini\antigravity-ide\brain\eece9790-eaf7-463f-8059-2778d3b7026b"

targets = [
    {
        "id": 20,
        "name": "Subject #20 — Female with Eyeglasses",
        "file": "track_20_face.jpg"
    },
    {
        "id": 21,
        "name": "Subject #21 — Male (Downward Angle)",
        "file": "track_21_face.jpg"
    },
    {
        "id": 22,
        "name": "Subject #22 — Male with Beard",
        "file": "track_22_face.jpg"
    }
]

for t in targets:
    file_name = str(t["file"])
    title_name = str(t["name"])
    target_id = t["id"]

    src_path = os.path.join(results_dir, file_name)
    if not os.path.exists(src_path):
        print(f"Warning: {src_path} not found")
        continue

    orig = cv2.imread(src_path)
    if orig is None:
        print(f"Warning: could not read {src_path}")
        continue

    enhanced = enhancer.enhance_face_crop(orig)

    # Save enhanced image in results
    out_enhanced_path = os.path.join(results_dir, f"enhanced_{file_name}")
    cv2.imwrite(out_enhanced_path, enhanced, [cv2.IMWRITE_JPEG_QUALITY, 98])

    # Create comparison panel
    panel = enhancer.create_comparison_panel(
        orig,
        enhanced,
        title=title_name,
        scale_display=2
    )

    out_panel_path = os.path.join(results_dir, f"comparison_subject_{target_id}.png")
    cv2.imwrite(out_panel_path, panel)

    # Copy to artifacts directory for visual embedding
    artifact_panel = os.path.join(artifact_dir, f"comparison_subject_{target_id}.png")
    artifact_enhanced = os.path.join(artifact_dir, f"enhanced_subject_{target_id}.jpg")
    artifact_orig = os.path.join(artifact_dir, f"original_subject_{target_id}.jpg")

    shutil.copyfile(out_panel_path, artifact_panel)
    shutil.copyfile(out_enhanced_path, artifact_enhanced)
    shutil.copyfile(src_path, artifact_orig)

    orig_var = cv2.Laplacian(cv2.cvtColor(orig, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var()
    enh_var = cv2.Laplacian(cv2.cvtColor(enhanced, cv2.COLOR_BGR2GRAY), cv2.CV_64F).var()
    print(f"Restored {t['name']}: Sharpness {orig_var:.1f} -> {enh_var:.1f} (+{((enh_var-orig_var)/orig_var)*100:.1f}%)")
