import cv2
from core.detector import FaceDetector

def main():
    print("[SYSTEM] Booting up Vision Daemon...")
    cap = cv2.VideoCapture(0) # 0 for default Mac webcam
    detector = FaceDetector()

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[ERROR] Webcam not responding.")
            break

        # Get the cropped face and its coordinates
        face_crop, bbox = detector.get_face_crop(frame)

        if bbox is not None:
            x, y, w, h = bbox
            # Draw a clean rectangle around the face
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(frame, "Face Locked", (x, y-10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # Show the cropped face in a separate small window for debugging
            cv2.imshow("Debug: Face Crop", face_crop)

        cv2.imshow("MacBook M1 FaceUnlock - Phase 1", frame)

        # Press 'q' to quit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()