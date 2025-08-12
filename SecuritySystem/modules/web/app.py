from flask import Flask, render_template, request, redirect, url_for, flash, session, Response, jsonify
import sqlite3, json, os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from modules.camera.streaming import generate_frames, picam2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FileOutput

app = Flask(__name__, template_folder='../../templates', static_folder='../../static')
app.secret_key = "picodersecuritycontrol"

DB_PATH = os.path.join(os.path.dirname(__file__), '../../data/database.db')
JSON_PATH = os.path.join(os.path.dirname(__file__), '../../config/users.json')

is_recording = False
video_output = None

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
    data.append({'username': username, 'password': password})
    os.makedirs(os.path.dirname(JSON_PATH), exist_ok=True)
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
                hashed_password = generate_password_hash(password, method="pbkdf2:sha256")
                cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
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

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/capture')
def capture():
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = os.path.join('data', 'photos', f'photo_{timestamp}.jpg')
        picam2.capture_file(filename)
        return jsonify(message=f"Photo saved: {filename}")
    except Exception as e:
        return jsonify(message=f"Error: {e}"), 500

@app.route('/record')
def record():
    global is_recording, video_output
    try:
        if not is_recording:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = os.path.join('data', 'videos', f'video_{timestamp}.h264')
            encoder = H264Encoder()
            video_output = FileOutput(filename)
            picam2.start_recording(encoder, video_output)
            is_recording = True
            return jsonify(message=f"Recording started: {filename}")
        else:
            picam2.stop_recording()
            is_recording = False
            return jsonify(message="Recording stopped and saved.")
    except Exception as e:
        return jsonify(message=f"Error: {e}"), 500

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

