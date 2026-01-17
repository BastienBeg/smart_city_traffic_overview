import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

from stream import VideoSource

class TestVideoSource(unittest.TestCase):

    @patch('stream.cv2.VideoCapture')
    def test_connect_success(self, mock_capture):
        """Test successful connection."""
        mock_cap_instance = MagicMock()
        mock_cap_instance.isOpened.return_value = True
        mock_capture.return_value = mock_cap_instance

        source = VideoSource("rtsp://test", "cam1")
        connected = source.connect()
        
        self.assertTrue(connected)
        mock_capture.assert_called_with("rtsp://test")

    @patch('stream.cv2.VideoCapture')
    def test_connect_fail(self, mock_capture):
        """Test connection failure."""
        mock_cap_instance = MagicMock()
        mock_cap_instance.isOpened.return_value = False
        mock_capture.return_value = mock_cap_instance

        source = VideoSource("rtsp://test", "cam1")
        connected = source.connect()
        
        self.assertFalse(connected)

    @patch('stream.time.sleep') # Mock sleep to speed up test
    @patch('stream.cv2.VideoCapture')
    def test_reconnection_logic(self, mock_capture, mock_sleep):
        """Test that stream tries to reconnect on failure."""
        
        # Setup mock behavior:
        # 1. Connect -> Fail
        # 2. Reconnect -> Fail
        # 3. Reconnect -> Success
        
        fail_cap = MagicMock()
        fail_cap.isOpened.return_value = False
        
        success_cap = MagicMock()
        success_cap.isOpened.return_value = True
        success_cap.read.return_value = (True, "frame_data")
        
        # Side effect for cv2.VideoCapture constructor
        mock_capture.side_effect = [fail_cap, fail_cap, success_cap]
        
        source = VideoSource("rtsp://test", "cam1", reconnect_delay=1)
        
        # limiting loop to avoid infinite test
        iterator = source.stream()
        
        # First call should trigger the reconnection loop
        # We expect it to eventually yield the frame from the 3rd connection attempt
        cam_id, frame = next(iterator)
        
        self.assertEqual(cam_id, "cam1")
        self.assertEqual(frame, "frame_data")
        self.assertEqual(mock_capture.call_count, 3) # Initial + 2 Retries
        
        source.stop()

if __name__ == '__main__':
    unittest.main()
