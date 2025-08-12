import io
import os
from datetime import datetime
from threading import Condition
from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder, H264Encoder
from picamera2.outputs import FileOutput

# Create directories
os.makedirs('data/photos', exist_ok=True)
os.makedirs('data/videos', exist_ok=True)

class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()

picam2 = Picamera2()
video_config = picam2.create_video_configuration(main={"size": (1280, 960)})
picam2.configure(video_config)
output = StreamingOutput()
picam2.start()

def generate_frames():
    encoder = JpegEncoder()
    picam2.start_recording(encoder, FileOutput(output))
    while True:
        with output.condition:
            output.condition.wait()
            frame = output.frame
        yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame + b'\r\n'

