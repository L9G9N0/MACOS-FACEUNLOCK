import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Ensure project root is on the path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Mock modules to avoid missing imports in test runs
sys.modules['cv2'] = MagicMock()
sys.modules['mediapipe'] = MagicMock()
sys.modules['mediapipe.tasks'] = MagicMock()
sys.modules['mediapipe.tasks.python'] = MagicMock()
sys.modules['mediapipe.tasks.python.vision'] = MagicMock()
sys.modules['face_recognition'] = MagicMock()

from vision_daemon.daemon import main

class TestVisionDaemon(unittest.TestCase):
    @patch('vision_daemon.daemon.cv2.VideoCapture')
    @patch('vision_daemon.daemon.FaceDetector')
    @patch('vision_daemon.daemon.FASEstimator')
    @patch('vision_daemon.daemon.FaceRecognizer')
    @patch('vision_daemon.daemon.send_auth_signal')
    @patch('vision_daemon.daemon.load_config')
    def test_daemon_loop_single_iteration(self, mock_load_config, mock_send, mock_rec, mock_fas, mock_det, mock_video_capture):
        """Test daemon runs loop iteration, calls detection/liveness, and triggers signal on match."""
        # 1. Mock configurations
        mock_load_config.return_value = {
            "camera_id": 0,
            "headless": True,
            "liveness_buffer_size": 1  # 1-frame buffer to trigger verification on first successful frame
        }
        
        # 2. Mock camera cap.read() to return one frame and then terminate loop via KeyboardInterrupt
        mock_cap = MagicMock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.side_effect = [(True, "mock_frame"), KeyboardInterrupt("Stop daemon")]
        mock_video_capture.return_value = mock_cap

        # 3. Mock FaceDetector crop output
        mock_det_instance = MagicMock()
        mock_det_instance.get_face_crop.return_value = ("mock_crop", (10, 10, 100, 100))
        mock_det.return_value = mock_det_instance

        # 4. Mock liveness estimator output (Live = True on first check)
        mock_fas_instance = MagicMock()
        mock_fas_instance.check_liveness.return_value = (True, 0.0, "LIVENESS VERIFIED")
        mock_fas.return_value = mock_fas_instance

        # 5. Mock FaceRecognizer match (User matched = "hariom")
        mock_rec_instance = MagicMock()
        mock_rec_instance.verify_identity.return_value = ("hariom", 0.15)
        mock_rec.return_value = mock_rec_instance

        # 6. Run daemon main
        main()

        # 7. Verify calls
        mock_cap.read.assert_called()
        mock_det_instance.get_face_crop.assert_called_with("mock_frame", padding_ratio=0.1)
        mock_fas_instance.check_liveness.assert_called_with("mock_frame", (10, 10, 100, 100))
        mock_rec_instance.verify_identity.assert_called_with("mock_frame", (10, 10, 100, 100))
        mock_send.assert_called_with("hariom")
        mock_cap.release.assert_called()

if __name__ == '__main__':
    unittest.main()
