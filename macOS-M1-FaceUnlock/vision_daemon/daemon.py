import cv2
import socket
import os
from collections import deque
from core.detector import FaceDetector
from core.antispoof import FASEstimator
from core.recognizer import FaceRecognizer

def main():
    print("[SYSTEM] Booting up Vision Daemon...")
    
    # 1. DEFINE SECURE SOCKET PATH (Layer 1 Security)
    home_dir = os.path.expanduser("~")
    socket_dir = os.path.join(home_dir, ".faceunlock_run")
    socket_path = os.path.join(socket_dir, "faceunlock.sock")
    
    if not os.path.exists(socket_dir):
        os.makedirs(socket_dir, mode=0o700)
    
    cap = cv2.VideoCapture(0)
    
    detector = FaceDetector()
    fas_estimator = FASEstimator()
    recognizer = FaceRecognizer()

    liveness_buffer = deque(maxlen=5)

    while True:
        ret, frame = cap.read()
        if not ret: break

        face_crop, bbox = detector.get_face_crop(frame, padding_ratio=0.1)

        if bbox is not None:
            x, y, w, h = bbox
            
            # 2. RUN LAYER 1: ACTIVE LIVENESS (FSM)
            is_live_current, yaw_angle, instruction = fas_estimator.check_liveness(frame, bbox)
            liveness_buffer.append(is_live_current)
            
            is_system_live = (len(liveness_buffer) == 5) and all(liveness_buffer)

            # 3. RUN LAYER 2: IDENTITY VERIFICATION
            if is_system_live:
                is_match, distance = recognizer.verify_identity(frame, bbox)
                
                if is_match:
                    color = (255, 255, 0) # Cyan for Authenticated
                    status_text = f"UNLOCKED: HARIOM | Match: {distance:.2f}"
                    
                    # --- THE IPC TRIGGER ---
                    try:
                        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                            s.connect(socket_path)
                            s.sendall(b"AUTH_SUCCESS_HARIOM")
                            print("[IPC] Sent unlock signal to PAM Module.")
                    except (FileNotFoundError, ConnectionRefusedError):
                        pass 

                else:
                    color = (0, 0, 255) # Red for Unknown
                    status_text = f"UNKNOWN PERSON | Match: {distance:.2f}"
            else:
                color = (0, 165, 255) # Orange for Pending
                status_text = f"{instruction} | Yaw:{yaw_angle:.1f}"

            # UI Update
            cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
            cv2.putText(frame, status_text, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        cv2.imshow("MacBook M1 FaceUnlock - Final System", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'): break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()