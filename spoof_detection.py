import os
import cv2
import numpy as np
from anti_spoof_predict import AntiSpoofPredict
from src.utility import parse_model_name
MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
REAL_THRESHOLD = 0.75

class SpoofDetector:
    def __init__(self):
        self.predictor = AntiSpoofPredict(device_id=0)

        self.model_paths = [
            os.path.join(MODEL_DIR, f)
            for f in os.listdir(MODEL_DIR)
            if f.endswith(".pth")
        ]

        if not self.model_paths:
            raise FileNotFoundError(
                f"No .pth model files found in '{MODEL_DIR}'. "
                "Download them from the Silent-Face-Anti-Spoofing repo."
            )

        print(f"SpoofDetector: using {len(self.model_paths)} model(s): {self.model_paths}")

    def _crop_face(self, frame: np.ndarray, bbox: tuple, target_size: tuple) -> np.ndarray:
        """
        Crop face with a margin (same as the original library does) then resize to the model's expected input size.
        """
        x1, y1, x2, y2 = bbox
        h, w = frame.shape[:2]

        face_w = x2 - x1
        face_h = y2 - y1
        margin_x = int(face_w * 0.3)
        margin_y = int(face_h * 0.3)

        x1 = max(0, x1 - margin_x)
        y1 = max(0, y1 - margin_y)
        x2 = min(w, x2 + margin_x)
        y2 = min(h, y2 + margin_y)

        face_crop = frame[y1:y2, x1:x2]

        if face_crop.size == 0:
            return None

        tw, th = target_size
        face_crop = cv2.resize(face_crop, (tw, th))
        return face_crop

    def check(self, frame: np.ndarray, bbox: tuple) -> bool:
        """
        Returns True if REAL, False if SPOOF.
        bbox: (x1, y1, x2, y2)
        """
        real_score  = 0.0
        spoof_score = 0.0
        count       = 0

        for model_path in self.model_paths:
            model_name = os.path.basename(model_path)
            try:
                h_in, w_in, _, _ = parse_model_name(model_name)
            except Exception:
                print(f"  WARNING: could not parse model name '{model_name}', skipping")
                continue

            face = self._crop_face(frame, bbox, (w_in, h_in))
            if face is None:
                continue

            try:
                result = self.predictor.predict(face, model_path)
                real_score  += result[0][1]
                spoof_score += result[0][0]
                count += 1
            except Exception as e:
                print(f"  WARNING: prediction failed for '{model_name}': {e}")
                continue

        if count == 0:
            raise RuntimeError("Spoof detection failed — no models could process the frame.")

        real_score  /= count
        spoof_score /= count

        print(f"Spoof check — real: {real_score:.3f}  spoof: {spoof_score:.3f}  "
              f"→ {'REAL' if real_score >= REAL_THRESHOLD else 'SPOOF'}")

        return real_score >= REAL_THRESHOLD