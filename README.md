# 👶 LittleCare - Child Healthcare Web Platform

A comprehensive, end-to-end pediatric child healthcare web application built with **HTML5, CSS3, Python Flask, and MySQL** (with automated SQLite fallback). Designed with a **Vibrant Graphical Pink Pediatric Theme** and 100% in English.

---

## 🛠️ Complete Modules

### 1. 🔐 Authentication & Session Module (`/login`, `/register`, `/logout`)
- Sign In & Sign Up with pure HTML/CSS tab switcher (no external JS framework dependencies).
- Secure password hashing (`pbkdf2:sha256`) via `werkzeug.security`.
- Role selection: **Parent / Guardian** or **Pediatrician Specialist**.
- Pure CSS "Forgot Password" modal & real-time flash alerts.

### 2. 👶 Child Profile & Digital Health Card (`/children/add`, `/children/<id>`, `/dashboard`)
- Register child profiles with DOB, gender, blood group, birth weight/height, allergies, and birth history.
- Automatic **human-readable age breakdown algorithm** (e.g. *"1 yr, 4 mos"*, *"8 months old"*, *"42 days old"*).
- Interactive **Digital Health Card** with allergy warning banners and physical stat badges.
- **Parent Data Isolation**: Strictly enforces that parents can only access and manage their own children.

### 3. 💉 Smart Vaccination & Immunization Tracker (`/vaccination`, `/vaccination/<id>/toggle`)
- Automated immunization schedule generated upon child creation from the **25 IAP/WHO standard vaccines**.
- Due dates calculated based on the child's exact Date of Birth.
- Real-time status indicators (**Given**, **Due**, **Overdue**) with interactive one-click toggle button.
- Immunization coverage progress bar and summary pills (Total, Completed, Upcoming, Overdue).

### 4. 📈 Child Growth & BMI Monitor (`/growth`, `/growth/add`, `/growth/<id>/delete`)
- Log periodic measurements: Weight (kg), Height (cm), Head Circumference (cm), and pediatric notes.
- Automatic **Pediatric BMI Calculation** ($\text{kg}/\text{m}^2$) and WHO growth status classification (*Healthy Weight*, *Underweight*, *Overweight Risk*).
- Interactive **Developmental Milestones Checklist** grouped by age bands (0–3m, 4–6m, 7–12m, 1–2y) for motor, cognitive, and language development.

### 5. 🩺 Doctor Appointment Booking & Management (`/appointments`, `/appointments/book`, `/appointments/<id>/cancel`)
- Verified pediatric specialist directory with doctor avatars, qualifications, experience, hospital affiliation, consultation fee, and ratings.
- Instant appointment booking form with date picker, time slot selector, and chief symptoms logging.
- Parent appointment manager with instant slot cancellation capability.

### 6. 🥗 Infant & Child Nutrition Guide (`/nutrition`)
- Stage-by-stage feeding guides: 0–6m (Exclusive Milk), 6–8m (First Solids & Purees), 8–12m (Finger Foods), 1–3y (Toddler Balanced Diet).
- Pediatrician-approved kid-friendly recipes (Apple-Oat Porridge, Moong Dal Khichdi, Creamy Avocado Mash).
- Essential micronutrient guide (Iron, Calcium, Vitamin D, DHA) and infant feeding safety rules (no honey < 1 year, choking hazard prevention).

### 7. 🩹 Symptom Triage Checker & Emergency First Aid (`/symptoms`)
- 🚨 **Emergency Red Flags Alert Banner**: Immediate hospital triage indicators (fever in infants < 3m, breathing distress, severe dehydration).
- Common pediatric illness triage cards: High Fever, Infant Colic & Gas, Cough/Cold, Diarrhea & Dehydration.
- Step-by-step emergency first-aid protocols: **Infant Choking Relief (5 Back Blows / 5 Chest Thrusts)** and Thermal Burns treatment.

---

## 📁 Project Directory Structure

```
ChildHealthcare/
├── app.py                     # Flask web server & all 10 route handlers
├── config.py                  # Database & session configuration
├── database.py                # PyMySQL & SQLite database manager + seed catalog
├── schema.sql                 # Complete MySQL Database Schema (7 tables)
├── child_healthcare.db        # SQLite database fallback file
├── requirements.txt           # Python dependencies (Flask, PyMySQL, cryptography, pillow)
├── test_all_modules.py        # Complete test suite (7 end-to-end integration tests)
├── test_auth.py               # Auth automated test suite (8 tests)
├── test_child_profile.py      # Child Profile automated test suite (8 tests)
├── static/
│   ├── css/
│   │   └── auth.css           # Graphical Pink Theme, navigation, tables, cards, milestones
│   └── images/
│       └── baby_heart_footprint.png # Pristine transparent baby footprint emblem
└── templates/
    ├── login.html             # Login & Registration Page (Pure CSS Tab Switcher)
    ├── dashboard.html         # Dynamic Parent Dashboard with Child Cards & Module Links
    ├── add_child.html         # Child Profile Registration Form
    ├── child_detail.html      # Digital Child Health Card & Stats View
    ├── vaccination.html       # Smart Vaccination & Immunization Tracker
    ├── growth.html            # Child Growth & BMI Monitor + Milestones Checklist
    ├── appointments.html      # Doctor Appointment Booking & Management
    ├── nutrition.html         # Pediatric Nutrition & Feeding Guides
    └── symptoms.html          # Symptom Triage Checker & Emergency First Aid
```

---

## 🚀 How to Run in VS Code

### Step 1: Open Project in VS Code
- Open **VS Code** -> `File` -> `Open Folder...` -> Select `C:\Users\HP\OneDrive\Desktop\ChildHealthcare`.

### Step 2: Start the Web Server
- Open Terminal (`Ctrl + ~`) and run:
  ```bash
  python app.py
  ```

### Step 3: Open in Web Browser
- Visit: **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 🧪 Run Automated Test Suite (23 Tests)

Run all 23 tests across authentication, profiles, vaccinations, growth, appointments, and security:
```bash
python -m unittest test_all_modules.py test_auth.py test_child_profile.py -v
```
All 23 tests will execute with **`OK` (100% Pass)**.
