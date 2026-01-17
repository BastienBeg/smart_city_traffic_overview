import cv2
import time
import logging
import os
from typing import Iterator, Optional, Tuple
import threading

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("VideoSource")


class VideoSource:
    """
    Handles robust video frames ingestion from RTSP streams or local files.
    Features:
    - Automatic reconnection for streams
    - Looping for file sources
    - Iterator interface for frame yielding
    - Frame sampling for inference at configurable FPS
    """

    def __init__(
        self,
        source_url: str,
        camera_id: str,
        reconnect_delay: int = 5,
        inference_fps: int = 5,
    ):
        """
        Initializes the VideoSource.

        Args:
            source_url: Path to video file or RTSP stream URL.
            camera_id: Unique identifier for this camera.
            reconnect_delay: Seconds to wait before reconnection attempt.
            inference_fps: Target FPS for inference sampling.
        """
        self.source_url = source_url
        self.camera_id = camera_id
        self.reconnect_delay = reconnect_delay
        self.inference_fps = inference_fps
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_running = False
        
        # Determine if source is a file or stream based on simple heuristic (or explicit config)
        # For now, if it creates a valid file path, treat as file, else stream
        self.is_file = os.path.exists(source_url) and os.path.isfile(source_url)
        logger.info(f"Initialized VideoSource for {camera_id}. Source Type: {'File' if self.is_file else 'Stream'}")

    def connect(self):
        """Attempts to connect to the video source."""
        if self.cap is not None:
            self.cap.release()
        
        logger.info(f"Connecting into {self.source_url}...")
        self.cap = cv2.VideoCapture(self.source_url)
        
        if not self.cap.isOpened():
            logger.error(f"Failed to open source: {self.source_url}")
            return False
            
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = int(self.cap.get(cv2.CAP_PROP_FPS)) or 30 # Default to 30 if unknown
        
        logger.info(f"Successfully connected to {self.source_url} ({self.width}x{self.height} @ {self.fps}fps)")
        return True

    def _reconnect_loop(self):
        """Blocks until connection is re-established."""
        while self.is_running:
            logger.warning(f"Connection lost. Retrying in {self.reconnect_delay} seconds...")
            time.sleep(self.reconnect_delay)
            if self.connect():
                return

    def stream(self) -> Iterator[Tuple[str, object]]:
        """
        Yields frames from the source.
        Returns tuples of (camera_id, frame).
        """
        self.is_running = True
        
        if not self.connect():
           # If initial connection fails, enter retry loop immediately if it's a stream
           # If it's a file, we might just crash or retry depends on requirement. 
           # Let's assume critical service and loop.
           self._reconnect_loop()

        while self.is_running:
            if self.cap is None or not self.cap.isOpened():
                self._reconnect_loop()
                continue
                
            ret, frame = self.cap.read()
            
            if not ret:
                if self.is_file:
                    # EOF reached for file, loop back
                    logger.info("EOF reached for file. Looping...")
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                else:
                    # Read failed for stream, trigger reconnect
                    logger.error("Failed to read frame from stream.")
                    self._reconnect_loop()
                    continue
            
            yield self.camera_id, frame

    def stream_for_inference(self) -> Iterator[Tuple[str, bytes]]:
        """
        Yields JPEG-encoded frames at the target inference FPS.
        Returns tuples of (camera_id, jpeg_bytes).

        This method samples frames at `self.inference_fps` rate and encodes them
        as JPEG for efficient gRPC transfer.
        """
        self.is_running = True

        if not self.connect():
            self._reconnect_loop()

        # Calculate frame interval based on source FPS and target inference FPS
        source_fps = self.fps if hasattr(self, "fps") else 30
        frame_interval = max(1, int(source_fps / self.inference_fps))
        frame_count = 0
        last_inference_time = time.time()
        min_interval = 1.0 / self.inference_fps

        logger.info(f"Starting inference stream: source={source_fps}fps, target={self.inference_fps}fps, interval={frame_interval} frames")

        while self.is_running:
            if self.cap is None or not self.cap.isOpened():
                self._reconnect_loop()
                continue

            ret, frame = self.cap.read()

            if not ret:
                if self.is_file:
                    logger.info("EOF reached for file. Looping...")
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    frame_count = 0
                    continue
                else:
                    logger.error("Failed to read frame from stream.")
                    self._reconnect_loop()
                    continue

            frame_count += 1

            # Time-based sampling: ensure minimum interval between inference frames
            current_time = time.time()
            if current_time - last_inference_time >= min_interval:
                # Encode frame as JPEG
                success, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                if success:
                    last_inference_time = current_time
                    yield self.camera_id, buffer.tobytes()
                else:
                    logger.warning("Failed to encode frame as JPEG")

    def stop(self):
        self.is_running = False
        if self.cap:
            self.cap.release()
        logger.info("VideoSource stopped.")

