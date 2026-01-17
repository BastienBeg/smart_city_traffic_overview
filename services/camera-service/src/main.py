import os
import time
import logging
import subprocess
import threading
from stream import VideoSource
from inference_client import InferenceClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("Main")


def start_ffmpeg_process(rtsp_url, width, height, fps):
    command = [
        'ffmpeg',
        '-y',
        '-f', 'rawvideo',
        '-vcodec', 'rawvideo',
        '-pix_fmt', 'bgr24',
        '-s', f"{width}x{height}",
        '-r', str(fps),
        '-i', '-',
        '-c:v', 'libx264',
        '-preset', 'ultrafast',
        '-f', 'rtsp',
        rtsp_url
    ]
    logger.info(f"Starting FFmpeg stream to {rtsp_url}")
    return subprocess.Popen(command, stdin=subprocess.PIPE)


def run_inference_loop(video_source: VideoSource, inference_client: InferenceClient, camera_id: str):
    """
    Runs a separate loop for inference using sampled frames.

    Args:
        video_source: The VideoSource instance.
        inference_client: The gRPC client for inference.
        camera_id: The camera identifier.
    """
    logger.info("Starting inference loop...")
    for cam_id, jpeg_bytes in video_source.stream_for_inference():
        try:
            detections = inference_client.detect(jpeg_bytes, camera_id=cam_id)
            if detections:
                logger.info(f"[{cam_id}] Detected {len(detections)} objects")
        except Exception as e:
            logger.error(f"Inference error: {e}")


def main():
    logger.info("Starting Camera Service...")

    # Load Config from Env
    camera_id = os.environ.get("CAMERA_ID", "default_camera")
    source_url = os.environ.get("SOURCE_URL")
    rtsp_out_url = os.environ.get("RTSP_OUT_URL")
    inference_url = os.environ.get("INFERENCE_SERVICE_URL", "inference-service:50051")
    inference_fps = int(os.environ.get("INFERENCE_FPS", "5"))

    if not source_url:
        logger.error("SOURCE_URL environment variable is required.")
        exit(1)

    logger.info(f"Configuration: CAMERA_ID={camera_id}, SOURCE_URL={source_url}, RTSP_OUT={rtsp_out_url}")
    logger.info(f"Inference: URL={inference_url}, FPS={inference_fps}")

    # Initialize Video Source
    video_source = VideoSource(source_url, camera_id, inference_fps=inference_fps)

    # Initialize gRPC Client for Inference
    inference_client = None
    if inference_url:
        inference_client = InferenceClient(inference_url)
        if inference_client.connect():
            logger.info("Connected to Inference Service.")
        else:
            logger.warning("Failed to connect to Inference Service. Running without inference.")
            inference_client = None

    ffmpeg_process = None

    # Start Inference Thread (if client is available)
    inference_thread = None
    if inference_client:
        # Create a separate VideoSource for inference to avoid blocking main loop
        inference_video_source = VideoSource(source_url, camera_id, inference_fps=inference_fps)
        inference_thread = threading.Thread(
            target=run_inference_loop,
            args=(inference_video_source, inference_client, camera_id),
            daemon=True
        )
        inference_thread.start()

    # Start Processing Loop (main loop for FFmpeg streaming if configured)
    try:
        for cam_id, frame in video_source.stream():
            # Initialize FFmpeg on first frame availability
            if rtsp_out_url and ffmpeg_process is None:
                ffmpeg_process = start_ffmpeg_process(rtsp_out_url, video_source.width, video_source.height, video_source.fps)

            # Check if FFmpeg process is still running
            if ffmpeg_process and ffmpeg_process.poll() is not None:
                logger.error(f"FFmpeg process exited with code {ffmpeg_process.returncode}. Restarting...")
                ffmpeg_process = None

            # Log periodically
            timestamp = time.time()
            if int(timestamp * 10) % 50 == 0: 
                 logger.info(f"Processed frame from {cam_id}. Frame shape: {frame.shape}")
            
            # Pipe to FFmpeg
            if ffmpeg_process:
                try:
                    ffmpeg_process.stdin.write(frame.tobytes())
                except Exception as e:
                    logger.error(f"FFmpeg write failed: {e}. Resetting process...")
                    try:
                        ffmpeg_process.stdin.close()
                        ffmpeg_process.wait(timeout=1)
                    except:
                        pass
                    ffmpeg_process = None
            
    except KeyboardInterrupt:
        logger.info("Stopping service...")
        video_source.stop()
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        exit(1)
    finally:
        if ffmpeg_process:
            ffmpeg_process.stdin.close()
            ffmpeg_process.wait()
        if inference_client:
            inference_client.close()

if __name__ == "__main__":
    main()

