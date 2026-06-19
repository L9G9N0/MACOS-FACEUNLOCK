import os
import json
import logging
import hashlib
from typing import Any, Dict

def verify_file_hash(file_path: str, expected_hash: str) -> bool:
    """Computes the SHA-256 hash of a file and verifies it matches the expected hash.
    
    Args:
        file_path (str): Path to the target file.
        expected_hash (str): The expected SHA-256 hexadecimal digest.
        
    Returns:
        bool: True if the file matches the expected hash, False otherwise.
    """
    if not os.path.exists(file_path):
        return False
    sha256 = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        return sha256.hexdigest() == expected_hash
    except Exception:
        return False

def load_config() -> Dict[str, Any]:
    """Loads system configuration options from configs/config.json.
    
    Returns:
        Dict[str, Any]: Configuration dictionary with resolved paths and keys.
    """
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "configs", "config.json")
    try:
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config = json.load(f)
                # Resolve socket path
                config["socket_path"] = os.path.expanduser(config.get("socket_path", "~/.faceunlock_run/faceunlock.sock"))
                return config
    except Exception as e:
        print(f"[WARNING] Could not parse config, loading defaults: {str(e)}")
        
    return {
        "distance_threshold": 0.45,
        "challenge_yaw_threshold": 12.0,
        "timeout_seconds": 5,
        "socket_path": os.path.expanduser("~/.faceunlock_run/faceunlock.sock"),
        "headless": True,
        "camera_id": 0,
        "liveness_buffer_size": 5
    }

def setup_logger(name: str = "FaceUnlock") -> logging.Logger:
    """Setup structured logger with log levels and format templates.
    
    Args:
        name (str): The name of the logger instance.
        
    Returns:
        logging.Logger: The configured Logger instance.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Console output
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        logger.addHandler(ch)
        
        # File output inside run directory
        home_dir = os.path.expanduser("~")
        log_dir = os.path.join(home_dir, ".faceunlock_run")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "faceunlock.log")
        
        fh = logging.FileHandler(log_file)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
        
    return logger

