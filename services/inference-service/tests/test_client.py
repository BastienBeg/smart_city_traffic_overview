import grpc
import os
import sys
import numpy as np
import cv2

# Add src to path to import generated protos
sys.path.append(os.path.join(os.path.dirname(__file__), '../src'))

import inference_pb2
import inference_pb2_grpc

def run():
    print("Connecting to inference service at localhost:50051...")
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = inference_pb2_grpc.InferenceServiceStub(channel)
        
        # Create a dummy image (black square)
        # 640x640 is standard YOLO input size
        img = np.zeros((640, 640, 3), dtype=np.uint8)
        
        # Draw a white rectangle to simulate an object (maybe unlikely to be detected without training, but ensures image flows)
        cv2.rectangle(img, (100, 100), (200, 200), (255, 255, 255), -1)
        
        _, img_encoded = cv2.imencode('.jpg', img)
        image_bytes = img_encoded.tobytes()
        
        print(f"Sending request with {len(image_bytes)} bytes...")
        try:
            response = stub.Detect(inference_pb2.DetectRequest(image_data=image_bytes), timeout=10)
            
            print("Response received:")
            for det in response.detections:
                print(f"  Class: {det.class_name} ({det.class_id}), Conf: {det.confidence:.2f}, Box: [{det.x1:.1f}, {det.y1:.1f}, {det.x2:.1f}, {det.y2:.1f}]")
            
            if not response.detections:
                print("No detections (expected for blank image).")
            
            print("Verification successful: gRPC call completed without error.")

        except grpc.RpcError as e:
            print(f"RPC failed: {e}")

if __name__ == '__main__':
    run()
