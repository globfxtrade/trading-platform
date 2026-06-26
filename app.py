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
    
    # Create default admin account if it doesn't exist
    cursor.execute("SELECT * FROM users WHERE email='admin@quantumtrade.com'")
    if not cursor.fetchone():
        admin_pass = generate_password_hash('AdminPassword123!')
        cursor.execute('''
            INSERT INTO users (fullname, email, password_hash, role, balance, active_plan)
            VALUES ('Platform Admin', 'admin@quantumtrade.com', ?, 'admin', 0.0, 'None')
        ''', (admin_pass,))
    
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
        email = request.form.get('email')
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
            return "Email already registered!"
            
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email=?", (email,))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user[3], password):
            session['user_id'] = user[0]
            session['role'] = user[4]
            
            if user[4] == 'admin':
                return redirect(url_for('admin'))
            return redirect(url_for('dashboard'))
        else:
            return "Invalid email or password!"
            
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
    
    return f"Welcome {user[1]}! Your Balance is ${user[5]}. Active Plan: {user[6]}"

@app.route('/admin')
def admin():
    # Verify the session role is set to admin
    if session.get('role') != 'admin':
        return "Access Denied! Please log in first."
        
    # Render the secure dark template admin panel
    return render_template('admin.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
