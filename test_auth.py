import unittest
import time
from app import app
from database import db_manager

class ChildHealthcareAuthTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
        self.test_email = f"sarah.jenkins.{int(time.time()*1000)}@example.com"

    def test_01_login_page_renders(self):
        """Test GET /login renders login page successfully with English text"""
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'LittleCare', response.data)
        self.assertIn(b'Sign In', response.data)
        self.assertIn(b'Create Account', response.data)
        self.assertIn(b'Smart Vaccination Tracker', response.data)
        print("PASS: Login page renders with full English branding and pure HTML/CSS forms.")

    def test_02_register_success(self):
        """Test user registration via form POST"""
        payload = {
            'full_name': 'Dr. Sarah Jenkins',
            'email': self.test_email,
            'phone': '+1 555-019-2834',
            'password': 'SecurePassword123',
            'confirm_password': 'SecurePassword123',
            'role': 'doctor'
        }
        response = self.client.post('/register', data=payload, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Sarah Jenkins', response.data)
        self.assertIn(b'Dashboard', response.data)
        print("PASS: Form POST registration and auto-login successful.")

    def test_03_register_duplicate_email(self):
        """Test registration with existing email shows English error"""
        # Register user first
        self.client.post('/register', data={
            'full_name': 'Dr. Sarah Jenkins',
            'email': self.test_email,
            'password': 'SecurePassword123',
            'confirm_password': 'SecurePassword123',
            'role': 'doctor'
        }, follow_redirects=True)

        # Logout to simulate a new visitor trying to register with the same email
        self.client.get('/logout', follow_redirects=True)

        # Attempt duplicate registration
        payload = {
            'full_name': 'Another User',
            'email': self.test_email,
            'password': 'Password123',
            'confirm_password': 'Password123',
            'role': 'parent'
        }
        response = self.client.post('/register', data=payload, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'already registered', response.data)
        print("PASS: Duplicate email validation functioning properly.")

    def test_04_register_password_mismatch(self):
        """Test registration with mismatched passwords"""
        payload = {
            'full_name': 'Parent User',
            'email': f'mismatch.{int(time.time()*1000)}@example.com',
            'password': 'Password123',
            'confirm_password': 'MismatchPassword',
            'role': 'parent'
        }
        response = self.client.post('/register', data=payload, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Passwords do not match', response.data)
        print("PASS: Password mismatch properly detected.")

    def test_05_login_success(self):
        """Test valid user login via standard form POST"""
        # Register user first
        self.client.post('/register', data={
            'full_name': 'Dr. Sarah Jenkins',
            'email': self.test_email,
            'password': 'SecurePassword123',
            'confirm_password': 'SecurePassword123',
            'role': 'doctor'
        }, follow_redirects=True)

        # Logout so we can test the login form
        self.client.get('/logout', follow_redirects=True)

        # Now login with the registered email
        payload = {
            'email': self.test_email,
            'password': 'SecurePassword123'
        }
        response = self.client.post('/login', data=payload, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome back, Dr. Sarah Jenkins', response.data)
        print("PASS: User login with valid credentials successful.")

    def test_06_login_invalid_password(self):
        """Test login with wrong password shows English error"""
        payload = {
            'email': self.test_email,
            'password': 'WrongPassword999'
        }
        response = self.client.post('/login', data=payload, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Invalid email address or password', response.data)
        print("PASS: Invalid password correctly rejected.")

    def test_07_dashboard_authenticated(self):
        """Test dashboard access when logged in"""
        self.client.post('/register', data={
            'full_name': 'Dr. Sarah Jenkins',
            'email': self.test_email,
            'password': 'SecurePassword123',
            'confirm_password': 'SecurePassword123',
            'role': 'doctor'
        }, follow_redirects=True)

        response = self.client.get('/dashboard')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Sarah Jenkins', response.data)
        self.assertIn(b'Account Information', response.data)
        print("PASS: Dashboard accessible with full English profile details.")

    def test_08_logout(self):
        """Test logout clears session and redirects with English flash message"""
        response = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'signed out successfully', response.data)
        print("PASS: Logout redirects and flashes English goodbye message.")

if __name__ == '__main__':
    unittest.main()
