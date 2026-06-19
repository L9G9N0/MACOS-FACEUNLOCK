import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import urllib.request
import os
import numpy as np
from typing import Tuple, Optional, Any
from shared.utils import verify_file_hash

class FaceDetector:
    def __init__(self, detection_confidence: float = 0.7) -> None:
        """
        Initialize the modern Mediapipe Tasks Vision API.
        Automatically provisions the required TFLite model if missing.
        
        Args:
            detection_confidence (float): Minimum confidence threshold for face detection.
        """
        self.model_path = os.path.join(os.path.dirname(__file__), "blaze_face_short_range.tflite")
        self._download_model_if_needed()
        
        # Configure the Base Options for the ML Engine
        base_options = python.BaseOptions(model_asset_path=self.model_path)
        options = vision.FaceDetectorOptions(
            base_options=base_options, 
            min_detection_confidence=detection_confidence
        )
        self.detector = vision.FaceDetector.create_from_options(options)

    def _download_model_if_needed(self) -> None:
        """Fetches the bare-metal optimized TFLite model from Google if not locally cached, verifying its integrity."""
        expected_hash = "b4578f35940bf5a1a655214a1cce5cab13eba73c1297cd78e1a04c2380b0152f"
        
        # If it exists but has a different hash, delete it so we re-download a clean copy
        if os.path.exists(self.model_path) and not verify_file_hash(self.model_path, expected_hash):
            print("[WARNING] Model hash mismatch. Deleting and re-downloading model...")
            try:
                os.remove(self.model_path)
            except Exception as e:
                print(f"[ERROR] Could not remove invalid model: {str(e)}")
            
        if not os.path.exists(self.model_path):
            print("[SYSTEM] Provisioning Mediapipe TFLite Model...")
            url = "https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite"
            urllib.request.urlretrieve(url, self.model_path)
            print("[SYSTEM] Model provisioned successfully.")
            
        # Hard fail if download is corrupted or modified
        if not verify_file_hash(self.model_path, expected_hash):
            raise ValueError(f"Integrity check failed for TFLite model: {self.model_path}")



    def get_face_crop(self, frame: np.ndarray, padding_ratio: float = 0.3) -> Tuple[Optional[np.ndarray], Optional[Tuple[int, int, int, int]]]:
        """
        Takes a BGR OpenCV frame, runs Tasks API, returns the PADDED cropped face.
        padding_ratio=0.3 means expanding the box by 30% in all directions.
        
        Args:
            frame (np.ndarray): Input image frame in BGR format.
            padding_ratio (float): Ratio to expand the bounding box by.
            
        Returns:
            Tuple[Optional[np.ndarray], Optional[Tuple[int, int, int, int]]]: 
                Cropped face image array and coordinates (x, y, w, h), or (None, None) if not detected.
        """
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        
        detection_result = self.detector.detect(mp_image)
        
        if not detection_result.detections:
            return None, None 

        detection = detection_result.detections[0]
        bbox = detection.bounding_box
        
        # Original coordinates
        orig_x, orig_y, orig_w, orig_h = int(bbox.origin_x), int(bbox.origin_y), int(bbox.width), int(bbox.height)
        
        # Calculate padding in pixels
        pad_x = int(orig_w * padding_ratio)
        pad_y = int(orig_h * padding_ratio)
        
        # Calculate new padded coordinates
        x = orig_x - pad_x
        y = orig_y - int(pad_y * 1.5) # Extra padding on top to include the full head/hair
        w = orig_w + (2 * pad_x)
        h = orig_h + (2 * pad_y)
        
        # OS-level Safety: Bounds checking (Clamping to array limits)
        ih, iw, _ = frame.shape
        x, y = max(0, x), max(0, y)
        w = min(w, iw - x)
        h = min(h, ih - y)
        
        # Array slicing the frame safely
        face_crop = frame[y:y+h, x:x+w]
        
        return face_crop, (x, y, w, h)