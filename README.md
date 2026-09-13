# 👶 LittleCare - Child Healthcare Portal

A comprehensive pediatric child healthcare web application built with **HTML5, CSS3, Python Flask, and MySQL** (100% English & Graphical Pink Theme).

---

## 🛠️ Modules Built

### 1. 🔐 Authentication & Session Module
- Sign In & Sign Up with pure HTML/CSS tab switcher (no external JS dependency).
- Secure password hashing (`pbkdf2:sha256`) via `werkzeug.security`.
- Role selection: **Parent / Guardian** or **Pediatrician**.
- Pure CSS "Forgot Password" modal & real-time flash alerts.

### 2. 👶 Child Profile & Health Card Management Module
- Register new child profiles with DOB, gender, blood group, birth weight/height, allergies, and pediatric history.
- Automatic **human-readable age calculation** (e.g. *"1 yr, 4 mos"* or *"8 months old"*).
- Digital **Child Health Card** view (`/children/<id>`) displaying allergy alerts, physical stats, and health module launchpads.
- **Dynamic Parent Dashboard** rendering registered children cards with instant "+ Add Child Profile" quick actions.
- Secure **Parent Data Isolation** ensuring parents can only view and manage their own children.

---

## 📁 Project Directory Structure

```
ChildHealthcare/
├── app.py                     # Flask web server & all route handlers
├── config.py                  # Database & session configuration
├── database.py                # PyMySQL & SQLite database manager
├── schema.sql                 # MySQL Database Schema for `users` and `children`
├── requirements.txt           # Python dependencies
├── test_auth.py               # Auth automated test suite (8 tests)
├── test_child_profile.py      # Child Profile automated test suite (8 tests)
├── static/
│   ├── css/
│   │   └── auth.css           # Graphical Pink Theme, child health cards & responsive styles
│   └── images/
│       └── baby_heart_footprint.png # Pristine transparent baby footprint emblem
└── templates/
    ├── login.html             # Login & Registration Page
    ├── dashboard.html         # Parent Dashboard with Child Health Cards
    ├── add_child.html         # Child Profile Registration Form
    └── child_detail.html      # Digital Child Health Card & Stats View
```

---

## 🚀 How to Run in VS Code

### Step 1: Open Folder in VS Code
- Open **VS Code** -> `File` -> `Open Folder...` -> Select `C:\Users\HP\OneDrive\Desktop\ChildHealthcare`.

### Step 2: Open Terminal & Run
- Press `Ctrl + ~` (or `Terminal` -> `New Terminal`).
- Start the server:
  ```bash
  python app.py
  ```

### Step 3: Open in Browser
- Visit: **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 🧪 Run Automated Tests
```bash
python test_auth.py
python test_child_profile.py
```
