from picamera2 import Picamera2
import time

try:
    picam2 = Picamera2()
    picam2.configure(picam2.create_video_configuration(main={"size": (640, 480)}))
    picam2.start()
    print("Camera started successfully")
    time.sleep(5)
    frame = picam2.capture_array()
    print("Frame captured successfully")
    picam2.stop()
    picam2.close()
except Exception as e:
    print(f"Error: {e}")
