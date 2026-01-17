"""
gRPC client module for communicating with the Inference Service.
"""
import grpc
import logging
from typing import List, Dict, Any

# These will be generated from inference.proto
# python -m grpc_tools.protoc -I./protos --python_out=./src --grpc_python_out=./src ./protos/inference.proto
import inference_pb2
import inference_pb2_grpc

logger = logging.getLogger("InferenceClient")


class InferenceClient:
    """
    gRPC client for the InferenceService.
    Sends frames and receives detection results.
    """

    def __init__(self, server_address: str):
        """
        Initializes the gRPC client.

        Args:
            server_address: Address of the inference service (e.g., "inference-service:50051").
        """
        self.server_address = server_address
        self.channel = None
        self.stub = None
        logger.info(f"Initialized InferenceClient targeting {server_address}")

    def connect(self) -> bool:
        """
        Establishes a connection to the gRPC server.

        Returns:
            True if connection is successful, False otherwise.
        """
        try:
            self.channel = grpc.insecure_channel(self.server_address)
            self.stub = inference_pb2_grpc.InferenceServiceStub(self.channel)
            # Optional: wait for connection to be ready
            grpc.channel_ready_future(self.channel).result(timeout=10)
            logger.info(f"Connected to InferenceService at {self.server_address}")
            return True
        except grpc.FutureTimeoutError:
            logger.error(f"Timeout connecting to InferenceService at {self.server_address}")
            return False
        except Exception as e:
            logger.error(f"Failed to connect to InferenceService: {e}")
            return False

    def detect(self, image_data: bytes, camera_id: str = "unknown") -> List[Dict[str, Any]]:
        """
        Sends image data to the inference service and returns detections.

        Args:
            image_data: JPEG-encoded image bytes.
            camera_id: The camera identifier for event attribution.

        Returns:
            List of detection dictionaries with keys: x1, y1, x2, y2, confidence, class_id, class_name.
        """
        if not self.stub:
            logger.error("Client not connected. Call connect() first.")
            return []

        try:
            request = inference_pb2.DetectRequest(image_data=image_data, camera_id=camera_id)
            response = self.stub.Detect(request)

            detections = []
            for det in response.detections:
                detections.append({
                    "x1": det.x1,
                    "y1": det.y1,
                    "x2": det.x2,
                    "y2": det.y2,
                    "confidence": det.confidence,
                    "class_id": det.class_id,
                    "class_name": det.class_name,
                })
            return detections
        except grpc.RpcError as e:
            logger.error(f"gRPC error during Detect: {e.code()} - {e.details()}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error during Detect: {e}")
            return []

    def close(self):
        """Closes the gRPC channel."""
        if self.channel:
            self.channel.close()
            logger.info("InferenceClient channel closed.")
