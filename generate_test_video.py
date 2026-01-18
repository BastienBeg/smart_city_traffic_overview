import cv2
import numpy as np

# Create a black image
height, width = 480, 640
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
out = cv2.VideoWriter('test_video.mp4', fourcc, 20.0, (width, height))

for _ in range(60): # 3 seconds
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    out.write(frame)

out.release()
print("test_video.mp4 created")
