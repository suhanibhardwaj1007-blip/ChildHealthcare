# 👶 LittleCare - Child Healthcare Portal

A pediatric child healthcare web application built strictly with **HTML5, CSS3, Python Flask, and MySQL** (All in English).

---

## 🛠️ Tech Stack

- **Frontend**: **Pure HTML5 & Modern CSS3** (No external JavaScript required; pure CSS tab switcher, responsive layout, pediatric pastel color system, standard semantic forms).
- **Backend**: **Python Flask** (`app.py` with standard form handlers, password hashing via `werkzeug.security`, session management, and flash alerts).
- **Database**: **MySQL** (`schema.sql`, `database.py` with PyMySQL, automated table creation, and local SQLite testing fallback).

---

## 📁 Project Directory Structure

```
ChildHealthcare/
├── app.py                     # Flask web server & form route handlers
├── config.py                  # Database & session configuration
├── database.py                # MySQL & SQLite connection manager
├── schema.sql                 # MySQL Database Schema for `users` table
├── requirements.txt           # Python dependencies
├── test_auth.py               # Automated test suite (8 passing tests)
├── static/
│   └── css/
│       └── auth.css           # Pure CSS styling, tab animations & responsive design
└── templates/
    ├── login.html             # English Login & Registration Page
    └── dashboard.html         # English Post-Login Welcome Dashboard
```

---

## 🚀 How to Run in VS Code

### Step 1: Open Folder in VS Code
- Open **VS Code** -> `File` -> `Open Folder...` -> Select `C:\Users\HP\OneDrive\Desktop\ChildHealthcare`.

### Step 2: Open Terminal
- Press `Ctrl + ~` (or `Terminal` -> `New Terminal`).

### Step 3: Run the Application
```bash
python app.py
```

### Step 4: Open in Web Browser
- Visit: **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 🗄️ MySQL Database Setup (Optional)

1. Open `config.py` and set your MySQL password:
   ```python
   MYSQL_HOST = 'localhost'
   MYSQL_PORT = 3306
   MYSQL_USER = 'root'
   MYSQL_PASSWORD = 'your_mysql_password'
   MYSQL_DB = 'child_healthcare_db'
   ```
2. If MySQL server is running, the app automatically connects and initializes the tables.
3. If MySQL is offline, the app seamlessly runs on local SQLite mode for immediate testing.

---

## 🧪 Run Automated Tests
```bash
python test_auth.py
```
