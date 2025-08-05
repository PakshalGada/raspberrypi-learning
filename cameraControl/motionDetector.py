import time
import os
from datetime import datetime
from picamera2 import Picamera2
import numpy as np
from PIL import Image
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration
SAVE_DIR = "/home/webbywonder/motion_captures"  # Directory to save captured images
THRESHOLD = 20  # Pixel difference threshold for motion detection
SENSITIVITY = 1000  # Number of pixels that must change to trigger motion
RESOLUTION = (640, 480)  # Camera resolution for faster processing
MIN_MOTION_FRAMES = 2  # Number of consecutive frames with motion to trigger capture

def ensure_save_directory():
    """Ensure the save directory exists."""
    if not os.path.exists(SAVE_DIR):
        os.makedirs(SAVE_DIR)
        logging.info(f"Created save directory: {SAVE_DIR}")

def capture_image(picam2, filename):
    """Capture and save an image with a timestamped filename."""
    try:
        picam2.capture_file(os.path.join(SAVE_DIR, filename))
        logging.info(f"Image captured: {filename}")
    except Exception as e:
        logging.error(f"Failed to capture image: {e}")

def main():
    # Initialize the camera
    try:
        picam2 = Picamera2()
        config = picam2.create_still_configuration(main={"size": RESOLUTION})
        picam2.configure(config)
        picam2.start()
        logging.info("Camera initialized successfully")
    except Exception as e:
        logging.error(f"Failed to initialize camera: {e}")
        return

    # Ensure save directory exists
    ensure_save_directory()

    # Allow camera to warm up
    time.sleep(2)

    # Initialize variables for motion detection
    previous_frame = None
    motion_frames = 0

    try:
        while True:
            # Capture a low-resolution frame for motion detection
            current_frame = picam2.capture_array()
            current_frame = np.array(Image.fromarray(current_frame).convert('L'))  # Convert to grayscale

            if previous_frame is not None:
                # Calculate the absolute difference between frames
                diff = np.abs(current_frame.astype(float) - previous_frame.astype(float))
                motion_pixels = np.sum(diff > THRESHOLD)

                if motion_pixels > SENSITIVITY:
                    motion_frames += 1
                    logging.info(f"Motion detected: {motion_pixels} pixels changed")
                    if motion_frames >= MIN_MOTION_FRAMES:
                        # Capture a high-quality image when motion is confirmed
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"motion_{timestamp}.jpg"
                        capture_image(picam2, filename)
                        motion_frames = 0  # Reset motion counter
                        time.sleep(1)  # Prevent multiple captures in quick succession
                else:
                    motion_frames = 0  # Reset if no motion

            previous_frame = current_frame
            time.sleep(0.1)  # Control frame rate

    except KeyboardInterrupt:
        logging.info("Stopping motion detection")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
    finally:
        picam2.stop()
        picam2.close()
        logging.info("Camera stopped and closed")

if __name__ == "__main__":
    main()  
