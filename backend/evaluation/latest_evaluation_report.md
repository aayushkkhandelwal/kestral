# Kestral AI — Model Performance & Evaluation Report

**Generated:** 2026-10-14T14:24:45.877990Z  
**Report ID:** `EVAL-1791987885`  
**Total Benchmark Duration:** 22.66s  

## 1. Person Detection Accuracy (IoU 0.50, Conf 0.35)

| Metric | Value |
| :--- | :--- |
| **Precision** | 100.0% |
| **Recall** | 6.7% |
| **F1-Score** | 12.5% |
| **mAP@0.50** | 6.7% |
| True Positives | 8 |
| False Positives | 0 |
| False Negatives | 112 |

### Performance by Condition

| Condition | Precision | Recall | F1-Score | mAP@0.50 |
| :--- | :---: | :---: | :---: | :---: |
| `people_crossing_paths` | 0.0% | 0.0% | 0.0% | 0.0% |
| `temporary_disappearance` | 0.0% | 0.0% | 0.0% | 0.0% |
| `low_light_and_motion_blur` | 100.0% | 26.7% | 42.1% | 26.7% |

## 2. Tracking Stability (ByteTrack)

- **Ground Truth Identities:** 3
- **Predicted Tracks:** 0
- **Total ID Switches:** 0
- **Track Fragmentations:** 0
- **ID Switch Rate:** 0.0 per identity

## 3. Face Detection & Best-Frame Extraction

- **Face Detection Precision:** 100.0%
- **Face Detection Recall:** 26.7%
- **Best-Frame Accuracy:** 100.0%
- **Usable Evidence Fraction:** 1/1
