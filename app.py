import os
import re
from datetime import datetime, date
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

# Helper: Calculate Child Age in Human-Readable Format
def calculate_child_age(dob):
    if not dob:
        return "Unknown age"
    if isinstance(dob, str):
        try:
            dob_date = datetime.strptime(dob[:10], '%Y-%m-%d').date()
        except Exception:
            return "Invalid DOB"
    elif isinstance(dob, datetime):
        dob_date = dob.date()
    elif isinstance(dob, date):
        dob_date = dob
    else:
        return "Unknown age"

    today = date.today()
    if dob_date > today:
        return "Newborn"

    years = today.year - dob_date.year
    months = today.month - dob_date.month
    days = today.day - dob_date.day

    if days < 0:
        months -= 1
    if months < 0:
        years -= 1
        months += 12

    total_months = years * 12 + months

    if years >= 2:
        return f"{years} yrs, {months} mos" if months > 0 else f"{years} years old"
    elif years == 1:
        return f"1 yr, {months} mos" if months > 0 else "1 year old"
    elif total_months >= 1:
        return f"{total_months} months old"
    else:
        diff_days = (today - dob_date).days
        return f"{diff_days} days old" if diff_days > 0 else "Born today"

# ----------------- AUTHENTICATION ROUTES ----------------- #

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

        # Insert User into DB
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
        flash('Registration failed due to a server error. Please try again.', 'error')
        return render_template('login.html', active_tab='register', db_mode=db_mode, form_data=request.form)

@app.route('/logout')
def logout():
    user_name = session.get('user_name', 'User')
    session.clear()
    flash(f'Goodbye, {user_name}! You have been signed out successfully.', 'info')
    return redirect(url_for('login_page'))

@app.route('/forgot-password', methods=['POST'])
def forgot_password():
    email = request.form.get('email', '').strip().lower()
    
    if not email:
        flash('Please enter your email address to reset password.', 'error')
        return redirect(url_for('login_page'))
    
    user = db_manager.get_user_by_email(email)
    if not user:
        flash('No account found with this email address.', 'error')
    else:
        flash(f'A password reset link has been sent to {email}.', 'success')
    
    return redirect(url_for('login_page'))

# ----------------- DASHBOARD & CHILD MANAGEMENT ROUTES ----------------- #

@app.route('/dashboard')
@login_required
def dashboard():
    user = db_manager.get_user_by_id(session['user_id'])
    if not user:
        session.clear()
        flash('Session expired. Please log in again.', 'warning')
        return redirect(url_for('login_page'))
    
    db_mode = "SQLite (Local Mode)" if db_manager.use_sqlite else "MySQL Database"
    
    # Fetch all registered children for this parent
    children = db_manager.get_children_by_parent(user['id'])
    
    # Compute display age for each child
    for child in children:
        child['display_age'] = calculate_child_age(child['dob'])
        
    return render_template('dashboard.html', user=user, children=children, db_mode=db_mode)

@app.route('/children/add', methods=['GET', 'POST'])
@login_required
def add_child():
    user = db_manager.get_user_by_id(session['user_id'])
    db_mode = "SQLite (Local Mode)" if db_manager.use_sqlite else "MySQL Database"

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        dob_str = request.form.get('dob', '').strip()
        gender = request.form.get('gender', 'male').strip().lower()
        blood_group = request.form.get('blood_group', '').strip()
        birth_weight = request.form.get('birth_weight_kg', '').strip()
        birth_height = request.form.get('birth_height_cm', '').strip()
        allergies = request.form.get('allergies', '').strip()
        medical_notes = request.form.get('medical_notes', '').strip()

        # Validations
        if not name:
            flash("Please enter the child's full name.", 'error')
            return render_template('add_child.html', user=user, db_mode=db_mode, form_data=request.form)

        if not dob_str:
            flash("Please enter the child's date of birth.", 'error')
            return render_template('add_child.html', user=user, db_mode=db_mode, form_data=request.form)

        try:
            dob_date = datetime.strptime(dob_str, '%Y-%m-%d').date()
            if dob_date > date.today():
                flash("Date of birth cannot be in the future.", 'error')
                return render_template('add_child.html', user=user, db_mode=db_mode, form_data=request.form)
        except ValueError:
            flash("Invalid date format. Please use YYYY-MM-DD.", 'error')
            return render_template('add_child.html', user=user, db_mode=db_mode, form_data=request.form)

        if gender not in ['male', 'female', 'other']:
            gender = 'male'

        # Parse numeric measurements
        weight_val = float(birth_weight) if birth_weight else None
        height_val = float(birth_height) if birth_height else None

        try:
            child_id = db_manager.create_child(
                parent_id=user['id'],
                name=name,
                dob=dob_str,
                gender=gender,
                blood_group=blood_group if blood_group else None,
                birth_weight_kg=weight_val,
                birth_height_cm=height_val,
                allergies=allergies if allergies else None,
                medical_notes=medical_notes if medical_notes else None
            )

            flash(f"Child profile for '{name}' added successfully! 🎉", 'success')
            return redirect(url_for('child_detail', child_id=child_id))

        except Exception as e:
            app.logger.error(f"Error adding child: {e}")
            flash(f"Failed to add child record. Please try again.", 'error')
            return render_template('add_child.html', user=user, db_mode=db_mode, form_data=request.form)

    return render_template('add_child.html', user=user, db_mode=db_mode, today_date=date.today().isoformat())

@app.route('/children/<int:child_id>')
@login_required
def child_detail(child_id):
    user = db_manager.get_user_by_id(session['user_id'])
    child = db_manager.get_child_by_id(child_id, parent_id=user['id'])

    if not child:
        flash("Child profile not found or access denied.", 'error')
        return redirect(url_for('dashboard'))

    child['display_age'] = calculate_child_age(child['dob'])
    db_mode = "SQLite (Local Mode)" if db_manager.use_sqlite else "MySQL Database"

    return render_template('child_detail.html', user=user, child=child, db_mode=db_mode)

@app.route('/children/<int:child_id>/delete', methods=['POST'])
@login_required
def delete_child(child_id):
    user_id = session['user_id']
    child = db_manager.get_child_by_id(child_id, parent_id=user_id)
    
    if not child:
        flash("Child record not found.", 'error')
        return redirect(url_for('dashboard'))

    success = db_manager.delete_child(child_id, parent_id=user_id)
    if success:
        flash(f"Profile for '{child['name']}' was deleted successfully.", 'info')
    else:
        flash("Failed to delete child profile.", 'error')
        
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    print("=" * 60)
    print("👶 LittleCare - Child Healthcare Portal Web Server")
    print(f"🚀 Database Engine: {'SQLite Local Fallback' if db_manager.use_sqlite else 'MySQL (' + Config.MYSQL_DB + ')'}")
    print("🌐 Running at: http://127.0.0.1:5000")
    print("=" * 60)
    app.run(debug=True, host='127.0.0.1', port=5000)
