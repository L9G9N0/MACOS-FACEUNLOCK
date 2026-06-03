import os
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

class FASEstimator:
    def __init__(self):
        print("[SYSTEM] Booting Active FSM (Tasks API 3D Geometry)...")
        self.model_path = os.path.join(os.path.dirname(__file__), "face_landmarker.task")
        
        if not os.path.exists(self.model_path):
            raise FileNotFoundError("[FATAL ERROR] Model missing! Run the curl command to download face_landmarker.task")

        # Native M1 Tasks API Setup (Identical to our FaceDetector)
        base_options = python.BaseOptions(model_asset_path=self.model_path)
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            output_facial_transformation_matrixes=True, # MAGIC FLAG: Directly outputs 3D OS-level matrix
            num_faces=1
        )
        self.landmarker = vision.FaceLandmarker.create_from_options(options)
        
        # FSM States
        self.challenge_completed = False
        self.required_angle = 12  # Degrees to turn (Left or Right)

    def get_head_yaw(self, frame):
        """Calculates Head Yaw using the 4x4 Transformation Matrix."""
        # Tasks API requires RGB Mediapipe Image format
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        result = self.landmarker.detect(mp_image)
        
        if not result.facial_transformation_matrixes:
            return None
            
        # Extract the 4x4 Pose Matrix
        matrix = result.facial_transformation_matrixes[0]
        rot_matrix = matrix[:3, :3] # Isolate the 3x3 Rotation matrix
        
        # Decompose matrix to Euler Angles (Degrees)
        angles, _, _, _, _, _ = cv2.RQDecomp3x3(rot_matrix)
        yaw = angles[1] 
        return yaw

    def check_liveness(self, frame, bbox):
        """Active Challenge-Response System."""
        yaw = self.get_head_yaw(frame)
        
        if yaw is None:
            return False, 0.0, "NO FACE"

        # FSM State Transitions
        # If absolute yaw crosses the threshold, user turned their head successfully
        if abs(yaw) > self.required_angle:
            self.challenge_completed = True
            
        if not self.challenge_completed:
            return False, yaw, "TURN HEAD (LEFT OR RIGHT)"
        else:
            # Challenge passed, now ensure they are looking back at the screen
            if abs(yaw) < 8: 
                return True, yaw, "LIVE (AUTH PASSED)"
            else:
                return False, yaw, "LOOK AT SCREEN"