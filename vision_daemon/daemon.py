import os
import sys
import cv2
import time
from collections import deque

# Adjust python paths for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from shared.utils import load_config, setup_logger
from ipc.protocol import send_auth_signal
from vision_daemon.core.detector import FaceDetector
from vision_daemon.core.antispoof import FASEstimator
from vision_daemon.core.recognizer import FaceRecognizer

logger = setup_logger("Daemon")

def main():
    logger.info("Starting FaceUnlock Vision Daemon...")
    config = load_config()
    
    camera_id = config.get("camera_id", 0)
    headless = config.get("headless", True)
    buf_size = config.get("liveness_buffer_size", 5)
    
    logger.info(f"Configurations - Camera: {camera_id} | Headless: {headless} | Liveness Buffer Size: {buf_size}")
    
    # Initialize capturing device
    cap = cv2.VideoCapture(camera_id)
    if not cap.isOpened():
        logger.error(f"Cannot initialize camera device index {camera_id}.")
        return

    try:
        detector = FaceDetector()
        fas_estimator = FASEstimator()
        recognizer = FaceRecognizer()
    except Exception as e:
        logger.error(f"Initialization failure of core models: {str(e)}")
        cap.release()
        return

    # Liveness state tracking buffer
    liveness_buffer = deque(maxlen=buf_size)
    
    # State flags to handle logs rate-limiting
    last_log_time = 0

    logger.info("Vision loop initialized successfully. Awaiting face lock...")
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                logger.warning("Camera failed to deliver frame. Retrying...")
                time.sleep(0.5)
                continue

            # Detect face
            face_crop, bbox = detector.get_face_crop(frame, padding_ratio=0.1)

            if bbox is not None:
                x, y, w, h = bbox
                
                # Verify active liveness challenge response
                is_live_current, yaw_angle, instruction = fas_estimator.check_liveness(frame, bbox)
                liveness_buffer.append(is_live_current)
                
                # Confirm liveness over buffer size
                is_system_live = (len(liveness_buffer) == buf_size) and all(liveness_buffer)

                now = time.time()
                if now - last_log_time > 1.5:  # Limit loop logging frequency
                    logger.debug(f"Yaw: {yaw_angle:.1f} | State: {instruction} | Liveness: {is_system_live}")
                    last_log_time = now

                # Verify identity if liveness confirmed
                if is_system_live:
                    matched_user, distance = recognizer.verify_identity(frame, bbox)
                    
                    if matched_user:
                        logger.info(f"Face matched user '{matched_user}' (Distance: {distance:.2f})")
                        # Dispatch success signal through UNIX socket
                        success = send_auth_signal(matched_user)
                        if success:
                            # Reset buffer to enforce re-challenge on next login trigger
                            liveness_buffer.clear()
                            fas_estimator.reset_session()
                            time.sleep(2)  # Cooldown
                    else:
                        if distance < 1.0:
                            logger.info(f"Unenrolled profile face detected. (Best distance: {distance:.2f})")
                
                if not headless:
                    color = (255, 255, 0) if is_system_live else (0, 165, 255)
                    status_text = f"Live: {is_system_live} | {instruction}"
                    cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
                    cv2.putText(frame, status_text, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            else:
                if not headless:
                    cv2.putText(frame, "Awaiting Face...", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

            if not headless:
                cv2.imshow("macOS FaceUnlock Monitor", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            else:
                # Sleep briefly to reduce CPU utilization in headless loops
                time.sleep(0.02)
                
    except KeyboardInterrupt:
        logger.info("Daemon execution stopped by terminal signal.")
    except Exception as e:
        logger.critical(f"Daemon crashed with error: {str(e)}")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        logger.info("Camera resources released. Exit.")

if __name__ == "__main__":
    main()