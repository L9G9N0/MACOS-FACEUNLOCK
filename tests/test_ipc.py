import os
import sys
import socket
import threading
import time
import tempfile
import unittest
from unittest.mock import patch

# Ensure project root is on the path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from ipc.protocol import send_auth_signal

class TestIPCLayer(unittest.TestCase):
    def setUp(self):
        # Create a temp directory for the socket file
        self.temp_dir = tempfile.mkdtemp()
        self.socket_path = os.path.join(self.temp_dir, "faceunlock_test.sock")
        self.received_data = None
        self.server_ready = threading.Event()
        self.stop_server = threading.Event()

    def tearDown(self):
        # Cleanup
        if os.path.exists(self.socket_path):
            os.unlink(self.socket_path)
        os.rmdir(self.temp_dir)

    def _run_mock_server(self):
        """A simple UNIX socket server running in a background thread."""
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.bind(self.socket_path)
        server.listen(1)
        server.settimeout(1.0)
        self.server_ready.set()

        try:
            while not self.stop_server.is_set():
                try:
                    conn, addr = server.accept()
                    conn.settimeout(1.0)
                    self.received_data = conn.recv(1024)
                    conn.close()
                    break
                except socket.timeout:
                    continue
        finally:
            server.close()

    @patch('ipc.protocol.load_config')
    def test_send_auth_signal_success(self, mock_load_config):
        """Test sending authentication success signal when listener is online."""
        mock_load_config.return_value = {
            "socket_path": self.socket_path
        }
        
        # Start background server
        server_thread = threading.Thread(target=self._run_mock_server)
        server_thread.start()
        self.server_ready.wait()

        # Send auth signal
        success = send_auth_signal("hariom")
        self.assertTrue(success)

        # Wait for thread to finish
        server_thread.join(timeout=2.0)
        self.stop_server.set()

        # Assert data received on socket matches expected payload
        self.assertIsNotNone(self.received_data)
        self.assertEqual(self.received_data.decode("utf-8"), "AUTH_SUCCESS_hariom")

    @patch('ipc.protocol.load_config')
    def test_send_auth_signal_no_socket(self, mock_load_config):
        """Test sending auth signal when no listener is waiting on socket path."""
        mock_load_config.return_value = {
            "socket_path": self.socket_path
        }
        # Do not start server, socket path does not exist
        success = send_auth_signal("hariom")
        self.assertFalse(success)

if __name__ == '__main__':
    unittest.main()
