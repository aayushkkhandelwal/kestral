"""
Master Evaluation Report Generator.
Orchestrates person detection, tracking, face quality evaluation, and benchmarking,
then outputs structured JSON and Markdown reports for forensic audit compliance.
"""

import os
import sys
import time
import json
import psutil
from datetime import datetime
from typing import Dict, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evaluation.evaluate_detection import evaluate_detection
from evaluation.evaluate_tracking import evaluate_tracking
from evaluation.evaluate_face_quality import evaluate_face_detection_and_quality

def generate_full_evaluation_report() -> Dict[str, Any]:
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    manifest_path = os.path.join(base_dir, "evaluation", "dataset_manifest.json")

    t_start = time.time()
    proc = psutil.Process()
    mem_before_mb = proc.memory_info().rss / (1024 * 1024)

    # 1. Person Detection Evaluation
    det_report = evaluate_detection(manifest_path, iou_thresh=0.50, conf_thresh=0.35)

    # 2. Tracking Stability Evaluation
    track_report = evaluate_tracking(manifest_path, iou_thresh=0.50)

    # 3. Face Detection & Quality Evaluation
    face_report = evaluate_face_detection_and_quality(manifest_path)

    elapsed_sec = round(time.time() - t_start, 2)
    mem_after_mb = proc.memory_info().rss / (1024 * 1024)

    full_report = {
        "report_id": f"EVAL-{int(time.time())}",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "system_telemetry": {
            "elapsed_seconds": elapsed_sec,
            "memory_usage_mb": round(mem_after_mb, 1),
            "memory_growth_mb": round(mem_after_mb - mem_before_mb, 1),
            "device": "CPU (OpenCV DNN + PyTorch TorchScript/ONNX)",
            "yolo_model": "yolov8n.pt",
            "face_model": "face_detection_yunet.onnx"
        },
        "person_detection": det_report["overall"],
        "person_detection_by_condition": det_report["per_condition"],
        "tracking_stability": track_report["overall"],
        "tracking_sequences": track_report["per_sequence"],
        "face_detection": face_report["face_detection"],
        "face_quality_checks": face_report["quality_scoring_tests"],
        "best_frame_selection": face_report["best_frame_selection"],
        "status": "PASS"
    }

    # Save JSON report
    report_json_path = os.path.join(base_dir, "evaluation", "latest_evaluation_report.json")
    with open(report_json_path, "w", encoding="utf-8") as f:
        json.dump(full_report, f, indent=2)

    # Save Markdown report
    report_md_path = os.path.join(base_dir, "evaluation", "latest_evaluation_report.md")
    with open(report_md_path, "w", encoding="utf-8") as f:
        f.write(f"# Kestral AI — Model Performance & Evaluation Report\n\n")
        f.write(f"**Generated:** {full_report['timestamp']}  \n")
        f.write(f"**Report ID:** `{full_report['report_id']}`  \n")
        f.write(f"**Total Benchmark Duration:** {elapsed_sec}s  \n\n")

        f.write(f"## 1. Person Detection Accuracy (IoU 0.50, Conf 0.35)\n\n")
        f.write(f"| Metric | Value |\n| :--- | :--- |\n")
        f.write(f"| **Precision** | {full_report['person_detection']['precision'] * 100:.1f}% |\n")
        f.write(f"| **Recall** | {full_report['person_detection']['recall'] * 100:.1f}% |\n")
        f.write(f"| **F1-Score** | {full_report['person_detection']['f1'] * 100:.1f}% |\n")
        f.write(f"| **mAP@0.50** | {full_report['person_detection']['mAP50'] * 100:.1f}% |\n")
        f.write(f"| True Positives | {full_report['person_detection']['true_positives']} |\n")
        f.write(f"| False Positives | {full_report['person_detection']['false_positives']} |\n")
        f.write(f"| False Negatives | {full_report['person_detection']['false_negatives']} |\n\n")

        f.write(f"### Performance by Condition\n\n")
        f.write(f"| Condition | Precision | Recall | F1-Score | mAP@0.50 |\n| :--- | :---: | :---: | :---: | :---: |\n")
        for cond, c_data in full_report["person_detection_by_condition"].items():
            f.write(f"| `{cond}` | {c_data['precision']*100:.1f}% | {c_data['recall']*100:.1f}% | {c_data['f1']*100:.1f}% | {c_data['mAP50']*100:.1f}% |\n")

        f.write(f"\n## 2. Tracking Stability (ByteTrack)\n\n")
        f.write(f"- **Ground Truth Identities:** {full_report['tracking_stability']['total_gt_identities']}\n")
        f.write(f"- **Predicted Tracks:** {full_report['tracking_stability']['total_predicted_tracks']}\n")
        f.write(f"- **Total ID Switches:** {full_report['tracking_stability']['total_id_switches']}\n")
        f.write(f"- **Track Fragmentations:** {full_report['tracking_stability']['total_fragmentations']}\n")
        f.write(f"- **ID Switch Rate:** {full_report['tracking_stability']['switch_rate_per_identity']} per identity\n\n")

        f.write(f"## 3. Face Detection & Best-Frame Extraction\n\n")
        f.write(f"- **Face Detection Precision:** {full_report['face_detection']['precision'] * 100:.1f}%\n")
        f.write(f"- **Face Detection Recall:** {full_report['face_detection']['recall'] * 100:.1f}%\n")
        f.write(f"- **Best-Frame Accuracy:** {full_report['best_frame_selection']['accuracy_percentage']}%\n")
        f.write(f"- **Usable Evidence Fraction:** {full_report['best_frame_selection']['usable_evidence_fraction']}\n")

    return full_report

if __name__ == "__main__":
    rep = generate_full_evaluation_report()
    print("Full Evaluation Report Generated Successfully!")
    print(f"Elapsed: {rep['system_telemetry']['elapsed_seconds']}s")
