from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import json
import os
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__, template_folder='../../templates', static_folder='../../static')
app.secret_key="picodersecuritycontrol"
DB_PATH = os.path.join(os.path.dirname(__file__), '../../data/database.db')
JSON_PATH = os.path.join(os.path.dirname(__file__), '../../config/users.json')

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


@app.route('/login', methods=['GET','POST'])
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
    
@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out', 'success')
    return redirect(url_for('login'))
