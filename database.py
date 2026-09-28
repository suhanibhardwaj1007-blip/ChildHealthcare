import pymysql
import pymysql.cursors
import sqlite3
import os
import logging
from datetime import datetime, date, timedelta
from config import Config

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Standard Pediatric Vaccine Seed Catalog (IAP / WHO Guidelines)
DEFAULT_VACCINES = [
    ("BCG", "Dose 1", 0, "At Birth", "Tuberculosis (TB)", 1, "Administered on left upper arm"),
    ("Hepatitis B (Hep B-1)", "Birth Dose", 0, "At Birth", "Hepatitis B Virus", 1, "Within 24 hours of birth"),
    ("Oral Polio Vaccine (OPV-0)", "Birth Dose", 0, "At Birth", "Poliovirus", 1, "Oral drops"),
    ("DTwP / DTaP-1", "Dose 1", 6, "6 Weeks", "Diphtheria, Tetanus & Pertussis (Whooping Cough)", 1, "Primary combination"),
    ("Inactivated Polio (IPV-1)", "Dose 1", 6, "6 Weeks", "Polio Paralysis", 1, "Injectable polio dose"),
    ("Hepatitis B (Hep B-2)", "Dose 2", 6, "6 Weeks", "Hepatitis B Infection", 1, "Second hepatitis dose"),
    ("Hib-1", "Dose 1", 6, "6 Weeks", "Haemophilus influenzae type b (Meningitis/Pneumonia)", 1, "Combination shot"),
    ("Rotavirus (RV-1)", "Dose 1", 6, "6 Weeks", "Severe Infant Diarrhea & Rotavirus gastroenteritis", 1, "Oral vaccine"),
    ("Pneumococcal (PCV-1)", "Dose 1", 6, "6 Weeks", "Pneumonia, Ear Infections & Bacteremia", 1, "Primary conjugate"),
    ("DTwP / DTaP-2", "Dose 2", 10, "10 Weeks", "Diphtheria, Tetanus & Pertussis", 1, "Second primary dose"),
    ("IPV-2 & Hib-2", "Dose 2", 10, "10 Weeks", "Polio & Meningitis", 1, "Second combo"),
    ("Rotavirus (RV-2)", "Dose 2", 10, "10 Weeks", "Rotavirus Diarrhea", 1, "Second oral dose"),
    ("Pneumococcal (PCV-2)", "Dose 2", 10, "10 Weeks", "Pneumonia & Strep infections", 1, "Second PCV dose"),
    ("DTwP / DTaP-3", "Dose 3", 14, "14 Weeks", "Diphtheria, Tetanus & Pertussis", 1, "Third primary dose"),
    ("IPV-3 & Hib-3", "Dose 3", 14, "14 Weeks", "Polio & Haemophilus", 1, "Third combo dose"),
    ("Rotavirus (RV-3)", "Dose 3", 14, "14 Weeks", "Rotavirus Gastroenteritis", 1, "Third oral dose"),
    ("Pneumococcal (PCV-3)", "Dose 3", 14, "14 Weeks", "Pneumococcal Disease", 1, "Third PCV dose"),
    ("Influenza (Flu-1)", "Dose 1", 26, "6 Months", "Seasonal Influenza / Viral Flu", 0, "Annual protection"),
    ("MMR-1 / Measles-1", "Dose 1", 39, "9 Months", "Measles, Mumps & Rubella", 1, "Vital immunity booster"),
    ("Typhoid Conjugate (TCV)", "Dose 1", 52, "12 Months", "Typhoid Fever & Salmonella", 1, "Long-term protection"),
    ("Hepatitis A (Hep A-1)", "Dose 1", 52, "12 Months", "Hepatitis A Liver Infection", 1, "Primary live/inactivated"),
    ("MMR-2", "Dose 2", 65, "15 Months", "Measles, Mumps & Rubella (Booster)", 1, "MMR Second Dose"),
    ("Varicella (Chickenpox-1)", "Dose 1", 65, "15 Months", "Chickenpox & Shingles", 0, "Varicella primary"),
    ("DTP Booster-1 & IPV-B1", "Booster 1", 78, "18 Months", "Diphtheria, Pertussis, Tetanus & Polio", 1, "First booster"),
    ("DTP Booster-2", "Booster 2", 260, "5 Years", "Diphtheria, Pertussis & Tetanus", 1, "Pre-school booster")
]

# Verified Pediatric Specialists Seed Data
DEFAULT_DOCTORS = [
    ("Dr. Ananya Roy", "Senior Pediatrician & Neonatologist", "MBBS, MD (Pediatrics), DCH", 14, "Apollo Cradle Children's Hospital", 800, 4.9, "Mon - Sat", "10:00 AM - 02:00 PM", "👩‍⚕️"),
    ("Dr. Rajesh Malhotra", "Pediatrician & Child Health Specialist", "MBBS, DNB (Pediatrics), FIAP", 18, "Max Super Speciality Hospital", 900, 4.8, "Mon - Fri", "02:00 PM - 07:00 PM", "👨‍⚕️"),
    ("Dr. Priya Mukherjee", "Pediatric Nutritionist & Dietitian", "M.Sc (Clinical Nutrition), Ph.D (Pediatrics)", 11, "Fortis Pediatric Wellness Clinic", 700, 4.9, "Mon - Sat", "11:00 AM - 04:00 PM", "👩‍⚕️"),
    ("Dr. Vikramaditya Joshi", "Child Allergist & Immunologist", "MBBS, MD, Fellow Pediatric Allergy (UK)", 16, "Cloudnine Child Healthcare Hospital", 1000, 5.0, "Tue - Sun", "09:00 AM - 01:00 PM", "👨‍⚕️"),
    ("Dr. Sneha Kulkarni", "General Pediatrician & Child Development", "MBBS, DCH, PGDND", 9, "Care & Cure Pediatric Clinic", 600, 4.7, "Mon - Sat", "04:00 PM - 08:30 PM", "👩‍⚕️")
]

class DatabaseManager:
    def __init__(self):
        self.use_sqlite = False
        self.sqlite_file = os.path.join(os.path.dirname(__file__), 'child_healthcare.db')
        self._init_db()

    def _get_mysql_connection(self, select_db=True):
        """Attempts to connect to MySQL server"""
        kwargs = {
            'host': Config.MYSQL_HOST,
            'port': Config.MYSQL_PORT,
            'user': Config.MYSQL_USER,
            'password': Config.MYSQL_PASSWORD,
            'charset': 'utf8mb4',
            'cursorclass': pymysql.cursors.DictCursor,
            'autocommit': True,
            'connect_timeout': 3
        }
        if select_db:
            kwargs['database'] = Config.MYSQL_DB
        return pymysql.connect(**kwargs)

    def _init_db(self):
        """Initializes database and all tables in MySQL (or SQLite fallback)"""
        try:
            conn = self._get_mysql_connection(select_db=False)
            with conn.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{Config.MYSQL_DB}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            conn.close()

            conn = self._get_mysql_connection(select_db=True)
            with conn.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        full_name VARCHAR(100) NOT NULL,
                        email VARCHAR(150) NOT NULL UNIQUE,
                        phone VARCHAR(20),
                        password_hash VARCHAR(255) NOT NULL,
                        role ENUM('parent', 'doctor', 'admin') DEFAULT 'parent',
                        profile_image VARCHAR(255) DEFAULT NULL,
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        INDEX idx_email (email),
                        INDEX idx_role (role)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS children (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        parent_id INT NOT NULL,
                        name VARCHAR(100) NOT NULL,
                        dob DATE NOT NULL,
                        gender ENUM('male', 'female', 'other') NOT NULL DEFAULT 'male',
                        blood_group VARCHAR(10) DEFAULT NULL,
                        birth_weight_kg DECIMAL(5,2) DEFAULT NULL,
                        birth_height_cm DECIMAL(5,2) DEFAULT NULL,
                        allergies TEXT DEFAULT NULL,
                        medical_notes TEXT DEFAULT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        FOREIGN KEY (parent_id) REFERENCES users(id) ON DELETE CASCADE,
                        INDEX idx_parent_id (parent_id),
                        INDEX idx_child_dob (dob)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS vaccines_master (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        dose_number VARCHAR(50) NOT NULL,
                        recommended_age_weeks INT NOT NULL,
                        recommended_age_label VARCHAR(50) NOT NULL,
                        prevents_disease VARCHAR(255) NOT NULL,
                        is_mandatory BOOLEAN DEFAULT TRUE,
                        notes TEXT DEFAULT NULL
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS child_vaccinations (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        child_id INT NOT NULL,
                        vaccine_id INT NOT NULL,
                        due_date DATE NOT NULL,
                        status ENUM('pending', 'completed', 'overdue') DEFAULT 'pending',
                        administered_date DATE DEFAULT NULL,
                        administered_by VARCHAR(100) DEFAULT NULL,
                        notes TEXT DEFAULT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                        FOREIGN KEY (child_id) REFERENCES children(id) ON DELETE CASCADE,
                        FOREIGN KEY (vaccine_id) REFERENCES vaccines_master(id) ON DELETE CASCADE,
                        INDEX idx_child_vaccine (child_id, vaccine_id),
                        INDEX idx_due_date (due_date)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS growth_records (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        child_id INT NOT NULL,
                        record_date DATE NOT NULL,
                        age_months INT NOT NULL,
                        weight_kg DECIMAL(5,2) NOT NULL,
                        height_cm DECIMAL(5,2) NOT NULL,
                        head_circumference_cm DECIMAL(5,2) DEFAULT NULL,
                        bmi DECIMAL(4,1) DEFAULT NULL,
                        growth_status VARCHAR(50) DEFAULT 'Healthy Weight',
                        notes TEXT DEFAULT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (child_id) REFERENCES children(id) ON DELETE CASCADE,
                        INDEX idx_child_growth (child_id, record_date)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS doctors (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        specialization VARCHAR(100) NOT NULL,
                        qualification VARCHAR(100) NOT NULL,
                        experience_years INT NOT NULL,
                        hospital VARCHAR(150) NOT NULL,
                        consultation_fee INT NOT NULL,
                        rating DECIMAL(2,1) DEFAULT 4.9,
                        available_days VARCHAR(100) DEFAULT 'Mon - Sat',
                        available_time VARCHAR(100) DEFAULT '10:00 AM - 05:00 PM',
                        avatar VARCHAR(10) DEFAULT '👨‍⚕️'
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS appointments (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        parent_id INT NOT NULL,
                        child_id INT NOT NULL,
                        doctor_id INT NOT NULL,
                        appointment_date DATE NOT NULL,
                        time_slot VARCHAR(50) NOT NULL,
                        reason_symptoms TEXT NOT NULL,
                        status ENUM('confirmed', 'completed', 'cancelled') DEFAULT 'confirmed',
                        notes TEXT DEFAULT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (parent_id) REFERENCES users(id) ON DELETE CASCADE,
                        FOREIGN KEY (child_id) REFERENCES children(id) ON DELETE CASCADE,
                        FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE CASCADE,
                        INDEX idx_parent_appointments (parent_id),
                        INDEX idx_child_appointments (child_id),
                        INDEX idx_doctor_appointments (doctor_id)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
                """)

                # Check and Seed Vaccines
                cursor.execute("SELECT COUNT(*) as cnt FROM vaccines_master")
                if cursor.fetchone()['cnt'] == 0:
                    cursor.executemany("""
                        INSERT INTO vaccines_master (name, dose_number, recommended_age_weeks, recommended_age_label, prevents_disease, is_mandatory, notes)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, DEFAULT_VACCINES)
                    logger.info("Seeded master vaccines catalog in MySQL.")

                # Check and Seed Doctors
                cursor.execute("SELECT COUNT(*) as cnt FROM doctors")
                if cursor.fetchone()['cnt'] == 0:
                    cursor.executemany("""
                        INSERT INTO doctors (name, specialization, qualification, experience_years, hospital, consultation_fee, rating, available_days, available_time, avatar)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, DEFAULT_DOCTORS)
                    logger.info("Seeded pediatric doctors directory in MySQL.")

            conn.close()
            logger.info("Successfully connected to MySQL and verified all LittleCare tables!")
            self.use_sqlite = False
        except Exception as e:
            logger.warning(f"MySQL connection unavailable ({e}). Initializing SQLite fallback...")
            self.use_sqlite = True
            self._init_sqlite()

    def _init_sqlite(self):
        """SQLite initialization with all tables and master seed data"""
        conn = sqlite3.connect(self.sqlite_file)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                phone TEXT,
                password_hash TEXT NOT NULL,
                role TEXT DEFAULT 'parent',
                profile_image TEXT DEFAULT NULL,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS children (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parent_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                dob TEXT NOT NULL,
                gender TEXT NOT NULL DEFAULT 'male',
                blood_group TEXT,
                birth_weight_kg REAL,
                birth_height_cm REAL,
                allergies TEXT,
                medical_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vaccines_master (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                dose_number TEXT NOT NULL,
                recommended_age_weeks INTEGER NOT NULL,
                recommended_age_label TEXT NOT NULL,
                prevents_disease TEXT NOT NULL,
                is_mandatory INTEGER DEFAULT 1,
                notes TEXT
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS child_vaccinations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                child_id INTEGER NOT NULL,
                vaccine_id INTEGER NOT NULL,
                due_date TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                administered_date TEXT,
                administered_by TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (child_id) REFERENCES children(id) ON DELETE CASCADE,
                FOREIGN KEY (vaccine_id) REFERENCES vaccines_master(id) ON DELETE CASCADE
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS growth_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                child_id INTEGER NOT NULL,
                record_date TEXT NOT NULL,
                age_months INTEGER NOT NULL,
                weight_kg REAL NOT NULL,
                height_cm REAL NOT NULL,
                head_circumference_cm REAL,
                bmi REAL,
                growth_status TEXT DEFAULT 'Healthy Weight',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (child_id) REFERENCES children(id) ON DELETE CASCADE
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS doctors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                specialization TEXT NOT NULL,
                qualification TEXT NOT NULL,
                experience_years INTEGER NOT NULL,
                hospital TEXT NOT NULL,
                consultation_fee INTEGER NOT NULL,
                rating REAL DEFAULT 4.9,
                available_days TEXT DEFAULT 'Mon - Sat',
                available_time TEXT DEFAULT '10:00 AM - 05:00 PM',
                avatar TEXT DEFAULT '👨‍⚕️'
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parent_id INTEGER NOT NULL,
                child_id INTEGER NOT NULL,
                doctor_id INTEGER NOT NULL,
                appointment_date TEXT NOT NULL,
                time_slot TEXT NOT NULL,
                reason_symptoms TEXT NOT NULL,
                status TEXT DEFAULT 'confirmed',
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (child_id) REFERENCES children(id) ON DELETE CASCADE,
                FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE CASCADE
            );
        """)

        # Check and Seed Vaccines in SQLite
        cursor.execute("SELECT COUNT(*) FROM vaccines_master")
        if cursor.fetchone()[0] == 0:
            cursor.executemany("""
                INSERT INTO vaccines_master (name, dose_number, recommended_age_weeks, recommended_age_label, prevents_disease, is_mandatory, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, DEFAULT_VACCINES)
            logger.info("Seeded master vaccines catalog in SQLite.")

        # Check and Seed Doctors in SQLite
        cursor.execute("SELECT COUNT(*) FROM doctors")
        if cursor.fetchone()[0] == 0:
            cursor.executemany("""
                INSERT INTO doctors (name, specialization, qualification, experience_years, hospital, consultation_fee, rating, available_days, available_time, avatar)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, DEFAULT_DOCTORS)
            logger.info("Seeded pediatric doctors directory in SQLite.")

        conn.commit()
        conn.close()
        logger.info(f"SQLite database fully initialized at: {self.sqlite_file}")

    def get_connection(self):
        """Returns active database connection"""
        if self.use_sqlite:
            conn = sqlite3.connect(self.sqlite_file)
            conn.row_factory = sqlite3.Row
            return conn
        else:
            try:
                return self._get_mysql_connection(select_db=True)
            except Exception as e:
                logger.error(f"MySQL connection lost ({e}). Falling back to SQLite.")
                self.use_sqlite = True
                return self.get_connection()

    # ----------------- USER METHODS ----------------- #

    def get_user_by_email(self, email):
        conn = self.get_connection()
        try:
            if self.use_sqlite:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE LOWER(email) = LOWER(?)", (email.strip(),))
                row = cursor.fetchone()
                return dict(row) if row else None
            else:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM users WHERE LOWER(email) = LOWER(%s)", (email.strip(),))
                    return cursor.fetchone()
        finally:
            conn.close()

    def get_user_by_id(self, user_id):
        conn = self.get_connection()
        try:
            if self.use_sqlite:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
            else:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
                    return cursor.fetchone()
        finally:
            conn.close()

    def create_user(self, full_name, email, phone, password_hash, role='parent'):
        conn = self.get_connection()
        try:
            if self.use_sqlite:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO users (full_name, email, phone, password_hash, role)
                    VALUES (?, ?, ?, ?, ?)
                """, (full_name.strip(), email.strip().lower(), phone.strip() if phone else None, password_hash, role))
                conn.commit()
                return cursor.lastrowid
            else:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO users (full_name, email, phone, password_hash, role)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (full_name.strip(), email.strip().lower(), phone.strip() if phone else None, password_hash, role))
                    return cursor.lastrowid
        finally:
            conn.close()

    # ----------------- CHILDREN METHODS ----------------- #

    def create_child(self, parent_id, name, dob, gender='male', blood_group=None, 
                     birth_weight_kg=None, birth_height_cm=None, allergies=None, medical_notes=None):
        conn = self.get_connection()
        try:
            if self.use_sqlite:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO children (parent_id, name, dob, gender, blood_group, birth_weight_kg, birth_height_cm, allergies, medical_notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (parent_id, name.strip(), str(dob), gender, blood_group, birth_weight_kg, birth_height_cm, allergies, medical_notes))
                conn.commit()
                child_id = cursor.lastrowid
            else:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO children (parent_id, name, dob, gender, blood_group, birth_weight_kg, birth_height_cm, allergies, medical_notes)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (parent_id, name.strip(), str(dob), gender, blood_group, birth_weight_kg, birth_height_cm, allergies, medical_notes))
                    child_id = cursor.lastrowid

            # Automatically generate standard vaccination schedule for this child!
            self.generate_child_vaccination_schedule(child_id, str(dob))
            return child_id
        finally:
            conn.close()

    def get_children_by_parent(self, parent_id):
        conn = self.get_connection()
        try:
            if self.use_sqlite:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM children WHERE parent_id = ? ORDER BY created_at DESC", (parent_id,))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
            else:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM children WHERE parent_id = %s ORDER BY created_at DESC", (parent_id,))
                    return cursor.fetchall()
        finally:
            conn.close()

    def get_child_by_id(self, child_id, parent_id=None):
        conn = self.get_connection()
        try:
            if self.use_sqlite:
                cursor = conn.cursor()
                if parent_id:
                    cursor.execute("SELECT * FROM children WHERE id = ? AND parent_id = ?", (child_id, parent_id))
                else:
                    cursor.execute("SELECT * FROM children WHERE id = ?", (child_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
            else:
                with conn.cursor() as cursor:
                    if parent_id:
                        cursor.execute("SELECT * FROM children WHERE id = %s AND parent_id = %s", (child_id, parent_id))
                    else:
                        cursor.execute("SELECT * FROM children WHERE id = %s", (child_id,))
                    return cursor.fetchone()
        finally:
            conn.close()

    def delete_child(self, child_id, parent_id):
        conn = self.get_connection()
        try:
            if self.use_sqlite:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM children WHERE id = ? AND parent_id = ?", (child_id, parent_id))
                conn.commit()
                return cursor.rowcount > 0
            else:
                with conn.cursor() as cursor:
                    cursor.execute("DELETE FROM children WHERE id = %s AND parent_id = %s", (child_id, parent_id))
                    return cursor.rowcount > 0
        finally:
            conn.close()

    # ----------------- VACCINATION METHODS ----------------- #

    def get_master_vaccines(self):
        conn = self.get_connection()
        try:
            if self.use_sqlite:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM vaccines_master ORDER BY recommended_age_weeks ASC, id ASC")
                return [dict(row) for row in cursor.fetchall()]
            else:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM vaccines_master ORDER BY recommended_age_weeks ASC, id ASC")
                    return cursor.fetchall()
        finally:
            conn.close()

    def generate_child_vaccination_schedule(self, child_id, dob_str):
        """Auto-computes due dates based on child DOB and seeds child_vaccinations"""
        conn = self.get_connection()
        try:
            # Parse DOB
            if isinstance(dob_str, str):
                dob_date = datetime.strptime(dob_str[:10], '%Y-%m-%d').date()
            else:
                dob_date = dob_str

            # Check if schedule already exists
            if self.use_sqlite:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM child_vaccinations WHERE child_id = ?", (child_id,))
                if cursor.fetchone()[0] > 0:
                    return
                cursor.execute("SELECT * FROM vaccines_master ORDER BY recommended_age_weeks ASC, id ASC")
                master_vaccines = [dict(r) for r in cursor.fetchall()]
            else:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) as cnt FROM child_vaccinations WHERE child_id = %s", (child_id,))
                    if cursor.fetchone()['cnt'] > 0:
                        return
                    cursor.execute("SELECT * FROM vaccines_master ORDER BY recommended_age_weeks ASC, id ASC")
                    master_vaccines = cursor.fetchall()

            today = date.today()
            records_to_insert = []
            for vac in master_vaccines:
                due_date = dob_date + timedelta(weeks=vac['recommended_age_weeks'])
                # Check initial status
                status = 'overdue' if due_date < today else 'pending'
                records_to_insert.append((child_id, vac['id'], str(due_date), status))

            if self.use_sqlite:
                cursor = conn.cursor()
                cursor.executemany("""
                    INSERT INTO child_vaccinations (child_id, vaccine_id, due_date, status)
                    VALUES (?, ?, ?, ?)
                """, records_to_insert)
                conn.commit()
            else:
                with conn.cursor() as cursor:
                    cursor.executemany("""
                        INSERT INTO child_vaccinations (child_id, vaccine_id, due_date, status)
                        VALUES (%s, %s, %s, %s)
                    """, records_to_insert)
        finally:
            conn.close()

    def get_child_vaccinations(self, child_id):
        """Fetches full immunization schedule with vaccine master details for a child"""
        conn = self.get_connection()
        try:
            query = """
                SELECT 
                    cv.id, cv.child_id, cv.vaccine_id, cv.due_date, cv.status, 
                    cv.administered_date, cv.administered_by, cv.notes,
                    vm.name as vaccine_name, vm.dose_number, vm.recommended_age_label,
                    vm.recommended_age_weeks, vm.prevents_disease, vm.is_mandatory,
                    vm.notes as vaccine_info
                FROM child_vaccinations cv
                JOIN vaccines_master vm ON cv.vaccine_id = vm.id
                WHERE cv.child_id = %s
                ORDER BY vm.recommended_age_weeks ASC, cv.due_date ASC, vm.id ASC
            """
            if self.use_sqlite:
                cursor = conn.cursor()
                cursor.execute(query.replace('%s', '?'), (child_id,))
                rows = cursor.fetchall()
                # Update overdue status on the fly if pending and past due date
                today = date.today()
                result = []
                for row in rows:
                    d = dict(row)
                    due_d = datetime.strptime(str(d['due_date'])[:10], '%Y-%m-%d').date() if d['due_date'] else None
                    if d['status'] != 'completed' and due_d and due_d < today:
                        d['status'] = 'overdue'
                    result.append(d)
                return result
            else:
                with conn.cursor() as cursor:
                    cursor.execute(query, (child_id,))
                    rows = cursor.fetchall()
                    today = date.today()
                    for row in rows:
                        due_d = row['due_date'] if isinstance(row['due_date'], date) else datetime.strptime(str(row['due_date'])[:10], '%Y-%m-%d').date()
                        if row['status'] != 'completed' and due_d and due_d < today:
                            row['status'] = 'overdue'
                    return rows
        finally:
            conn.close()

    def toggle_vaccination_status(self, vaccination_id, child_id, parent_id, status=None, administered_date=None, administered_by=None, notes=None):
        """Toggles vaccination completion with parent ownership check"""
        conn = self.get_connection()
        try:
            # Verify child belongs to parent
            child = self.get_child_by_id(child_id, parent_id)
            if not child:
                return False

            if not status:
                # Fetch current status
                if self.use_sqlite:
                    cursor = conn.cursor()
                    cursor.execute("SELECT status, due_date FROM child_vaccinations WHERE id = ? AND child_id = ?", (vaccination_id, child_id))
                    row = cursor.fetchone()
                    if not row: return False
                    cur_status = row['status']
                    due_date = row['due_date']
                else:
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT status, due_date FROM child_vaccinations WHERE id = %s AND child_id = %s", (vaccination_id, child_id))
                        row = cursor.fetchone()
                        if not row: return False
                        cur_status = row['status']
                        due_date = row['due_date']

                if cur_status == 'completed':
                    # Toggle to pending/overdue
                    due_d = due_date if isinstance(due_date, date) else datetime.strptime(str(due_date)[:10], '%Y-%m-%d').date()
                    new_status = 'overdue' if due_d < date.today() else 'pending'
                    admin_d = None
                else:
                    new_status = 'completed'
                    admin_d = date.today().isoformat()
            else:
                new_status = status
                admin_d = administered_date if new_status == 'completed' else None

            if self.use_sqlite:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE child_vaccinations 
                    SET status = ?, administered_date = ?, administered_by = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND child_id = ?
                """, (new_status, admin_d, administered_by, notes, vaccination_id, child_id))
                conn.commit()
                return cursor.rowcount > 0
            else:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE child_vaccinations 
                        SET status = %s, administered_date = %s, administered_by = %s, notes = %s
                        WHERE id = %s AND child_id = %s
                    """, (new_status, admin_d, administered_by, notes, vaccination_id, child_id))
                    return cursor.rowcount > 0
        finally:
            conn.close()

    def get_vaccination_summary(self, child_id):
        """Returns statistics of completed, upcoming, and overdue vaccines"""
        vaccines = self.get_child_vaccinations(child_id)
        total = len(vaccines)
        completed = sum(1 for v in vaccines if v['status'] == 'completed')
        overdue = sum(1 for v in vaccines if v['status'] == 'overdue')
        pending = sum(1 for v in vaccines if v['status'] == 'pending')
        progress_pct = int((completed / total * 100)) if total > 0 else 0
        return {
            'total': total,
            'completed': completed,
            'overdue': overdue,
            'pending': pending,
            'progress_pct': progress_pct
        }

    # ----------------- GROWTH & BMI METHODS ----------------- #

    def add_growth_record(self, child_id, record_date, age_months, weight_kg, height_cm, head_circumference_cm=None, notes=None):
        """Logs a growth record and calculates BMI & WHO category"""
        # Calculate BMI = weight (kg) / (height (m) ^ 2)
        height_m = float(height_cm) / 100.0
        bmi = round(float(weight_kg) / (height_m * height_m), 1) if height_m > 0 else None

        # Simplified WHO Growth Indicator for Children
        if bmi:
            if bmi < 14.0:
                growth_status = "Underweight"
            elif bmi <= 17.5:
                growth_status = "Healthy Weight"
            elif bmi <= 19.5:
                growth_status = "Overweight Risk"
            else:
                growth_status = "Overweight"
        else:
            growth_status = "Healthy Weight"

        conn = self.get_connection()
        try:
            if self.use_sqlite:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO growth_records (child_id, record_date, age_months, weight_kg, height_cm, head_circumference_cm, bmi, growth_status, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (child_id, str(record_date), age_months, weight_kg, height_cm, head_circumference_cm, bmi, growth_status, notes))
                conn.commit()
                return cursor.lastrowid
            else:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO growth_records (child_id, record_date, age_months, weight_kg, height_cm, head_circumference_cm, bmi, growth_status, notes)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (child_id, str(record_date), age_months, weight_kg, height_cm, head_circumference_cm, bmi, growth_status, notes))
                    return cursor.lastrowid
        finally:
            conn.close()

    def get_growth_records(self, child_id):
        conn = self.get_connection()
        try:
            if self.use_sqlite:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM growth_records WHERE child_id = ? ORDER BY record_date DESC", (child_id,))
                return [dict(row) for row in cursor.fetchall()]
            else:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM growth_records WHERE child_id = %s ORDER BY record_date DESC", (child_id,))
                    return cursor.fetchall()
        finally:
            conn.close()

    def get_latest_growth_record(self, child_id):
        conn = self.get_connection()
        try:
            if self.use_sqlite:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM growth_records WHERE child_id = ? ORDER BY record_date DESC, id DESC LIMIT 1", (child_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
            else:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM growth_records WHERE child_id = %s ORDER BY record_date DESC, id DESC LIMIT 1", (child_id,))
                    return cursor.fetchone()
        finally:
            conn.close()

    def delete_growth_record(self, record_id, child_id, parent_id):
        child = self.get_child_by_id(child_id, parent_id)
        if not child: return False

        conn = self.get_connection()
        try:
            if self.use_sqlite:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM growth_records WHERE id = ? AND child_id = ?", (record_id, child_id))
                conn.commit()
                return cursor.rowcount > 0
            else:
                with conn.cursor() as cursor:
                    cursor.execute("DELETE FROM growth_records WHERE id = %s AND child_id = %s", (record_id, child_id))
                    return cursor.rowcount > 0
        finally:
            conn.close()

    # ----------------- DOCTORS & APPOINTMENTS ----------------- #

    def get_all_doctors(self):
        conn = self.get_connection()
        try:
            if self.use_sqlite:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM doctors ORDER BY rating DESC, experience_years DESC")
                return [dict(row) for row in cursor.fetchall()]
            else:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM doctors ORDER BY rating DESC, experience_years DESC")
                    return cursor.fetchall()
        finally:
            conn.close()

    def get_doctor_by_id(self, doctor_id):
        conn = self.get_connection()
        try:
            if self.use_sqlite:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM doctors WHERE id = ?", (doctor_id,))
                row = cursor.fetchone()
                return dict(row) if row else None
            else:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM doctors WHERE id = %s", (doctor_id,))
                    return cursor.fetchone()
        finally:
            conn.close()

    def create_appointment(self, parent_id, child_id, doctor_id, appointment_date, time_slot, reason_symptoms, notes=None):
        conn = self.get_connection()
        try:
            if self.use_sqlite:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO appointments (parent_id, child_id, doctor_id, appointment_date, time_slot, reason_symptoms, notes, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'confirmed')
                """, (parent_id, child_id, doctor_id, str(appointment_date), time_slot, reason_symptoms, notes))
                conn.commit()
                return cursor.lastrowid
            else:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO appointments (parent_id, child_id, doctor_id, appointment_date, time_slot, reason_symptoms, notes, status)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, 'confirmed')
                    """, (parent_id, child_id, doctor_id, str(appointment_date), time_slot, reason_symptoms, notes))
                    return cursor.lastrowid
        finally:
            conn.close()

    def get_appointments_by_parent(self, parent_id):
        conn = self.get_connection()
        try:
            query = """
                SELECT 
                    a.id, a.parent_id, a.child_id, a.doctor_id, a.appointment_date, 
                    a.time_slot, a.reason_symptoms, a.status, a.notes, a.created_at,
                    c.name as child_name, c.dob as child_dob, c.gender as child_gender,
                    d.name as doctor_name, d.specialization as doctor_specialization, 
                    d.hospital as doctor_hospital, d.consultation_fee, d.avatar as doctor_avatar
                FROM appointments a
                JOIN children c ON a.child_id = c.id
                JOIN doctors d ON a.doctor_id = d.id
                WHERE a.parent_id = %s
                ORDER BY a.appointment_date DESC, a.created_at DESC
            """
            if self.use_sqlite:
                cursor = conn.cursor()
                cursor.execute(query.replace('%s', '?'), (parent_id,))
                return [dict(row) for row in cursor.fetchall()]
            else:
                with conn.cursor() as cursor:
                    cursor.execute(query, (parent_id,))
                    return cursor.fetchall()
        finally:
            conn.close()

    def cancel_appointment(self, appointment_id, parent_id):
        conn = self.get_connection()
        try:
            if self.use_sqlite:
                cursor = conn.cursor()
                cursor.execute("UPDATE appointments SET status = 'cancelled' WHERE id = ? AND parent_id = ?", (appointment_id, parent_id))
                conn.commit()
                return cursor.rowcount > 0
            else:
                with conn.cursor() as cursor:
                    cursor.execute("UPDATE appointments SET status = 'cancelled' WHERE id = %s AND parent_id = %s", (appointment_id, parent_id))
                    return cursor.rowcount > 0
        finally:
            conn.close()

# Singleton DB instance
db_manager = DatabaseManager()
