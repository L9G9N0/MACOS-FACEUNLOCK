import os
import json
import cv2
import numpy as np
import face_recognition

class FaceRecognizer:
    def __init__(self):
        print("[SYSTEM] Booting Identity Verification (RAM Caching)...")
        self.profile_path = os.path.join(os.path.dirname(__file__), "hariom_profile.json")
        
        # 1. RAM CACHING: Read from Disk I/O only ONCE during initialization
        if not os.path.exists(self.profile_path):
            raise FileNotFoundError("[FATAL] Profile not found. Run encoder.py first.")
            
        with open(self.profile_path, "r") as f:
            # Load into RAM and convert back to a fast NumPy array
            self.master_vector = np.array(json.load(f))
            
        print("[SYSTEM] Master Profile loaded into RAM securely.")

    def verify_identity(self, frame, bbox):
        """Compares the real-time face with the RAM-cached master vector."""
        x, y, w, h = bbox
        
        # Optimization: Crop the frame so the ML model processes fewer pixels
        face_crop = frame[max(0, y):y+h, max(0, x):x+w]
        rgb_crop = cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB)
        
        # Generate 128-D vector for the current live frame
        encodings = face_recognition.face_encodings(rgb_crop)
        
        if len(encodings) == 0:
            return False, 1.0 # No face vectors found
            
        current_vector = encodings[0]
        
        # Euclidean Distance Math: Lower distance means a closer match.
        # Default is 0.6, but for enterprise security, we enforce a strict 0.45 limit
        distance = face_recognition.face_distance([self.master_vector], current_vector)[0]
        is_match = distance < 0.45 
        
        return bool(is_match), float(distance)