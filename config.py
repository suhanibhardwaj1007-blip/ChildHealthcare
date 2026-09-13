import os

class Config:
    # Flask Session Secret Key
    SECRET_KEY = os.environ.get('SECRET_KEY', 'bal-arogya-child-health-secret-key-2026')
    
    # MySQL Database Settings
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')  # Set your MySQL root password here or via env
    MYSQL_DB = os.environ.get('MYSQL_DB', 'child_healthcare_db')
    
    # Session Configuration
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
