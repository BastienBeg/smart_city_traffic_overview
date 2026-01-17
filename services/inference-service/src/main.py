import grpc
from concurrent import futures
import time
import os
import sys
import uuid
from datetime import datetime, timezone

# Ensure current directory is in path (for generated imports)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import inference_pb2
import inference_pb2_grpc
from model import InferenceModel
from event_bus import KafkaEventBus

# Global Kafka producer
event_bus: KafkaEventBus = None


class InferenceService(inference_pb2_grpc.InferenceServiceServicer):
    """
    gRPC Service implementation for Object Detection.
    """
    def __init__(self) -> None:
        """Initialize the service with an inference model."""
        self.model = InferenceModel()

    def Detect(self, request: inference_pb2.DetectRequest, context: grpc.ServicerContext) -> inference_pb2.DetectResponse:
        """
        Handle Detect RPC calls.

        Args:
            request (inference_pb2.DetectRequest): The request object containing image data.
            context (grpc.ServicerContext): The context for the RPC call.

        Returns:
            inference_pb2.DetectResponse: The response containing detection results.
        """
        global event_bus
        start_time = time.time()

        try:
            image_data = request.image_data
            if not image_data:
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                context.set_details("Empty image data")
                return inference_pb2.DetectResponse()

            detections_data = self.model.predict(image_data)
            
            response = inference_pb2.DetectResponse()
            for d in detections_data:
                det_msg = inference_pb2.Detection(
                    x1=d['x1'],
                    y1=d['y1'],
                    x2=d['x2'],
                    y2=d['y2'],
                    confidence=d['confidence'],
                    class_id=d['class_id'],
                    class_name=d['class_name']
                )
                response.detections.append(det_msg)
            
            # Publish detection event to Kafka
            if event_bus and len(detections_data) > 0:
                latency_ms = (time.time() - start_time) * 1000
                camera_id = request.camera_id if request.camera_id else "unknown"
                detection_event = {
                    "event_id": str(uuid.uuid4()),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "camera_id": camera_id,
                    "detections": detections_data,
                    "inference_latency_ms": round(latency_ms, 2),
                }
                event_bus.publish(detection_event, key=camera_id)

            return response
        except Exception as e:
            print(f"Error during detection: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            return inference_pb2.DetectResponse()


def serve():
    global event_bus
    print("Starting Inference Service...")
    
    # Initialize Kafka producer
    kafka_enabled = os.environ.get("KAFKA_ENABLED", "true").lower() == "true"
    if kafka_enabled:
        event_bus = KafkaEventBus()
        if not event_bus.connect():
            print("WARNING: Kafka connection failed. Events will not be published.")
            event_bus = None
        else:
            print("Kafka producer initialized.")
    else:
        print("Kafka publishing disabled.")

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    inference_pb2_grpc.add_InferenceServiceServicer_to_server(InferenceService(), server)
    port = os.environ.get("PORT", "50051")
    server.add_insecure_port(f'[::]:{port}')
    server.start()
    print(f"Inference Service listening on port {port}...")
    
    try:
        server.wait_for_termination()
    finally:
        if event_bus:
            event_bus.close()

if __name__ == '__main__':
    serve()

