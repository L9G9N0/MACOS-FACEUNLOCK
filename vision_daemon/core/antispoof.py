import os
import cv2
import random
import time
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from shared.utils import load_config, setup_logger, verify_file_hash
from typing import Tuple, Optional

logger = setup_logger("Liveness")

class FASEstimator:
    # State Enumerations
    STATE_AWAITING_CHALLENGE = 0
    STATE_CHALLENGE_HELD = 1
    STATE_RETURNING = 2
    STATE_CONFIRMED = 3
    STATE_FAILED = 4

    def __init__(self) -> None:
        """Initializes the Active Liveness 3D head-pose validation engine."""
        logger.info("Initializing Active Liveness 3D Estimator...")
        self.config = load_config()
        self.required_angle = self.config.get("challenge_yaw_threshold", 12.0)
        self.model_path = os.path.join(os.path.dirname(__file__), "face_landmarker.task")
        
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"[FATAL] Model missing at {self.model_path}. Download face_landmarker.task first.")

        # Validate file integrity to prevent server model modifications or corruptions
        expected_hash = "64184e229b263107bc2b804c6625db1341ff2bb731874b0bcc2fe6544e0bc9ff"
        if not verify_file_hash(self.model_path, expected_hash):
            raise ValueError(f"[FATAL] Integrity check failed for facial landmarker task file: {self.model_path}")


        base_options = python.BaseOptions(model_asset_path=self.model_path)
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            output_facial_transformation_matrixes=True,
            num_faces=1
        )
        self.landmarker = vision.FaceLandmarker.create_from_options(options)
        
        self.reset_session()

    def reset_session(self) -> None:
        """Resets the challenge session state parameters."""
        self.current_state = self.STATE_AWAITING_CHALLENGE
        # Randomize challenge direction: -1 for Left (negative yaw), 1 for Right (positive yaw)
        self.challenge_direction = random.choice([-1, 1])
        self.challenge_start_time = time.time()
        self.timeout_limit = 5.0  # 5 seconds to complete the turn
        self.cooldown_until = 0.0
        logger.info(f"Challenge initialized: Turn head {'LEFT' if self.challenge_direction < 0 else 'RIGHT'}")

    def get_head_yaw(self, frame: np.ndarray) -> Optional[float]:
        """Calculates Head Yaw in degrees using the facial transformation matrix.
        
        Args:
            frame (np.ndarray): The BGR image frame containing the face.
            
        Returns:
            Optional[float]: Yaw rotation in degrees, or None if computation failed.
        """
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        result = self.landmarker.detect(mp_image)
        
        if not result.facial_transformation_matrixes:
            return None
            
        matrix = result.facial_transformation_matrixes[0]
        rot_matrix = matrix[:3, :3]
        
        # Decompose matrix to Euler angles
        angles, _, _, _, _, _ = cv2.RQDecomp3x3(rot_matrix)
        # angles[1] corresponds to Yaw (y-axis rotation)
        return float(angles[1])

    def check_liveness(self, frame: np.ndarray, bbox: Optional[Tuple[int, int, int, int]]) -> Tuple[bool, float, str]:
        """Processes head pose angles against the active FSM liveness challenge flow.
        
        Args:
            frame (np.ndarray): The BGR image frame.
            bbox (Optional[Tuple[int, int, int, int]]): The detected face bounding box coordinates (x, y, w, h).
            
        Returns:
            Tuple[bool, float, str]: (is_live, current_yaw, status_instruction)
        """
        now = time.time()
        
        if now < self.cooldown_until:
            return False, 0.0, f"COOLDOWN (FAIL RECOVERY)... {int(self.cooldown_until - now)}s"

        yaw = self.get_head_yaw(frame)
        if yaw is None:
            return False, 0.0, "NO FACE DETECTED"

        # Check for challenge timeout
        if self.current_state != self.STATE_CONFIRMED and (now - self.challenge_start_time) > self.timeout_limit:
            logger.warning("Active liveness challenge timed out. Triggering failure recovery.")
            self.current_state = self.STATE_FAILED
            self.cooldown_until = now + 2.0  # 2 seconds cooldown
            self.reset_session()
            return False, yaw, "TIMEOUT: CHALLENGE RESET"

        # State transitions
        if self.current_state == self.STATE_AWAITING_CHALLENGE:
            instruction = f"TURN HEAD {'LEFT' if self.challenge_direction < 0 else 'RIGHT'}"
            # Check if target yaw is crossed in the correct randomized direction
            if (self.challenge_direction < 0 and yaw < -self.required_angle) or \
               (self.challenge_direction > 0 and yaw > self.required_angle):
                self.current_state = self.STATE_CHALLENGE_HELD
                logger.info("Challenge direction matched. Proceeding to return phase.")
            return False, yaw, instruction

        elif self.current_state == self.STATE_CHALLENGE_HELD:
            instruction = "HOLD AND START RETURNING CENTER"
            # Proceed to returning status
            self.current_state = self.STATE_RETURNING
            return False, yaw, instruction

        elif self.current_state == self.STATE_RETURNING:
            instruction = "LOOK STRAIGHT AT SCREEN"
            # Expect user to return center (absolute yaw < 6 degrees)
            if abs(yaw) < 6.0:
                self.current_state = self.STATE_CONFIRMED
                logger.info("Active liveness verification successful.")
            return False, yaw, instruction

        elif self.current_state == self.STATE_CONFIRMED:
            return True, yaw, "LIVENESS VERIFIED"

        return False, yaw, "LIVENESS PENDING"