import os
import sys
import json
import shutil
import tempfile
import unittest
import numpy as np
from unittest.mock import MagicMock, patch

# Ensure project root is on the path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Setup mock for sys.modules before importing FaceRecognizer
sys.modules['face_recognition'] = MagicMock()
sys.modules['cv2'] = MagicMock()

from vision_daemon.core.recognizer import FaceRecognizer

class TestFaceRecognizer(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for profiles
        self.test_dir = tempfile.mkdtemp()
        
        # Patch load_config to return controlled threshold
        with patch('vision_daemon.core.recognizer.load_config') as mock_load:
            mock_load.return_value = {"distance_threshold": 0.45}
            
            # Setup recognizer and swap profiles directory to temp path
            self.recognizer = FaceRecognizer()
            self.recognizer.profiles_dir = self.test_dir
            self.recognizer.cached_profiles = {}

    def tearDown(self):
        # Cleanup temporary files
        shutil.rmtree(self.test_dir)

    def test_add_and_load_profile(self):
        """Test profile storage and dynamic reloading."""
        vector = np.random.rand(128)
        success = self.recognizer.add_profile("testuser", vector)
        self.assertTrue(success)
        self.assertIn("testuser", self.recognizer.cached_profiles)
        
        # Confirm file exists on disk
        profile_file = os.path.join(self.test_dir, "testuser_profile.json")
        self.assertTrue(os.path.exists(profile_file))
        
        # Test reload from disk
        self.recognizer.cached_profiles = {}
        self.recognizer.load_all_profiles()
        self.assertIn("testuser", self.recognizer.cached_profiles)
        np.testing.assert_array_almost_equal(self.recognizer.cached_profiles["testuser"], vector)

    def test_remove_profile(self):
        """Test profile removal from cache and disk."""
        vector = np.random.rand(128)
        self.recognizer.add_profile("testuser", vector)
        self.assertIn("testuser", self.recognizer.cached_profiles)
        
        success = self.recognizer.remove_profile("testuser")
        self.assertTrue(success)
        self.assertNotIn("testuser", self.recognizer.cached_profiles)
        profile_file = os.path.join(self.test_dir, "testuser_profile.json")
        self.assertFalse(os.path.exists(profile_file))

    def test_export_import_profile(self):
        """Test exporting profile and importing profile from external paths."""
        vector = np.random.rand(128)
        self.recognizer.add_profile("testuser", vector)
        
        export_file = os.path.join(self.test_dir, "exported.json")
        success_export = self.recognizer.export_profile("testuser", export_file)
        self.assertTrue(success_export)
        self.assertTrue(os.path.exists(export_file))
        
        # Re-import under different username
        success_import = self.recognizer.import_profile("importeduser", export_file)
        self.assertTrue(success_import)
        self.assertIn("importeduser", self.recognizer.cached_profiles)
        np.testing.assert_array_almost_equal(self.recognizer.cached_profiles["importeduser"], vector)

    @patch('vision_daemon.core.recognizer.face_recognition')
    @patch('cv2.cvtColor')
    def test_verify_identity_match(self, mock_cvt, mock_face_rec):
        """Test matching logic with face_distance checks."""
        master_vector = np.ones(128)
        self.recognizer.cached_profiles = {"hariom": master_vector}
        
        # Mock face encodings return value
        mock_face_rec.face_encodings.return_value = [np.ones(128)]
        # Distance = 0.2 (below threshold 0.45)
        mock_face_rec.face_distance.return_value = [0.2]
        
        matched_user, distance = self.recognizer.verify_identity(np.zeros((100, 100, 3), dtype=np.uint8), (10, 10, 80, 80))
        self.assertEqual(matched_user, "hariom")
        self.assertEqual(distance, 0.2)

    @patch('vision_daemon.core.recognizer.face_recognition')
    @patch('cv2.cvtColor')
    def test_verify_identity_no_match(self, mock_cvt, mock_face_rec):
        """Test mismatch behavior when face distance exceeds threshold."""
        master_vector = np.ones(128)
        self.recognizer.cached_profiles = {"hariom": master_vector}
        
        mock_face_rec.face_encodings.return_value = [np.ones(128)]
        # Distance = 0.6 (above threshold 0.45)
        mock_face_rec.face_distance.return_value = [0.6]
        
        matched_user, distance = self.recognizer.verify_identity(np.zeros((100, 100, 3), dtype=np.uint8), (10, 10, 80, 80))
        self.assertIsNone(matched_user)
        self.assertEqual(distance, 0.6)

if __name__ == '__main__':
    unittest.main()
