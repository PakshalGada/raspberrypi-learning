from flask import Flask, Response, render_template, jsonify
import subprocess
import threading
import time
import signal
import sys
import cv2
import numpy as np
import os
import RPi.GPIO as GPIO

app = Flask(__name__)

# Set up GPIO for LED and HC-SR04
LED_PIN = 18
TRIG_PIN = 23
ECHO_PIN = 24
GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_PIN, GPIO.OUT)
GPIO.setup(TRIG_PIN, GPIO.OUT)
GPIO.setup(ECHO_PIN, GPIO.IN)
GPIO.output(LED_PIN, GPIO.LOW)  # LED off initially
GPIO.output(TRIG_PIN, GPIO.LOW)  # Trigger off initially

class LibCameraStream:
    def __init__(self):
        self.process = None
        self.running = False
        self.thread = None
        self.zoom_level = 1.0  # Initial zoom level (1.0 = no zoom)
        self.max_zoom = 3.0   # Maximum zoom level
        self.min_zoom = 1.0   # Minimum zoom level
        self.zoom_step = 0.2  # Zoom increment/decrement
        self.frame_lock = threading.Lock()  # Thread-safe zoom level access
        self.current_frame = None  # Store current frame for snapshots
        self.frame_ready = threading.Event()  # Event to signal frame availability

    def start_stream(self):
        """Start the camera streaming using rpicam-vid"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.stream_video)
            self.thread.daemon = True
            self.thread.start()
            print("LibCamera stream started")

    def stop_stream(self):
        """Stop the camera streaming"""
        self.running = False
        if self.process:
            self.process.terminate()
            self.process.wait()
            self.process = None
        if self.thread:
            self.thread.join()
        print("LibCamera stream stopped")

    def stream_video(self):
        """Stream video using rpicam-vid"""
        cmd = [
            'rpicam-vid',
            '--timeout', '0',  # Run indefinitely
            '--width', '640',
            '--height', '480',
            '--framerate', '30',
            '--output', '-',  # Output to stdout
            '--codec', 'mjpeg',
            '--quality', '80',
            '--flush'  # Force flush of output
        ]

        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,  # Capture stderr for debugging
                bufsize=0
            )
            print("rpicam-vid process started")
            # Check stderr for errors
            stderr_thread = threading.Thread(target=self.log_stderr)
            stderr_thread.daemon = True
            stderr_thread.start()
        except Exception as e:
            print(f"Error starting rpicam-vid: {e}")
            self.running = False

    def log_stderr(self):
        """Log stderr from rpicam-vid"""
        while self.running and self.process:
            try:
                line = self.process.stderr.readline().decode('utf-8').strip()
                if line:
                    print(f"rpicam-vid stderr: {line}")
            except:
                break

    def apply_zoom(self, frame):
        """Apply digital zoom to the frame"""
        with self.frame_lock:
            zoom = self.zoom_level
        if zoom == 1.0:
            return frame

        height, width = frame.shape[:2]
        new_width = int(width / zoom)
        new_height = int(height / zoom)
        x_offset = (width - new_width) // 2
        y_offset = (height - new_height) // 2

        # Crop the frame to simulate zoom
        cropped = frame[y_offset:y_offset + new_height, x_offset:x_offset + new_width]
        # Resize back to original dimensions
        zoomed = cv2.resize(cropped, (width, height), interpolation=cv2.INTER_LINEAR)
        return zoomed

    def save_snapshot(self):
        """Capture and save a single frame as a snapshot"""
        if not self.running or not self.process:
            print("Cannot take snapshot: Stream not running")
            return False

        # Wait for a frame to be available (with timeout)
        if not self.frame_ready.wait(timeout=2.0):
            print("Timeout waiting for frame")
            return False

        try:
            with self.frame_lock:
                if self.current_frame is None:
                    print("No current frame available")
                    return False
                
                # Copy the current frame
                frame = self.current_frame.copy()

            # Create photo directory if it doesn't exist
            os.makedirs("static/photo", exist_ok=True)
            
            # Save the frame
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"static/photo/snapshot_{timestamp}.jpg"
            
            success = cv2.imwrite(filename, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
            if success:
                print(f"Snapshot saved as {filename}")
                return True
            else:
                print("Failed to write image file")
                return False
                
        except Exception as e:
            print(f"Error saving snapshot: {e}")
            return False

    def find_jpeg_boundaries(self, buffer):
        """Find JPEG frame boundaries in buffer"""
        frames = []
        start_marker = b'\xff\xd8'
        end_marker = b'\xff\xd9'
        
        pos = 0
        while pos < len(buffer):
            # Find start of JPEG
            start_pos = buffer.find(start_marker, pos)
            if start_pos == -1:
                break
                
            # Find end of JPEG
            end_pos = buffer.find(end_marker, start_pos + 2)
            if end_pos == -1:
                break
                
            # Extract complete JPEG frame
            frame_data = buffer[start_pos:end_pos + 2]
            frames.append(frame_data)
            pos = end_pos + 2
            
        return frames, buffer[pos:]  # Return frames and remaining buffer

    def generate_frames(self):
        """Generate frames for streaming"""
        if not self.process:
            print("No rpicam-vid process running")
            return

        buffer = b''
        frame_count = 0

        try:
            while self.running and self.process and self.process.poll() is None:
                try:
                    chunk = self.process.stdout.read(8192)  # Larger buffer
                    if not chunk:
                        print("No more data from rpicam-vid")
                        break

                    buffer += chunk
                    
                    # Process complete JPEG frames
                    frames, buffer = self.find_jpeg_boundaries(buffer)
                    
                    for frame_data in frames:
                        if not self.running:
                            break
                            
                        # Decode frame
                        nparr = np.frombuffer(frame_data, np.uint8)
                        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                        
                        if frame is None:
                            continue

                        # Apply digital zoom and mirror effect
                        frame = self.apply_zoom(frame)
                        frame = cv2.flip(frame, 1)  # Horizontal flip
                        
                        # Store current frame for snapshots
                        with self.frame_lock:
                            self.current_frame = frame.copy()
                            self.frame_ready.set()
                        
                        # Encode for streaming
                        ret, encoded = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                        if not ret:
                            continue
                            
                        frame_data = encoded.tobytes()
                        frame_count += 1
                        
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')
                        
                except Exception as e:
                    print(f"Error processing frame: {e}")
                    continue

        except Exception as e:
            print(f"Error in frame generation: {e}")
        
        print(f"Generated {frame_count} frames")

# Ultrasonic sensor management
class UltrasonicSensor:
    def __init__(self):
        self.armed = False
        self.distance = None
        self.thread = None
        self.running = False
        self.lock = threading.Lock()

    def measure_distance(self):
        """Measure distance using HC-SR04"""
        try:
            # Send trigger pulse
            GPIO.output(TRIG_PIN, GPIO.HIGH)
            time.sleep(0.00001)  # 10us pulse
            GPIO.output(TRIG_PIN, GPIO.LOW)

            # Wait for echo start
            while GPIO.input(ECHO_PIN) == 0:
                pulse_start = time.time()

            # Wait for echo end
            while GPIO.input(ECHO_PIN) == 1:
                pulse_end = time.time()

            # Calculate distance
            pulse_duration = pulse_end - pulse_start
            distance = pulse_duration * 17150  # Speed of sound = 343m/s, distance in cm
            distance = round(distance, 2)

            with self.lock:
                self.distance = distance
            return distance
        except:
            return None

    def start_measuring(self):
        """Start measuring distance in a separate thread"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.measure_loop)
            self.thread.daemon = True
            self.thread.start()
            print("Ultrasonic sensor started")

    def measure_loop(self):
        """Continuously measure distance while armed"""
        while self.running:
            if self.armed:
                self.measure_distance()
            time.sleep(0.1)  # Measure every 100ms
            if not self.armed:
                with self.lock:
                    self.distance = None

    def stop_measuring(self):
        """Stop measuring distance"""
        self.running = False
        if self.thread:
            self.thread.join()
        with self.lock:
            self.distance = None
        print("Ultrasonic sensor stopped")

# Global instances
camera_stream = LibCameraStream()
ultrasonic_sensor = UltrasonicSensor()

@app.route('/')
def index():
    """Main page with video stream and initial image gallery"""
    photo_dir = 'static/photo'
    images = []
    if os.path.exists(photo_dir):
        images = [f for f in os.listdir(photo_dir) if f.endswith('.jpg')]
        images.sort(reverse=True)  # Sort by newest first
    return render_template('index.html', images=images)

@app.route('/get_images')
def get_images():
    """Return list of images in the photo folder as JSON"""
    photo_dir = 'static/photo'
    images = []
    if os.path.exists(photo_dir):
        images = [f for f in os.listdir(photo_dir) if f.endswith('.jpg')]
        images.sort(reverse=True)  # Sort by newest first
    return jsonify(images)

@app.route('/get_distance')
def get_distance():
    """Return the latest distance measurement"""
    with ultrasonic_sensor.lock:
        distance = ultrasonic_sensor.distance
    if distance is None:
        return jsonify({"distance": null})
    return jsonify({"distance": distance})

@app.route('/video_feed')
def video_feed():
    """Video streaming route"""
    return Response(camera_stream.generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/zoom_in')
def zoom_in():
    """Increase zoom level"""
    with camera_stream.frame_lock:
        if camera_stream.zoom_level < camera_stream.max_zoom:
            camera_stream.zoom_level = min(camera_stream.zoom_level + camera_stream.zoom_step, camera_stream.max_zoom)
            print(f"Zoomed in to {camera_stream.zoom_level}x")
    return f"Zoom level: {camera_stream.zoom_level}x"

@app.route('/zoom_out')
def zoom_out():
    """Decrease zoom level"""
    with camera_stream.frame_lock:
        if camera_stream.zoom_level > camera_stream.min_zoom:
            camera_stream.zoom_level = max(camera_stream.zoom_level - camera_stream.zoom_step, camera_stream.min_zoom)
            print(f"Zoomed out to {camera_stream.zoom_level}x")
    return f"Zoom level: {camera_stream.zoom_level}x"

@app.route('/arm')
def arm():
    """Arm the system: start ultrasonic sensor and turn LED on"""
    ultrasonic_sensor.armed = True
    GPIO.output(LED_PIN, GPIO.HIGH)
    print("System armed: Ultrasonic sensor on, LED on")
    return "System armed"

@app.route('/disarm')
def disarm():
    """Disarm the system: stop ultrasonic sensor and turn LED off"""
    ultrasonic_sensor.armed = False
    GPIO.output(LED_PIN, GPIO.LOW)
    print("System disarmed: Ultrasonic sensor off, LED off")
    return "System disarmed"

@app.route('/take_picture')
def take_picture():
    """Take a snapshot and save it"""
    if camera_stream.save_snapshot():
        return "Snapshot taken successfully"
    return "Failed to take snapshot"

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\nShutting down...")
    camera_stream.stop_stream()
    ultrasonic_sensor.stop_measuring()
    GPIO.cleanup()  # Clean up GPIO pins
    sys.exit(0)

if __name__ == '__main__':
    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)

    try:
        print("Starting LibCamera Flask App...")
        print("If this doesn't work, try running:")
        print("rpicam-hello --list-cameras")
        print("to check if your camera is detected")

        # Start camera and ultrasonic sensor
        camera_stream.start_stream()
        ultrasonic_sensor.start_measuring()

        # Run Flask app
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)

    except Exception as e:
        print(f"Error starting application: {e}")
    finally:
        camera_stream.stop_stream()
        ultrasonic_sensor.stop_measuring()
        GPIO.cleanup()
