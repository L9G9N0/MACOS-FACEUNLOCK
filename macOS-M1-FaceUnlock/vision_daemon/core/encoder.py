import cv2
import face_recognition
import numpy as np
import json
import os

class FaceEncoder:
    def __init__(self):
        # We will save your digital password in the core folder
        self.profile_path = os.path.join(os.path.dirname(__file__), "hariom_profile.json")

    def enroll_face(self):
        """Captures a frame, extracts the 128-D vector, and saves it to disk."""
        print("[SYSTEM] Starting Face Enrollment...")
        print("[INSTRUCTION] Look directly at the camera and press 'e' to capture.")
        
        cap = cv2.VideoCapture(0)
        
        while True:
            ret, frame = cap.read()
            if not ret: break
            
            cv2.putText(frame, "Press 'E' to Enroll Face", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 0), 2)
            cv2.imshow("Enrollment", frame)
            
            if cv2.waitKey(1) & 0xFF == ord('e'):
                # 1. Convert to RGB for the AI
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # 2. Extract the 128-D Vector
                encodings = face_recognition.face_encodings(rgb_frame)
                
                if len(encodings) > 0:
                    master_vector = encodings[0]
                    
                    # 3. Save to Disk (Only once!)
                    with open(self.profile_path, "w") as f:
                        # Numpy arrays must be converted to standard lists for JSON
                        json.dump(master_vector.tolist(), f)
                        
                    print(f"[SUCCESS] Profile saved! Vector size: {len(master_vector)} dimensions.")
                    break
                else:
                    print("[ERROR] No face found. Try again.")
                    
            elif cv2.waitKey(1) & 0xFF == ord('q'):
                break
                
        cap.release()
        cv2.destroyAllWindows()

# Run this file independently to enroll your face
if __name__ == "__main__":
    encoder = FaceEncoder()
    encoder.enroll_face()