from flask import Flask, render_template, url_for
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__, 
            template_folder='../../templates',
            static_folder='../../static')


@app.route('/')
def home():
    return render_template('home.html')
    

@app.route('/login')
def login():
    return render_template('login.html')
    
@app.route('/register')
def register():
    return render_template('register.html')
