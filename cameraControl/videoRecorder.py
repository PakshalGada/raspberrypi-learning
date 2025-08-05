from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FileOutput
from datetime import datetime
import time
import threading
import os
import sys

class VideoRecorder:
    def __init__(self):
        self.camera = Picamera2()
        self.encoder = H264Encoder(bitrate=10000000)  # 10Mbps bitrate
        self.is_recording = False
        self.recording_thread = None
        
        # Create videos directory if it doesn't exist
        os.makedirs('videos', exist_ok=True)
        
    def _progress_bar(self, current, total, width=20):
        """Create a progress bar string"""
        filled = int(width * current / total)
        bar = '█' * filled + '─' * (width - filled)
        return f"[{bar}] {current}/{total}s"
    
    def _recording_progress(self, duration, filename):
        """Display recording progress in real-time"""
        start_time = time.time()
        
        while self.is_recording and (time.time() - start_time) < duration:
            elapsed = int(time.time() - start_time)
            remaining = duration - elapsed
            
            # Clear line and show progress
            sys.stdout.write('\r' + ' ' * 60)  # Clear line
            sys.stdout.write(f'\rRecording: {self._progress_bar(elapsed, duration)} ({remaining}s remaining)')
            sys.stdout.flush()
            
            time.sleep(1)
        
        if self.is_recording:
            sys.stdout.write('\r' + ' ' * 60)  # Clear line
            sys.stdout.write(f'\rRecording: {self._progress_bar(duration, duration)} Complete!')
            sys.stdout.flush()
            print()  # New line
    
    def record_video(self, duration=10, resolution=(1920, 1080), fps=30):
        """
        Record a video for specified duration
        
        Args:
            duration: recording duration in seconds
            resolution: tuple (width, height)
            fps: frames per second
        """
        try:
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"video_{timestamp}.mp4"
            filepath = os.path.join('videos', filename)
            
            # Configure camera for video recording
            video_config = self.camera.create_video_configuration(
                main={"size": resolution},
                controls={"FrameRate": fps}
            )
            self.camera.configure(video_config)
            
            print(f"Starting video recording...")
            print(f"Resolution: {resolution[0]}x{resolution[1]} @ {fps}fps")
            print(f"Duration: {duration} seconds")
            print(f"Output: {filename}")
            print("-" * 50)
            
            # Start camera and recording
            self.camera.start()
            time.sleep(2)  # Allow camera to settle
            
            output = FileOutput(filepath)
            self.camera.start_recording(self.encoder, output)
            self.is_recording = True
            
            # Start progress display in separate thread
            progress_thread = threading.Thread(
                target=self._recording_progress, 
                args=(duration, filename)
            )
            progress_thread.start()
            
            # Record for specified duration
            time.sleep(duration)
            
            # Stop recording
            self.is_recording = False
            self.camera.stop_recording()
            self.camera.stop()
            
            # Wait for progress thread to finish
            progress_thread.join()
            
            print(f"\n✓ Video saved: {filename}")
            print(f"  Duration: {duration} seconds")
            print(f"  Resolution: {resolution[0]}x{resolution[1]}")
            print(f"  Frame rate: {fps} fps")
            
            return filepath
            
        except Exception as e:
            print(f"\nError recording video: {e}")
            self.is_recording = False
            if self.camera.started:
                self.camera.stop()
            return None
    
    def record_multiple_formats(self):
        """Record videos in different formats for testing"""
        formats = [
            {'resolution': (1920, 1080), 'fps': 30, 'name': 'Full HD 30fps'},
            {'resolution': (1280, 720), 'fps': 30, 'name': 'HD 30fps'},
            {'resolution': (640, 480), 'fps': 30, 'name': 'VGA 30fps'},
            {'resolution': (1920, 1080), 'fps': 60, 'name': 'Full HD 60fps'},
        ]
        
        print("Recording multiple video formats...")
        print("=" * 50)
        
        for i, fmt in enumerate(formats, 1):
            print(f"\n[{i}/{len(formats)}] Recording {fmt['name']}...")
            self.record_video(
                duration=10, 
                resolution=fmt['resolution'], 
                fps=fmt['fps']
            )
            
            if i < len(formats):
                print("\nPausing 3 seconds before next recording...")
                time.sleep(3)
        
        print(f"\n🎉 All {len(formats)} videos recorded successfully!")
    
    def custom_recording(self):
        """Interactive custom recording setup"""
        print("\nCustom Video Recording Setup")
        print("-" * 30)
        
        # Get duration
        while True:
            try:
                duration = int(input("Recording duration (seconds, 5-60): "))
                if 5 <= duration <= 60:
                    break
                else:
                    print("Duration must be between 5 and 60 seconds")
            except ValueError:
                print("Please enter a valid number")
        
        # Get resolution
        print("\nAvailable resolutions:")
        print("1. 1920x1080 (Full HD)")
        print("2. 1280x720 (HD)")
        print("3. 640x480 (VGA)")
        print("4. 3840x2160 (4K) - if supported")
        
        res_choice = input("Select resolution (1-4): ").strip()
        res_map = {
            '1': (1920, 1080),
            '2': (1280, 720),
            '3': (640, 480),
            '4': (3840, 2160)
        }
        
        if res_choice not in res_map:
            print("Invalid choice, using Full HD")
            resolution = (1920, 1080)
        else:
            resolution = res_map[res_choice]
        
        # Get frame rate
        print("\nAvailable frame rates:")
        print("1. 24 fps (Cinema)")
        print("2. 30 fps (Standard)")
        print("3. 60 fps (Smooth)")
        
        fps_choice = input("Select frame rate (1-3): ").strip()
        fps_map = {'1': 24, '2': 30, '3': 60}
        
        if fps_choice not in fps_map:
            print("Invalid choice, using 30 fps")
            fps = 30
        else:
            fps = fps_map[fps_choice]
        
        # Confirm settings
        print(f"\nRecording Settings:")
        print(f"  Duration: {duration} seconds")
        print(f"  Resolution: {resolution[0]}x{resolution[1]}")
        print(f"  Frame rate: {fps} fps")
        
        confirm = input("\nProceed with recording? (y/n): ").strip().lower()
        if confirm == 'y':
            self.record_video(duration, resolution, fps)
        else:
            print("Recording cancelled")

def main():
    """Main execution function"""
    recorder = VideoRecorder()
    
    print("PiCamera2 Video Recording System")
    print("=" * 40)
    
    while True:
        print("\nOptions:")
        print("1. Quick 10-second recording (Full HD)")
        print("2. Custom recording settings")
        print("3. Record multiple formats")
        print("4. Exit")
        
        choice = input("\nSelect option (1-4): ").strip()
        
        if choice == '1':
            print("\nStarting quick 10-second Full HD recording...")
            recorder.record_video(duration=10, resolution=(1920, 1080), fps=30)
            
        elif choice == '2':
            recorder.custom_recording()
            
        elif choice == '3':
            recorder.record_multiple_formats()
            
        elif choice == '4':
            print("Goodbye!")
            break
            
        else:
            print("Invalid choice, please try again")

if __name__ == "__main__":
    main()
