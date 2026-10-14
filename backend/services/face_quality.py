import cv2
import numpy as np
from typing import Dict, Any, List, Optional
import config

class FaceQualityAssessor:
    """
    Quality v2 Multi-dimensional Biometric Fidelity Assessment Engine.
    Evaluates:
      - Size-normalized Laplacian sharpness (normalized 112x112 resolution)
      - Physical face pixel resolution & aspect fidelity
      - Geometric pose proxy (yaw and pitch from 5 landmarks)
      - Photometric exposure & luminance clipping
      - Neural detector confidence
      - Automatic low-light CLAHE enhancement with flag detection
    """

    @staticmethod
    def deblur_and_sharpen_image(
        crop_img: np.ndarray,
        amount: float = config.DEBLUR_USM_AMOUNT,
        sigma: float = config.DEBLUR_USM_SIGMA
    ) -> np.ndarray:
        """
        Enhances blurry face images using dual-stage Unsharp Masking (USM)
        and edge-preserving bilateral smoothing to recover crisp facial contours.
        """
        if crop_img is None or crop_img.size == 0:
            return crop_img

        # 1. Bilateral filtering to preserve true edges while suppressing high-frequency sensor noise
        denoised = cv2.bilateralFilter(crop_img, d=5, sigmaColor=35, sigmaSpace=35)

        # 2. Gaussian blur for frequency separation
        blurred = cv2.GaussianBlur(denoised, (0, 0), sigmaX=sigma)

        # 3. Add weighted unsharp mask
        sharpened = cv2.addWeighted(denoised, 1.0 + amount, blurred, -amount, 0)

        # 4. Subtle high-pass detail boost for facial features (eyes, nose, mouth)
        kernel = np.array([
            [0, -0.25, 0],
            [-0.25, 2.0, -0.25],
            [0, -0.25, 0]
        ], dtype=np.float32)
        boosted = cv2.filter2D(sharpened, -1, kernel)

        # Blend to prevent harsh over-sharpening halos
        result = cv2.addWeighted(sharpened, 0.70, boosted, 0.30, 0)
        return np.clip(result, 0, 255).astype(np.uint8)

    @staticmethod
    def enhance_crop_if_needed(crop_img: np.ndarray, sharpness_norm: Optional[float] = None) -> (np.ndarray, bool):
        """
        Applies CLAHE for low-light crops AND adaptive deblurring for blurry crops.
        Returns (enhanced_crop, is_enhanced).
        """
        if crop_img is None or crop_img.size == 0:
            return crop_img, False

        enhanced = crop_img.copy()
        is_enhanced = False

        # 1. Low-light CLAHE
        lab = cv2.cvtColor(enhanced, cv2.COLOR_BGR2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)
        mean_l = float(np.mean(l_channel))

        if mean_l < config.CLAHE_LUMINANCE_THRESHOLD:
            clahe = cv2.createCLAHE(
                clipLimit=config.CLAHE_CLIP_LIMIT,
                tileGridSize=config.CLAHE_TILE_GRID_SIZE
            )
            l_enhanced = clahe.apply(l_channel)
            lab_enhanced = cv2.merge((l_enhanced, a_channel, b_channel))
            enhanced = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)
            is_enhanced = True

        # 2. Deblurring if sharpness is below threshold
        norm_sharp = sharpness_norm
        if norm_sharp is None:
            norm_rz = cv2.resize(crop_img, (112, 112))
            gray = cv2.cvtColor(norm_rz, cv2.COLOR_BGR2GRAY)
            lap = cv2.Laplacian(gray, cv2.CV_64F).var()
            norm_sharp = round(min(100.0, (lap / config.SHARPNESS_REFERENCE) * 100.0), 1)

        if norm_sharp < config.DEBLUR_BLUR_THRESHOLD:
            enhanced = FaceQualityAssessor.deblur_and_sharpen_image(enhanced)
            is_enhanced = True

        return enhanced, is_enhanced

    @staticmethod
    def assess_crop(
        crop_img: np.ndarray,
        has_real_face: bool = True,
        landmarks: Optional[List[List[int]]] = None,
        detector_conf: float = 0.50
    ) -> Dict[str, Any]:
        """
        Calculates Quality v2 metrics for a given face/head crop.
        """
        if crop_img is None or crop_img.size == 0:
            return {
                "overall_score": 0.0,
                "grade": "INVALID",
                "has_real_face": False,
                "sharpness": 0.0,
                "sharpness_normalized": 0.0,
                "resolution_score": 0.0,
                "brightness": 0.0,
                "brightness_score": 0.0,
                "contrast": 0.0,
                "contrast_score": 0.0,
                "crop_width": 0,
                "crop_height": 0,
                "size_score": 0.0,
                "pose_score": 0.0,
                "yaw_proxy": 0.0,
                "pitch_proxy": 0.0,
                "exposure_score": 0.0,
                "enhanced": False,
                "flags": ["no_face"]
            }

        # Check and apply CLAHE enhancement for dark footage
        enhanced_img, was_enhanced = FaceQualityAssessor.enhance_crop_if_needed(crop_img)
        work_img = enhanced_img

        h, w = work_img.shape[:2]
        gray = cv2.cvtColor(work_img, cv2.COLOR_BGR2GRAY)
        flags: List[str] = []

        if was_enhanced:
            flags.append("enhanced")

        # 1. Size-Normalized Sharpness
        # Resize to standard 112x112 so sharpness is invariant to sensor/crop scale
        try:
            gray_112 = cv2.resize(gray, (112, 112), interpolation=cv2.INTER_AREA)
            raw_laplacian_var = float(cv2.Laplacian(gray_112, cv2.CV_64F).var())
        except Exception:
            raw_laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())

        sharpness_norm = min(1.0, max(0.0, (raw_laplacian_var / config.SHARPNESS_REFERENCE) ** 0.70))
        if sharpness_norm < 0.25:
            flags.append("blurry")

        # 2. Size / Resolution Score
        size_norm = min(1.0, max(0.0, h / config.SIZE_REFERENCE_HEIGHT))
        if h < config.MIN_FACE_HEIGHT_PIXELS:
            flags.append("low_res")
            size_norm *= 0.50

        # 3. Geometric Pose Proxy from Landmarks
        yaw_proxy = 0.0
        pitch_proxy = 0.0
        pose_norm = 1.0

        if landmarks and len(landmarks) >= 5 and has_real_face:
            try:
                # landmarks: 0=right_eye, 1=left_eye, 2=nose, 3=right_mouth, 4=left_mouth
                r_eye = np.array(landmarks[0], dtype=float)
                l_eye = np.array(landmarks[1], dtype=float)
                nose = np.array(landmarks[2], dtype=float)
                r_mouth = np.array(landmarks[3], dtype=float)
                l_mouth = np.array(landmarks[4], dtype=float)

                eye_mid = (r_eye + l_eye) / 2.0
                mouth_mid = (r_mouth + l_mouth) / 2.0
                inter_eye_dist = max(1.0, float(np.linalg.norm(l_eye - r_eye)))
                face_vert_span = max(1.0, float(np.linalg.norm(mouth_mid - eye_mid)))

                # Yaw proxy: distance of nose from eye midpoint normalized by inter-eye distance
                yaw_proxy = float((nose[0] - eye_mid[0]) / inter_eye_dist)

                # Pitch proxy: vertical placement of nose between eye line and mouth line
                pitch_proxy = float((nose[1] - eye_mid[1]) / face_vert_span - 0.50)

                # Penalize severe lateral turn or extreme tilt
                abs_yaw = abs(yaw_proxy)
                abs_pitch = abs(pitch_proxy)

                if abs_yaw > 0.35:
                    flags.append("side_pose")

                pose_penalty = min(1.0, (abs_yaw * 1.6) + (abs_pitch * 0.9))
                pose_norm = max(0.0, 1.0 - pose_penalty)
            except Exception:
                pose_norm = 0.70
        else:
            if not has_real_face:
                pose_norm = 0.15
                flags.append("no_face")
            else:
                pose_norm = 0.65

        # 4. Exposure & Luminance Balance
        mean_brightness = float(np.mean(gray))
        if mean_brightness < 45.0:
            flags.append("dim")

        # Distance from ideal photographic midtone (128)
        lum_dist = abs(mean_brightness - 128.0) / 128.0
        # Check clipped underexposed (<15) or overexposed (>240) pixels
        clipped_ratio = float(np.sum((gray < 15) | (gray > 240))) / max(1, (h * w))
        exposure_norm = max(0.0, min(1.0, 1.0 - (lum_dist * 0.65 + clipped_ratio * 1.5)))

        # 5. Contrast & Photometric Standard Deviation
        std_contrast = float(np.std(gray))
        contrast_norm = min(1.0, max(0.0, std_contrast / 55.0))

        # 6. Detector Confidence
        conf_norm = min(1.0, max(0.0, float(detector_conf)))

        # 7. Composite Weighted Score (0..100)
        composite = (
            sharpness_norm * config.QUALITY_WEIGHT_SHARPNESS +
            size_norm * config.QUALITY_WEIGHT_SIZE +
            pose_norm * config.QUALITY_WEIGHT_POSE +
            exposure_norm * config.QUALITY_WEIGHT_EXPOSURE +
            conf_norm * config.QUALITY_WEIGHT_CONFIDENCE
        ) * 100.0

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
            final_score = round(float(np.clip(composite * 0.25, 5.0, 25.0)), 1)
            grade = "NOT_VISIBLE"

        return {
            # Existing keys (Additive only - keep backwards compatibility)
            "overall_score": final_score,
            "grade": grade,
            "has_real_face": has_real_face,
            "sharpness": round(raw_laplacian_var, 1),
            "sharpness_normalized": round(sharpness_norm * 100.0, 1),
            "resolution_score": round(size_norm * 100.0, 1),
            "brightness": round(mean_brightness, 1),
            "brightness_score": round(exposure_norm * 100.0, 1),
            "contrast": round(std_contrast, 1),
            "contrast_score": round(contrast_norm * 100.0, 1),
            "crop_width": w,
            "crop_height": h,
            # New keys per CONTRACTS section B
            "size_score": round(size_norm * 100.0, 1),
            "pose_score": round(pose_norm * 100.0, 1),
            "yaw_proxy": round(yaw_proxy, 3),
            "pitch_proxy": round(pitch_proxy, 3),
            "exposure_score": round(exposure_norm * 100.0, 1),
            "enhanced": was_enhanced,
            "flags": flags
        }
