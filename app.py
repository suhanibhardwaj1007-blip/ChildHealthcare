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
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

# Helper: Calculate Child Age Breakdown
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

# Helper: Get Child Age in Total Months (for Growth Tracking)
def get_age_in_months(dob):
    if isinstance(dob, str):
        dob_date = datetime.strptime(dob[:10], '%Y-%m-%d').date()
    elif isinstance(dob, datetime):
        dob_date = dob.date()
    else:
        dob_date = dob
    today = date.today()
    return max(0, (today.year - dob_date.year) * 12 + (today.month - dob_date.month))

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

        if not email or not password:
            flash('Both email and password are required.', 'error')
            return render_template('login.html', active_tab='login', db_mode=db_mode, email=email)

        user = db_manager.get_user_by_email(email)
        if not user or not check_password_hash(user['password_hash'], password):
            flash('Invalid email address or password. Please try again.', 'error')
            return render_template('login.html', active_tab='login', db_mode=db_mode, email=email)

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

    existing_user = db_manager.get_user_by_email(email)
    if existing_user:
        flash('This email is already registered. Please log in.', 'error')
        return render_template('login.html', active_tab='login', db_mode=db_mode, email=email)

    try:
        password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        user_id = db_manager.create_user(
            full_name=full_name,
            email=email,
            phone=phone,
            password_hash=password_hash,
            role=role
        )

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

# ----------------- DASHBOARD & CHILD MANAGEMENT ----------------- #

@app.route('/dashboard')
@login_required
def dashboard():
    user = db_manager.get_user_by_id(session['user_id'])
    if not user:
        session.clear()
        flash('Session expired. Please log in again.', 'warning')
        return redirect(url_for('login_page'))
    
    db_mode = "SQLite (Local Mode)" if db_manager.use_sqlite else "MySQL Database"
    children = db_manager.get_children_by_parent(user['id'])
    for child in children:
        child['display_age'] = calculate_child_age(child['dob'])
        child['vac_summary'] = db_manager.get_vaccination_summary(child['id'])
        
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
            flash("Failed to add child record. Please try again.", 'error')
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
    child['vac_summary'] = db_manager.get_vaccination_summary(child_id)
    child['latest_growth'] = db_manager.get_latest_growth_record(child_id)
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

# ----------------- MODULE 3: VACCINATION TRACKER ----------------- #

@app.route('/vaccination')
@login_required
def vaccination_tracker():
    user = db_manager.get_user_by_id(session['user_id'])
    children = db_manager.get_children_by_parent(user['id'])
    db_mode = "SQLite (Local Mode)" if db_manager.use_sqlite else "MySQL Database"

    if not children:
        flash("Please register a child profile first to track immunization schedules.", "info")
        return redirect(url_for('add_child'))

    # Selected child
    child_id_param = request.args.get('child_id')
    selected_child = None
    if child_id_param:
        try:
            selected_child = db_manager.get_child_by_id(int(child_id_param), parent_id=user['id'])
        except ValueError:
            selected_child = None

    if not selected_child:
        selected_child = children[0]

    selected_child['display_age'] = calculate_child_age(selected_child['dob'])
    vaccines = db_manager.get_child_vaccinations(selected_child['id'])
    summary = db_manager.get_vaccination_summary(selected_child['id'])

    return render_template('vaccination.html', user=user, children=children, 
                           selected_child=selected_child, vaccines=vaccines, 
                           summary=summary, db_mode=db_mode)

@app.route('/vaccination/<int:vaccination_id>/toggle', methods=['POST'])
@login_required
def toggle_vaccination(vaccination_id):
    child_id = request.form.get('child_id')
    status = request.form.get('status')
    admin_date = request.form.get('administered_date') or date.today().isoformat()
    admin_by = request.form.get('administered_by')
    notes = request.form.get('notes')

    if not child_id:
        flash("Child ID is required.", "error")
        return redirect(url_for('vaccination_tracker'))

    try:
        success = db_manager.toggle_vaccination_status(
            vaccination_id=vaccination_id,
            child_id=int(child_id),
            parent_id=session['user_id'],
            status=status,
            administered_date=admin_date if status == 'completed' else None,
            administered_by=admin_by,
            notes=notes
        )
        if success:
            flash("Vaccination record updated successfully! 💉", "success")
        else:
            flash("Failed to update vaccination status.", "error")
    except Exception as e:
        app.logger.error(f"Vaccination toggle error: {e}")
        flash("Error updating vaccination status.", "error")

    return redirect(url_for('vaccination_tracker', child_id=child_id))

# ----------------- MODULE 4: GROWTH & BMI TRACKER ----------------- #

@app.route('/growth')
@login_required
def growth_tracker():
    user = db_manager.get_user_by_id(session['user_id'])
    children = db_manager.get_children_by_parent(user['id'])
    db_mode = "SQLite (Local Mode)" if db_manager.use_sqlite else "MySQL Database"

    if not children:
        flash("Please register a child profile first to track growth milestones.", "info")
        return redirect(url_for('add_child'))

    child_id_param = request.args.get('child_id')
    selected_child = None
    if child_id_param:
        try:
            selected_child = db_manager.get_child_by_id(int(child_id_param), parent_id=user['id'])
        except ValueError:
            selected_child = None

    if not selected_child:
        selected_child = children[0]

    selected_child['display_age'] = calculate_child_age(selected_child['dob'])
    records = db_manager.get_growth_records(selected_child['id'])
    latest = db_manager.get_latest_growth_record(selected_child['id'])
    current_age_months = get_age_in_months(selected_child['dob'])

    return render_template('growth.html', user=user, children=children, 
                           selected_child=selected_child, records=records, 
                           latest=latest, current_age_months=current_age_months,
                           today_date=date.today().isoformat(), db_mode=db_mode)

@app.route('/growth/add', methods=['POST'])
@login_required
def add_growth_record():
    child_id = request.form.get('child_id')
    record_date = request.form.get('record_date') or date.today().isoformat()
    weight = request.form.get('weight_kg')
    height = request.form.get('height_cm')
    head_circ = request.form.get('head_circumference_cm')
    notes = request.form.get('notes')

    if not child_id or not weight or not height:
        flash("Child, weight, and height are required for logging growth.", "error")
        return redirect(url_for('growth_tracker', child_id=child_id))

    child = db_manager.get_child_by_id(int(child_id), parent_id=session['user_id'])
    if not child:
        flash("Child profile not found.", "error")
        return redirect(url_for('growth_tracker'))

    try:
        weight_val = float(weight)
        height_val = float(height)
        head_val = float(head_circ) if head_circ else None
        age_months = get_age_in_months(child['dob'])

        db_manager.add_growth_record(
            child_id=child['id'],
            record_date=record_date,
            age_months=age_months,
            weight_kg=weight_val,
            height_cm=height_val,
            head_circumference_cm=head_val,
            notes=notes
        )
        flash("Growth measurement logged successfully! 📈", "success")
    except Exception as e:
        app.logger.error(f"Error logging growth: {e}")
        flash("Failed to log growth record. Please check values.", "error")

    return redirect(url_for('growth_tracker', child_id=child_id))

@app.route('/growth/<int:record_id>/delete', methods=['POST'])
@login_required
def delete_growth(record_id):
    child_id = request.form.get('child_id')
    if child_id:
        db_manager.delete_growth_record(record_id, int(child_id), session['user_id'])
        flash("Growth record removed.", "info")
    return redirect(url_for('growth_tracker', child_id=child_id))

# ----------------- MODULE 5: DOCTOR APPOINTMENTS ----------------- #

@app.route('/appointments')
@login_required
def appointments():
    user = db_manager.get_user_by_id(session['user_id'])
    children = db_manager.get_children_by_parent(user['id'])
    doctors = db_manager.get_all_doctors()
    booked = db_manager.get_appointments_by_parent(user['id'])
    db_mode = "SQLite (Local Mode)" if db_manager.use_sqlite else "MySQL Database"

    return render_template('appointments.html', user=user, children=children, 
                           doctors=doctors, appointments=booked, 
                           today_date=date.today().isoformat(), db_mode=db_mode)

@app.route('/appointments/book', methods=['POST'])
@login_required
def book_appointment():
    child_id = request.form.get('child_id')
    doctor_id = request.form.get('doctor_id')
    app_date = request.form.get('appointment_date')
    time_slot = request.form.get('time_slot')
    symptoms = request.form.get('reason_symptoms', '').strip()
    notes = request.form.get('notes', '').strip()

    if not child_id or not doctor_id or not app_date or not time_slot or not symptoms:
        flash("All fields including child, doctor, date, time, and symptoms are required.", "error")
        return redirect(url_for('appointments'))

    # Verify child ownership
    child = db_manager.get_child_by_id(int(child_id), parent_id=session['user_id'])
    doctor = db_manager.get_doctor_by_id(int(doctor_id))

    if not child or not doctor:
        flash("Invalid child or doctor selected.", "error")
        return redirect(url_for('appointments'))

    try:
        booking_date = datetime.strptime(app_date, '%Y-%m-%d').date()
        if booking_date < date.today():
            flash("Appointment date cannot be in the past.", "error")
            return redirect(url_for('appointments'))

        db_manager.create_appointment(
            parent_id=session['user_id'],
            child_id=int(child_id),
            doctor_id=int(doctor_id),
            appointment_date=app_date,
            time_slot=time_slot,
            reason_symptoms=symptoms,
            notes=notes
        )
        flash(f"Appointment booked with {doctor['name']} for {child['name']} on {app_date}! 🩺", "success")
    except Exception as e:
        app.logger.error(f"Booking error: {e}")
        flash("Failed to book appointment. Please try again.", "error")

    return redirect(url_for('appointments'))

@app.route('/appointments/<int:appointment_id>/cancel', methods=['POST'])
@login_required
def cancel_appointment(appointment_id):
    success = db_manager.cancel_appointment(appointment_id, parent_id=session['user_id'])
    if success:
        flash("Appointment cancelled successfully.", "info")
    else:
        flash("Failed to cancel appointment.", "error")
    return redirect(url_for('appointments'))

# ----------------- MODULE 6: NUTRITION & MEAL PLANNER ----------------- #

@app.route('/nutrition')
def nutrition_guide():
    user = db_manager.get_user_by_id(session['user_id']) if 'user_id' in session else None
    db_mode = "SQLite (Local Mode)" if db_manager.use_sqlite else "MySQL Database"
    return render_template('nutrition.html', user=user, db_mode=db_mode)

# ----------------- MODULE 7: SYMPTOM CHECKER & FIRST AID ----------------- #

@app.route('/symptoms')
def symptoms_guide():
    user = db_manager.get_user_by_id(session['user_id']) if 'user_id' in session else None
    db_mode = "SQLite (Local Mode)" if db_manager.use_sqlite else "MySQL Database"
    return render_template('symptoms.html', user=user, db_mode=db_mode)

if __name__ == '__main__':
    print("=" * 60)
    print("👶 LittleCare - Comprehensive Child Healthcare Web Platform")
    print(f"🚀 Database Engine: {'SQLite Local Fallback' if db_manager.use_sqlite else 'MySQL (' + Config.MYSQL_DB + ')'}")
    print("🌐 Running at: http://127.0.0.1:5000")
    print("=" * 60)
    app.run(debug=True, host='127.0.0.1', port=5000)
