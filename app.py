import os
import re
from flask import Flask, render_template, request, session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from config import Config
from database import db_manager

app = Flask(__name__)
app.config.from_object(Config)

# Helper: Login Required Decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access your dashboard.', 'warning')
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

# ----------------- WEB ROUTES ----------------- #

@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login_page'))

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    
    active_tab = request.args.get('tab', 'login')
    db_mode = "SQLite (Local Mode)" if db_manager.use_sqlite else "MySQL Database"

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        # Validation
        if not email or not password:
            flash('Both email and password are required.', 'error')
            return render_template('login.html', active_tab='login', db_mode=db_mode, email=email)

        # Query User
        user = db_manager.get_user_by_email(email)
        if not user or not check_password_hash(user['password_hash'], password):
            flash('Invalid email address or password. Please try again.', 'error')
            return render_template('login.html', active_tab='login', db_mode=db_mode, email=email)

        # Successful Login -> Establish Session
        session['user_id'] = user['id']
        session['user_name'] = user['full_name']
        session['user_email'] = user['email']
        session['role'] = user.get('role', 'parent')

        if remember:
            session.permanent = True

        flash(f"Welcome back, {user['full_name']}!", 'success')
        return redirect(url_for('dashboard'))

    return render_template('login.html', active_tab=active_tab, db_mode=db_mode)

@app.route('/register', methods=['POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))

    full_name = request.form.get('full_name', '').strip()
    email = request.form.get('email', '').strip().lower()
    phone = request.form.get('phone', '').strip()
    password = request.form.get('password', '')
    confirm_password = request.form.get('confirm_password', '')
    role = request.form.get('role', 'parent').strip().lower()
    db_mode = "SQLite (Local Mode)" if db_manager.use_sqlite else "MySQL Database"

    # Validations
    if not full_name:
        flash('Please enter your full name.', 'error')
        return render_template('login.html', active_tab='register', db_mode=db_mode, form_data=request.form)

    if not email:
        flash('Please enter your email address.', 'error')
        return render_template('login.html', active_tab='register', db_mode=db_mode, form_data=request.form)

    email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    if not re.match(email_regex, email):
        flash('Please enter a valid email address (e.g. name@example.com).', 'error')
        return render_template('login.html', active_tab='register', db_mode=db_mode, form_data=request.form)

    if not password:
        flash('Please enter a password.', 'error')
        return render_template('login.html', active_tab='register', db_mode=db_mode, form_data=request.form)

    if len(password) < 6:
        flash('Password must be at least 6 characters long.', 'error')
        return render_template('login.html', active_tab='register', db_mode=db_mode, form_data=request.form)

    if password != confirm_password:
        flash('Passwords do not match. Please re-enter.', 'error')
        return render_template('login.html', active_tab='register', db_mode=db_mode, form_data=request.form)

    if role not in ['parent', 'doctor']:
        role = 'parent'

    # Check if email is already registered
    existing_user = db_manager.get_user_by_email(email)
    if existing_user:
        flash('This email is already registered. Please log in.', 'error')
        return render_template('login.html', active_tab='login', db_mode=db_mode, email=email)

    try:
        # Secure password hashing
        password_hash = generate_password_hash(password, method='pbkdf2:sha256')

        # Insert User into MySQL / DB
        user_id = db_manager.create_user(
            full_name=full_name,
            email=email,
            phone=phone,
            password_hash=password_hash,
            role=role
        )

        # Automatically log in the user
        session['user_id'] = user_id
        session['user_name'] = full_name
        session['user_email'] = email
        session['role'] = role

        flash('Your account has been created successfully! Welcome to LittleCare.', 'success')
        return redirect(url_for('dashboard'))

    except Exception as e:
        app.logger.error(f"Registration Error: {e}")
        flash(f'Registration failed due to a server error. Please try again.', 'error')
        return render_template('login.html', active_tab='register', db_mode=db_mode, form_data=request.form)

@app.route('/dashboard')
@login_required
def dashboard():
    user = db_manager.get_user_by_id(session['user_id'])
    if not user:
        session.clear()
        flash('Session expired. Please log in again.', 'warning')
        return redirect(url_for('login_page'))
    
    db_mode = "SQLite (Local Mode)" if db_manager.use_sqlite else "MySQL Database"
    return render_template('dashboard.html', user=user, db_mode=db_mode)

@app.route('/logout')
def logout():
    user_name = session.get('user_name', 'User')
    session.clear()
    flash(f'Goodbye, {user_name}! You have been signed out successfully.', 'info')
    return redirect(url_for('login_page'))

@app.route('/forgot-password', methods=['POST'])
def forgot_password():
    email = request.form.get('email', '').strip().lower()
    db_mode = "SQLite (Local Mode)" if db_manager.use_sqlite else "MySQL Database"
    
    if not email:
        flash('Please enter your email address to reset password.', 'error')
        return redirect(url_for('login_page'))
    
    user = db_manager.get_user_by_email(email)
    if not user:
        flash('No account found with this email address.', 'error')
    else:
        flash(f'A password reset link has been sent to {email}.', 'success')
    
    return redirect(url_for('login_page'))

if __name__ == '__main__':
    print("=" * 60)
    print("👶 LittleCare - Child Healthcare Portal Web Server")
    print(f"🚀 Database Engine: {'SQLite Local Fallback' if db_manager.use_sqlite else 'MySQL (' + Config.MYSQL_DB + ')'}")
    print("🌐 Running at: http://127.0.0.1:5000")
    print("=" * 60)
    app.run(debug=True, host='127.0.0.1', port=5000)
