from flask import Flask, render_template, request, redirect, url_for, flash, session, Response
import sqlite3
import json
import os
from werkzeug.security import generate_password_hash, check_password_hash
from modules.camera.streaming import StreamingOutput
import cv2
import time

app = Flask(__name__, template_folder='../../templates', static_folder='../../static')
app.secret_key = "picodersecuritycontrol"
DB_PATH = os.path.join(os.path.dirname(__file__), '../../data/database.db')
JSON_PATH = os.path.join(os.path.dirname(__file__), '../../config/users.json')

# Initialize camera
camera = None

def init_camera():
    """Initialize the camera"""
    global camera
    try:
        camera = StreamingOutput()
        print("Camera initialized successfully")
    except Exception as e:
        print(f"Failed to initialize camera: {e}")
        camera = None

def cleanup_camera():
    """Cleanup camera on app shutdown"""
    global camera
    if camera:
        camera.stop()
        
atexit.register(cleanup_camera)


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        conn.commit()

def save_to_json(username, password):
    data = []
    if os.path.exists(JSON_PATH):
        with open(JSON_PATH, 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []

    data.append({'username': username, 'password': password})  # Plain password for demo only

    with open(JSON_PATH, 'w') as f:
        json.dump(data, f, indent=4)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT password FROM users WHERE username = ?', (username,))
            user = cursor.fetchone()

            if user and check_password_hash(user[0], password):
                session['username'] = username
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password', 'error')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                hashed_password = generate_password_hash(password)
                cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)',
                             (username, hashed_password))
                conn.commit()

                save_to_json(username, password)
                flash('Registration successful! Please login.', 'success')
                return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already exists', 'error')

    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        return render_template('dashboard.html', username=session['username'])
    return redirect(url_for('login'))

def video_feed():
    """Video streaming route"""
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if camera is None:
        return "Camera not available", 503
    
    return Response(gen_frames(), 
                   mimetype='multipart/x-mixed-replace; boundary=frame')

def gen_frames():
    """Generate video frames for streaming"""
    global camera
    
    while True:
        if camera is None:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + 
                   create_error_frame() + b'\r\n')
            time.sleep(1)
            continue
            
        try:
            frame = camera.get_frame()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        except Exception as e:
            print(f"Error getting frame: {e}")
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + 
                   create_error_frame() + b'\r\n')
        
        time.sleep(1/30)  # 30 FPS

def create_error_frame():
    """Create an error frame when camera is not available"""
    import numpy as np
    
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.putText(img, 'Camera Error', (220, 220), 
               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    cv2.putText(img, 'Please check camera connection', (150, 260), 
               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    
    _, buffer = cv2.imencode('.jpg', img)
    return buffer.tobytes()
  

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out', 'success')
    return redirect(url_for('login'))
