import os
import json
import cv2
import numpy as np
import face_recognition
from shared.utils import load_config, setup_logger
from typing import Tuple, Optional, Dict, Union

logger = setup_logger("Recognizer")

class FaceRecognizer:
    def __init__(self) -> None:
        """Initializes the Multi-Identity Face Verification Engine."""
        logger.info("Initializing Multi-Identity Face Verification Engine...")
        self.config = load_config()
        self.threshold = self.config.get("distance_threshold", 0.45)
        
        # Resolve profiles directory
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.profiles_dir = os.path.join(project_root, "assets", "profiles")
        os.makedirs(self.profiles_dir, exist_ok=True)
        
        # Dict caching master profiles in RAM
        self.cached_profiles: Dict[str, np.ndarray] = {}
        self.load_all_profiles()

    def load_all_profiles(self) -> None:
        """Loads all JSON profile files from the profiles directory into memory."""
        self.cached_profiles = {}
        for filename in os.listdir(self.profiles_dir):
            if filename.endswith("_profile.json"):
                username = filename.replace("_profile.json", "")
                filepath = os.path.join(self.profiles_dir, filename)
                try:
                    with open(filepath, "r") as f:
                        data = json.load(f)
                        self.cached_profiles[username] = np.array(data)
                    logger.info(f"Loaded master profile for user: {username}")
                except Exception as e:
                    logger.error(f"Error loading profile {filename}: {str(e)}")

    def verify_identity(self, frame: np.ndarray, bbox: Tuple[int, int, int, int]) -> Tuple[Optional[str], float]:
        """Compares the frame face against all cached profiles in RAM.
        
        Args:
            frame (np.ndarray): The BGR image frame containing the face.
            bbox (Tuple[int, int, int, int]): Face box coordinates (x, y, w, h).
            
        Returns:
            Tuple[Optional[str], float]: (matched_username, distance) if a match is found, else (None, min_distance).
        """
        if not self.cached_profiles:
            logger.warning("No profiles loaded in database.")
            return None, 1.0

        x, y, w, h = bbox
        face_crop = frame[max(0, y):y+h, max(0, x):x+w]
        
        if face_crop.size == 0:
            return None, 1.0
            
        rgb_crop = cv2.cvtColor(face_crop, cv2.COLOR_BGR2RGB)
        encodings = face_recognition.face_encodings(rgb_crop)
        
        if not encodings:
            return None, 1.0
            
        current_vector = encodings[0]
        
        best_match = None
        min_distance = 1.0
        
        # Compare against all registered users
        for username, master_vector in self.cached_profiles.items():
            distance = face_recognition.face_distance([master_vector], current_vector)[0]
            if distance < min_distance:
                min_distance = distance
                if distance < self.threshold:
                    best_match = username
                    
        return best_match, float(min_distance)

    def add_profile(self, username: str, vector: Union[np.ndarray, list]) -> bool:
        """Adds or updates a user profile on disk and in memory cache.
        
        Args:
            username (str): Target user name to register.
            vector (Union[np.ndarray, list]): 128-D facial vector data.
            
        Returns:
            bool: True if profile is successfully saved, False otherwise.
        """
        filepath = os.path.join(self.profiles_dir, f"{username}_profile.json")
        try:
            with open(filepath, "w") as f:
                json.dump(vector.tolist() if isinstance(vector, np.ndarray) else vector, f)
            self.cached_profiles[username] = np.array(vector)
            logger.info(f"Successfully saved profile: {username}")
            return True
        except Exception as e:
            logger.error(f"Failed to add profile {username}: {str(e)}")
            return False

    def remove_profile(self, username: str) -> bool:
        """Removes a user profile from disk and from memory cache.
        
        Args:
            username (str): The target user name.
            
        Returns:
            bool: True if successfully removed, False otherwise.
        """
        filepath = os.path.join(self.profiles_dir, f"{username}_profile.json")
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                if username in self.cached_profiles:
                    del self.cached_profiles[username]
                logger.info(f"Successfully removed profile: {username}")
                return True
            except Exception as e:
                logger.error(f"Failed to delete profile {username}: {str(e)}")
        return False

    def export_profile(self, username: str, export_path: str) -> bool:
        """Exports profile vector data to a custom path.
        
        Args:
            username (str): The target user name.
            export_path (str): Destination file path.
            
        Returns:
            bool: True if export succeeded, False otherwise.
        """
        if username in self.cached_profiles:
            try:
                with open(export_path, "w") as f:
                    json.dump(self.cached_profiles[username].tolist(), f)
                logger.info(f"Exported profile {username} to {export_path}")
                return True
            except Exception as e:
                logger.error(f"Export profile failed: {str(e)}")
        return False

    def import_profile(self, username: str, import_path: str) -> bool:
        """Imports profile vector data from a file.
        
        Args:
            username (str): The target user name.
            import_path (str): Path to import file.
            
        Returns:
            bool: True if import succeeded, False otherwise.
        """
        if os.path.exists(import_path):
            try:
                with open(import_path, "r") as f:
                    vector = json.load(f)
                return self.add_profile(username, vector)
            except Exception as e:
                logger.error(f"Import profile failed: {str(e)}")
        return False