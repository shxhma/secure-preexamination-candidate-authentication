import os
import cv2
import numpy as np
from insightface.app import FaceAnalysis

class PhotoValidator:
    MAX_FILE_SIZE_KB = 500

    def __init__(self):
        self.app = FaceAnalysis(name="buffalo_l")
        self.app.prepare(ctx_id=-1, det_size=(640,640))

    def validate(self, photo_path):

        # ---- FILE SIZE CHECK ----
        size = os.path.getsize(photo_path)

        if size > self.MAX_FILE_SIZE_KB * 1024:
            raise ValueError("Photo must be less than 500KB")

        # ---- LOAD IMAGE ----
        img = cv2.imread(photo_path)

        if img is None:
            raise ValueError("Invalid image file")

        # ---- FACE DETECTION ----
        faces = self.app.get(img)

        if len(faces) == 0:
            raise ValueError("No face detected")

        if len(faces) > 1:
            raise ValueError("Multiple faces detected")

        face = faces[0]

        # ---- STRONG HUMAN FILTER (embedding quality) ----
        embedding_norm = np.linalg.norm(face.embedding)

        if embedding_norm < 15:
            raise ValueError("Possible cartoon or fake image detected")

        # ---- DETECTION CONFIDENCE ----
        if face.det_score < 0.7:
            raise ValueError("Face confidence too low")

        return face