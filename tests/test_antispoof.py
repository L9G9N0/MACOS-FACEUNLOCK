import os
import sys
import unittest
import numpy as np
from unittest.mock import MagicMock, patch

# Ensure project root is on the path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Mock mediapipe and cv2
sys.modules['mediapipe'] = MagicMock()
sys.modules['mediapipe.tasks'] = MagicMock()
sys.modules['mediapipe.tasks.python'] = MagicMock()
sys.modules['mediapipe.tasks.python.vision'] = MagicMock()
sys.modules['cv2'] = MagicMock()

from vision_daemon.core.antispoof import FASEstimator

class TestFASEstimator(unittest.TestCase):
    @patch('vision_daemon.core.antispoof.vision.FaceLandmarker.create_from_options')
    @patch('vision_daemon.core.antispoof.load_config')
    @patch('os.path.exists')
    def setUp(self, mock_exists, mock_load_config, mock_create):
        mock_exists.return_value = True
        mock_load_config.return_value = {
            "challenge_yaw_threshold": 12.0,
            "timeout_seconds": 5,
            "socket_path": "/tmp/test_faceunlock.sock"
        }
        self.mock_landmarker = MagicMock()
        mock_create.return_value = self.mock_landmarker
        self.estimator = FASEstimator()

    def test_reset_session(self):
        """Test if session state resets correctly."""
        self.estimator.reset_session()
        self.assertEqual(self.estimator.current_state, FASEstimator.STATE_AWAITING_CHALLENGE)
        self.assertIn(self.estimator.challenge_direction, [-1, 1])
        self.assertGreater(self.estimator.timeout_limit, 0.0)

    @patch('vision_daemon.core.antispoof.cv2.cvtColor')
    @patch('vision_daemon.core.antispoof.cv2.RQDecomp3x3')
    def test_get_head_yaw(self, mock_rq, mock_cvt):
        """Test head yaw extraction from landmarker outputs."""
        mock_result = MagicMock()
        mock_result.facial_transformation_matrixes = [
            np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
        ]
        self.mock_landmarker.detect.return_value = mock_result
        mock_rq.return_value = ([0.0, 15.5, 0.0], None, None, None, None, None)

        yaw = self.estimator.get_head_yaw(None)
        self.assertEqual(yaw, 15.5)

    @patch('vision_daemon.core.antispoof.cv2.cvtColor')
    @patch('vision_daemon.core.antispoof.cv2.RQDecomp3x3')
    def test_check_liveness_flow_success(self, mock_rq, mock_cvt):
        """Test successful liveness validation challenge flow."""
        mock_result = MagicMock()
        mock_result.facial_transformation_matrixes = [
            np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
        ]
        self.mock_landmarker.detect.return_value = mock_result
        
        # Enforce direction to be 1 (RIGHT)
        self.estimator.challenge_direction = 1
        self.estimator.current_state = FASEstimator.STATE_AWAITING_CHALLENGE
        
        # 1. User looks straight -> Still awaiting challenge
        mock_rq.return_value = ([0.0, 0.0, 0.0], None, None, None, None, None)
        is_live, yaw, inst = self.estimator.check_liveness(None, None)
        self.assertFalse(is_live)
        self.assertEqual(self.estimator.current_state, FASEstimator.STATE_AWAITING_CHALLENGE)
        
        # 2. User turns right -> Transitions to Held in state, returns turn instructions
        mock_rq.return_value = ([0.0, 15.0, 0.0], None, None, None, None, None)
        is_live, yaw, inst = self.estimator.check_liveness(None, None)
        self.assertFalse(is_live)
        self.assertEqual(self.estimator.current_state, FASEstimator.STATE_CHALLENGE_HELD)
        
        # 3. Next frame -> Transitions from Held to Returning center
        mock_rq.return_value = ([0.0, 15.0, 0.0], None, None, None, None, None)
        is_live, yaw, inst = self.estimator.check_liveness(None, None)
        self.assertFalse(is_live)
        self.assertEqual(self.estimator.current_state, FASEstimator.STATE_RETURNING)
        
        # 4. User returns center -> Transitions from Returning to Confirmed, returns False on change step
        mock_rq.return_value = ([0.0, 2.0, 0.0], None, None, None, None, None)
        is_live, yaw, inst = self.estimator.check_liveness(None, None)
        self.assertFalse(is_live)
        self.assertEqual(self.estimator.current_state, FASEstimator.STATE_CONFIRMED)
        
        # 5. Subsequent frame while Confirmed -> Returns True
        mock_rq.return_value = ([0.0, 2.0, 0.0], None, None, None, None, None)
        is_live, yaw, inst = self.estimator.check_liveness(None, None)
        self.assertTrue(is_live)
        self.assertEqual(inst, "LIVENESS VERIFIED")

    @patch('vision_daemon.core.antispoof.cv2.cvtColor')
    @patch('vision_daemon.core.antispoof.cv2.RQDecomp3x3')
    def test_check_liveness_timeout(self, mock_rq, mock_cvt):
        """Test that liveness estimator handles timeout correctly."""
        mock_result = MagicMock()
        mock_result.facial_transformation_matrixes = [
            np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
        ]
        self.mock_landmarker.detect.return_value = mock_result
        mock_rq.return_value = ([0.0, 0.0, 0.0], None, None, None, None, None)
        
        # Fast-forward start time to trigger timeout
        self.estimator.challenge_start_time = 0.0
        
        is_live, yaw, inst = self.estimator.check_liveness(None, None)
        self.assertFalse(is_live)
        self.assertEqual(self.estimator.current_state, FASEstimator.STATE_AWAITING_CHALLENGE)
        self.assertIn("TIMEOUT", inst)

if __name__ == '__main__':
    unittest.main()
