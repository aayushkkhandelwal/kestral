import cv2
import numpy as np
from typing import Dict, Any

class FaceQualityAssessor:
    """
    Evaluates multi-dimensional biometric and photographic quality indicators on face and subject crops.
    Factors include Laplacian sharpness variance, resolution fidelity, luminance balance, and contrast.
    """
    
    @staticmethod
    def assess_crop(crop_img: np.ndarray, has_real_face: bool = True) -> Dict[str, Any]:
        """
        Calculates quality metrics for a given image crop.
        
        Args:
            crop_img: BGR numpy image
            has_real_face: Whether a real face was verified by the neural network
        """
        if crop_img is None or crop_img.size == 0:
            return {
                "overall_score": 0.0,
                "grade": "INVALID",
                "sharpness": 0.0,
                "resolution_score": 0.0,
                "brightness_score": 0.0,
                "contrast_score": 0.0,
                "crop_dims": [0, 0],
                "has_real_face": False
            }

        h, w = crop_img.shape[:2]
        gray = cv2.cvtColor(crop_img, cv2.COLOR_BGR2GRAY)

        # 1. Sharpness via Variance of Laplacian
        laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        sharpness_norm = min(100.0, (laplacian_var / 350.0) ** 0.65 * 100.0)

        # 2. Resolution / Size Score
        pixel_count = h * w
        resolution_norm = min(100.0, (pixel_count / 30000.0) ** 0.5 * 100.0)

        # 3. Brightness / Luminance Balance
        mean_brightness = float(np.mean(gray))
        if mean_brightness < 40:
            brightness_norm = max(10.0, (mean_brightness / 40.0) * 40.0)
        elif mean_brightness > 220:
            brightness_norm = max(10.0, ((255 - mean_brightness) / 35.0) * 50.0)
        else:
            dist = abs(mean_brightness - 128.0)
            brightness_norm = max(20.0, 100.0 - (dist / 88.0) * 45.0)

        # 4. Contrast
        std_contrast = float(np.std(gray))
        contrast_norm = min(100.0, (std_contrast / 55.0) * 100.0)

        # 5. Composite Weighted Score
        composite = (
            sharpness_norm * 0.40 +
            resolution_norm * 0.30 +
            brightness_norm * 0.15 +
            contrast_norm * 0.15
        )

        if has_real_face:
            final_score = round(float(np.clip(composite, 0.0, 100.0)), 1)
            if final_score >= 82.0:
                grade = "EXCELLENT"
            elif final_score >= 65.0:
                grade = "GOOD"
            elif final_score >= 45.0:
                grade = "FAIR"
            else:
                grade = "LOW"
        else:
            # Face is not visible (back of head / turned away)
            # Cap score so it is never mistaken for a valid facial evidence capture
            final_score = round(float(np.clip(composite * 0.28, 5.0, 28.0)), 1)
            grade = "NOT_VISIBLE"

        return {
            "overall_score": final_score,
            "grade": grade,
            "has_real_face": has_real_face,
            "sharpness": round(laplacian_var, 1),
            "sharpness_normalized": round(sharpness_norm, 1),
            "resolution_score": round(resolution_norm, 1),
            "brightness": round(mean_brightness, 1),
            "brightness_score": round(brightness_norm, 1),
            "contrast": round(std_contrast, 1),
            "contrast_score": round(contrast_norm, 1),
            "crop_width": w,
            "crop_height": h
        }
