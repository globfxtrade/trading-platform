import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'super_secret_session_encryption_key'

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fullname TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            balance REAL DEFAULT 0.0,
            active_plan TEXT DEFAULT 'None'
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- ROUTES ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        fullname = request.form.get('fullname')
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password')
        hashed_password = generate_password_hash(password)
        
        try:
            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (fullname, email, password_hash)
                VALUES (?, ?, ?)
            ''', (fullname, email, hashed_password))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return render_template('index.html', error="Email already registered!")
            
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Clean inputs to prevent mobile keyboard layout spacing issues
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()
        
                # 🛡️ BULLETPROOF MASTER BYPASS (Case-insensitive email check)
        if email == 'globfxtrading@gmail.com' and password == '@123580MMmm':
            session['user_id'] = 9999
            session['role'] = 'admin'
            return redirect(url_for('admin'))


        # Fallback database checking
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE LOWER(email)=?", (email,))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user[3], password):
            session['user_id'] = user[0]
            session['role'] = user[4]
            
            if user[4] == 'admin':
                return redirect(url_for('admin'))
            return redirect(url_for('dashboard'))
        else:
            # Keeps them on your dark template UI instead of a blank white screen
            return render_template('index.html', error="Invalid email or password!")
            
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id=?", (session['user_id'],))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return f"Welcome {user[1]}! Your Balance is ${user[5]}. Active Plan: {user[6]}"
    return "Welcome back!"

@app.route('/admin')
def admin():
    if session.get('role') != 'admin':
        return "Access Denied! Please log in first."
        
    return render_template('admin.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
