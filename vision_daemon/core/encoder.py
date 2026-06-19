import os
import cv2
import json
import argparse
import face_recognition
from shared.utils import load_config, setup_logger
from vision_daemon.core.detector import FaceDetector
import numpy as np

logger = setup_logger("Encoder")

class FaceEncoder:
    def __init__(self, username: str = "hariom") -> None:
        """Initializes Face Enrollment setup for a specific user.
        
        Args:
            username (str): Target system username to enroll.
        """
        self.username = username
        self.config = load_config()
        self.camera_id = self.config.get("camera_id", 0)
        
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.profiles_dir = os.path.join(project_root, "assets", "profiles")
        os.makedirs(self.profiles_dir, exist_ok=True)
        self.profile_path = os.path.join(self.profiles_dir, f"{self.username}_profile.json")
        self.detector = FaceDetector()

    def enroll_face(self, auto_capture: bool = False) -> bool:
        """Captures a frame from the webcam, extracts the 128-D vector, and saves it.
        
        Args:
            auto_capture (bool): If True, captures dynamically in headless mode when face is stable.
            
        Returns:
            bool: True if enrollment succeeded, False otherwise.
        """
        logger.info(f"Starting Face Enrollment for user: {self.username}")
        logger.info("Initializing camera interface...")
        
        cap = cv2.VideoCapture(self.camera_id)
        if not cap.isOpened():
            logger.error("Could not open webcam. Verify camera permissions.")
            return False
            
        success = False
        face_found_frames = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                logger.error("Failed to read frame from camera.")
                break
                
            # Perform detection checks
            face_crop, bbox = self.detector.get_face_crop(frame, padding_ratio=0.1)
            
            if not self.config.get("headless", True) and not auto_capture:
                # Render enrollment visual instructions if running on screen UI mode
                cv2.putText(frame, "Press 'E' to Enroll Face", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)
                if bbox is not None:
                    x, y, w, h = bbox
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.imshow("Enrollment Setup", frame)
                
                key = cv2.waitKey(1) & 0xFF
                if key == ord('e'):
                    success = self._process_frame(frame)
                    if success:
                        break
                elif key == ord('q'):
                    break
            else:
                # Auto-capture logic for headless execution
                if bbox is not None:
                    face_found_frames += 1
                    logger.info(f"Face lock stable... [{face_found_frames}/10]")
                    if face_found_frames >= 10:
                        success = self._process_frame(frame)
                        if success:
                            break
                else:
                    face_found_frames = max(0, face_found_frames - 1)
                    
        cap.release()
        cv2.destroyAllWindows()
        return success

    def _process_frame(self, frame: np.ndarray) -> bool:
        """Helper to compute embedding vector and serialize to profile.json.
        
        Args:
            frame (np.ndarray): The BGR camera image frame.
            
        Returns:
            bool: True if encoding was extracted and saved, False otherwise.
        """
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        encodings = face_recognition.face_encodings(rgb_frame)
        
        if encodings:
            master_vector = encodings[0]
            with open(self.profile_path, "w") as f:
                json.dump(master_vector.tolist(), f)
            logger.info(f"Enrollment successful! Saved user profile to {self.profile_path}")
            return True
        else:
            logger.warning("No face encoding vector extracted. Retrying frame capture.")
            return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FaceUnlock Enrollment Tool")
    parser.add_argument("--username", type=str, default="hariom", help="Target username to enroll")
    parser.add_argument("--auto", action="store_true", help="Auto-capture face without GUI windows")
    args = parser.parse_args()
    
    encoder = FaceEncoder(username=args.username)
    encoder.enroll_face(auto_capture=args.auto)