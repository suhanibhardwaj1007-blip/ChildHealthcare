import pymysql
import pymysql.cursors
import sqlite3
import os
import logging
from config import Config

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

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
        """Initializes database and tables in MySQL (or SQLite fallback if MySQL is offline)"""
        try:
            # 1. Connect without selecting database to create DB if missing
            conn = self._get_mysql_connection(select_db=False)
            with conn.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{Config.MYSQL_DB}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            conn.close()

            # 2. Connect to the database and create tables
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
            conn.close()
            logger.info("Successfully connected to MySQL and verified 'users' table!")
            self.use_sqlite = False
        except Exception as e:
            logger.warning(f"MySQL connection unavailable ({e}). Initializing SQLite fallback for seamless testing...")
            self.use_sqlite = True
            self._init_sqlite()

    def _init_sqlite(self):
        """SQLite table initialization for instant local testing when MySQL server is not running"""
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
        conn.commit()
        conn.close()
        logger.info(f"SQLite fallback database initialized at: {self.sqlite_file}")

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

    def get_user_by_email(self, email):
        """Fetches user details by email address"""
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
        """Fetches user details by primary key ID"""
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
        """Inserts a new user record into the database"""
        conn = self.get_connection()
        try:
            if self.use_sqlite:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO users (full_name, email, phone, password_hash, role)
                    VALUES (?, ?, ?, ?, ?)
                """, (full_name.strip(), email.strip().lower(), phone.strip() if phone else None, password_hash, role))
                conn.commit()
                user_id = cursor.lastrowid
                return user_id
            else:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO users (full_name, email, phone, password_hash, role)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (full_name.strip(), email.strip().lower(), phone.strip() if phone else None, password_hash, role))
                    user_id = cursor.lastrowid
                    return user_id
        finally:
            conn.close()

# Singleton DB instance
db_manager = DatabaseManager()
