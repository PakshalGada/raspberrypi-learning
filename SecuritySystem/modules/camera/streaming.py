import os
import cv2
import time
import threading
from datetime import datetime
from picamera2 import Picamera2

PHOTOS_DIR = os.path.join("data", "photos")
VIDEOS_DIR = os.path.join("data", "videos")
os.makedirs(PHOTOS_DIR, exist_ok=True)
os.makedirs(VIDEOS_DIR, exist_ok=True)

picam2 = Picamera2()
config = picam2.create_preview_configuration(
    main={"size": (640, 480), "format": "BGR888"}  
)
picam2.configure(config)
picam2.start()

_lock = threading.Lock()
_current_frame = None  
_running = True

_manual_recording = False         
_motion_recording = False         
_recording_active = False         
_writer = None
_record_target_fps = 20.0
_last_write_time = 0.0
_current_video_path = None

_MOTION_MIN_AREA = 5000           
_MOTION_PERSISTENCE_S = 5.0       
_last_motion_ts = 0.0
_prev_gray = None

# Motion control variables
_motion_thread = None
_motion_running = False


def _now_ts():
    return time.time()

def _timestamp_name(prefix: str, ext: str):
    return f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"

def get_latest_frame():
    with _lock:
        if _current_frame is None:
            return None
        return _current_frame.copy()

def _open_writer(frame_shape):
    global _writer, _current_video_path, _last_write_time
    h, w = frame_shape[:2]
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    filename = _timestamp_name("video", "mp4")
    path = os.path.join(VIDEOS_DIR, filename)
    writer = cv2.VideoWriter(path, fourcc, _record_target_fps, (w, h))
    if not writer.isOpened():
        raise RuntimeError("Failed to open VideoWriter")
    _writer = writer
    _current_video_path = path
    _last_write_time = 0.0
    print(f"[REC] Started recording: {path}")

def _close_writer():
    global _writer, _current_video_path
    if _writer is not None:
        _writer.release()
        print(f"[REC] Saved recording: {_current_video_path}")
    _writer = None
    _current_video_path = None

def _update_recording_state(frame_shape):
    global _recording_active
    want_active = _manual_recording or _motion_recording
    if want_active and not _recording_active:
        _open_writer(frame_shape)
        _recording_active = True
    elif not want_active and _recording_active:
        _close_writer()
        _recording_active = False

def start_manual_recording():
    global _manual_recording
    with _lock:
        _manual_recording = True

def stop_manual_recording():
    global _manual_recording
    with _lock:
        _manual_recording = False

def is_recording():
    with _lock:
        return _recording_active

def save_photo_from_latest() -> str:
    frame = get_latest_frame()
    if frame is None:
        raise RuntimeError("No frame available to save")
    filename = _timestamp_name("photo", "jpg")
    path = os.path.join(PHOTOS_DIR, filename)
    if not cv2.imwrite(path, frame):
        raise RuntimeError("Failed to write photo")
    return path

def _camera_loop():
    global _current_frame, _last_write_time
    while _running:
        rgb = picam2.capture_array("main")
        bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)

        with _lock:
            _current_frame = bgr
            _update_recording_state(bgr.shape)

            if _recording_active and _writer is not None:
                now = _now_ts()
                if _last_write_time == 0.0 or (now - _last_write_time) >= (1.0 / _record_target_fps):
                    _writer.write(bgr)
                    _last_write_time = now

        time.sleep(0.005)

def start_motion_detection():
    global _motion_thread, _motion_running
    if _motion_running:
        return
    _motion_running = True
    _motion_thread = threading.Thread(target=_motion_loop, daemon=True)
    _motion_thread.start()
    print("[MOTION] Motion detection started.")

def stop_motion_detection():
    global _motion_running
    _motion_running = False
    print("[MOTION] Motion detection stopped.")

def _motion_loop():
    global _prev_gray, _motion_recording, _last_motion_ts, _motion_running
    while _running and _motion_running:
        frame = get_latest_frame()
        if frame is None:
            time.sleep(0.02)
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if _prev_gray is None:
            _prev_gray = gray
            time.sleep(0.05)
            continue

        delta = cv2.absdiff(_prev_gray, gray)
        thresh = cv2.threshold(delta, 25, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        motion_now = any(cv2.contourArea(c) > _MOTION_MIN_AREA for c in contours)

        with _lock:
            if motion_now:
                _motion_recording = True
                _last_motion_ts = _now_ts()
            else:
                if _motion_recording and (_now_ts() - _last_motion_ts) > _MOTION_PERSISTENCE_S:
                    _motion_recording = False

        _prev_gray = gray
        time.sleep(0.05)

def generate_frames():
    import numpy as np 
    while True:
        frame = get_latest_frame()
        if frame is None:
            time.sleep(0.01)
            continue
        ok, buf = cv2.imencode(".jpg", frame)
        if not ok:
            continue
        jpg = buf.tobytes()
        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" + jpg + b"\r\n")

_thread_cam = threading.Thread(target=_camera_loop, daemon=True)
_thread_cam.start()

