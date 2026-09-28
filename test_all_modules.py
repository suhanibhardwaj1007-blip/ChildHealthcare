import unittest
import os
import tempfile
from datetime import date, timedelta
from app import app
from database import db_manager

class LittleCareAllModulesTest(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret-key-12345'
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

        # Isolate database for tests
        self.db_fd, self.temp_db_path = tempfile.mkstemp(suffix='.db')
        db_manager.use_sqlite = True
        db_manager.sqlite_file = self.temp_db_path
        db_manager._init_sqlite()

    def tearDown(self):
        os.close(self.db_fd)
        if os.path.exists(self.temp_db_path):
            try:
                os.remove(self.temp_db_path)
            except Exception:
                pass

    # Helper: Register & Login
    def register_and_login(self, email="parent1@example.com", password="password123", name="Parent One"):
        self.client.post('/register', data={
            'full_name': name,
            'email': email,
            'phone': '9876543210',
            'password': password,
            'confirm_password': password,
            'role': 'parent'
        }, follow_redirects=True)

        return self.client.post('/login', data={
            'email': email,
            'password': password
        }, follow_redirects=True)

    # Helper: Add Child
    def add_child(self, name="Aarav Sharma", dob="2025-06-15", gender="male"):
        return self.client.post('/children/add', data={
            'name': name,
            'dob': dob,
            'gender': gender,
            'blood_group': 'B+',
            'birth_weight_kg': '3.2',
            'birth_height_cm': '50.0',
            'allergies': 'None',
            'medical_notes': 'Normal birth'
        }, follow_redirects=True)

    # 1. Auth & Session Tests
    def test_auth_registration_and_login(self):
        # Register user
        res = self.register_and_login("testparent@example.com", "pass12345", "Test Parent")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Test Parent", res.data)

        # Logout
        res_logout = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(res_logout.status_code, 200)

        # Protected route redirects to login
        res_dash = self.client.get('/dashboard', follow_redirects=True)
        self.assertIn(b"Sign In to Portal", res_dash.data)

    # 2. Child Creation & Auto-Vaccine Generation Tests
    def test_child_creation_and_auto_vaccine_schedule(self):
        self.register_and_login()
        res = self.add_child("Baby Kiara", "2026-01-10", "female")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Baby Kiara", res.data)

        # Check DB records
        children = db_manager.get_children_by_parent(1)
        self.assertEqual(len(children), 1)
        child_id = children[0]['id']

        # Verify automated 25 vaccines schedule generated
        vaccines = db_manager.get_child_vaccinations(child_id)
        self.assertEqual(len(vaccines), 25)
        self.assertEqual(vaccines[0]['vaccine_name'], "BCG")

        # Verify summary stats
        summary = db_manager.get_vaccination_summary(child_id)
        self.assertEqual(summary['total'], 25)
        self.assertEqual(summary['completed'], 0)

    # 3. Vaccination Tracker & Toggle Status
    def test_vaccination_tracker_and_toggle(self):
        self.register_and_login()
        self.add_child("Aarav", "2025-06-01", "male")
        child = db_manager.get_children_by_parent(1)[0]
        vacs = db_manager.get_child_vaccinations(child['id'])
        first_vac_id = vacs[0]['id']

        # View vaccination page
        res = self.client.get(f'/vaccination?child_id={child["id"]}')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Immunization Schedule", res.data)
        self.assertIn(b"BCG", res.data)

        # Toggle to Completed
        res_toggle = self.client.post(f'/vaccination/{first_vac_id}/toggle', data={
            'child_id': child['id']
        }, follow_redirects=True)
        self.assertEqual(res_toggle.status_code, 200)

        # Check updated status
        summary = db_manager.get_vaccination_summary(child['id'])
        self.assertEqual(summary['completed'], 1)
        self.assertEqual(summary['progress_pct'], 4)

        # Toggle back to pending
        self.client.post(f'/vaccination/{first_vac_id}/toggle', data={
            'child_id': child['id']
        }, follow_redirects=True)
        summary_undo = db_manager.get_vaccination_summary(child['id'])
        self.assertEqual(summary_undo['completed'], 0)

    # 4. Growth Tracker & BMI Calculation
    def test_growth_tracker_bmi_and_deletion(self):
        self.register_and_login()
        self.add_child("Rohan", "2025-01-01", "male")
        child = db_manager.get_children_by_parent(1)[0]

        # View Growth page
        res = self.client.get(f'/growth?child_id={child["id"]}')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Growth Monitor", res.data)

        # Log growth measurement: weight=8.5 kg, height=72 cm
        # BMI = 8.5 / (0.72 * 0.72) = 16.4 kg/m² -> Healthy Weight
        res_add = self.client.post('/growth/add', data={
            'child_id': child['id'],
            'record_date': '2026-03-01',
            'weight_kg': '8.5',
            'height_cm': '72.0',
            'head_circumference_cm': '43.0',
            'notes': '6 months milestone visit'
        }, follow_redirects=True)
        self.assertEqual(res_add.status_code, 200)
        self.assertIn(b"8.5 kg", res_add.data)
        self.assertIn(b"Healthy Weight", res_add.data)

        # Verify in DB
        records = db_manager.get_growth_records(child['id'])
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]['bmi'], 16.4)
        self.assertEqual(records[0]['growth_status'], 'Healthy Weight')

        # Delete growth record
        res_del = self.client.post(f'/growth/{records[0]["id"]}/delete', data={
            'child_id': child['id']
        }, follow_redirects=True)
        self.assertEqual(res_del.status_code, 200)
        self.assertEqual(len(db_manager.get_growth_records(child['id'])), 0)

    # 5. Doctor Appointment Booking & Management
    def test_doctor_appointments_flow(self):
        self.register_and_login()
        self.add_child("Advik", "2025-05-10", "male")
        child = db_manager.get_children_by_parent(1)[0]
        doctors = db_manager.get_all_doctors()
        self.assertGreaterEqual(len(doctors), 5)
        doc = doctors[0]

        # View Appointments Page
        res = self.client.get('/appointments')
        self.assertEqual(res.status_code, 200)
        self.assertIn(doc['name'].encode(), res.data)

        # Book Appointment
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        res_book = self.client.post('/appointments/book', data={
            'child_id': child['id'],
            'doctor_id': doc['id'],
            'appointment_date': tomorrow,
            'time_slot': '10:00 AM - 10:30 AM',
            'reason_symptoms': 'Routine 9-month checkup and mild cold',
            'notes': 'First time visit'
        }, follow_redirects=True)
        self.assertEqual(res_book.status_code, 200)
        self.assertIn(b"Appointment booked with", res_book.data)

        # Verify appointment in DB
        booked = db_manager.get_appointments_by_parent(1)
        self.assertEqual(len(booked), 1)
        self.assertEqual(booked[0]['status'], 'confirmed')
        self.assertEqual(booked[0]['doctor_name'], doc['name'])

        # Cancel Appointment
        res_cancel = self.client.post(f'/appointments/{booked[0]["id"]}/cancel', follow_redirects=True)
        self.assertEqual(res_cancel.status_code, 200)
        booked_after = db_manager.get_appointments_by_parent(1)
        self.assertEqual(booked_after[0]['status'], 'cancelled')

    # 6. Nutrition & Symptoms Educational Guides
    def test_nutrition_and_symptoms_guides(self):
        # Publicly accessible routes
        res_nutri = self.client.get('/nutrition')
        self.assertEqual(res_nutri.status_code, 200)
        self.assertIn(b"Pediatric Nutrition", res_nutri.data)
        self.assertIn(b"Apple &amp; Oats Porridge", res_nutri.data)

        res_symp = self.client.get('/symptoms')
        self.assertEqual(res_symp.status_code, 200)
        self.assertIn(b"Immediate Pediatric Emergency Red Flags", res_symp.data)
        self.assertIn(b"Infant Choking Relief", res_symp.data)

    # 7. Parent Data Isolation & Security
    def test_parent_data_isolation(self):
        # Parent 1 registers and adds a child
        self.register_and_login("parent1@test.com", "pass123", "Parent One")
        self.add_child("Child One", "2025-01-01", "male")
        child_p1 = db_manager.get_children_by_parent(1)[0]
        self.client.get('/logout')

        # Parent 2 registers
        self.register_and_login("parent2@test.com", "pass123", "Parent Two")
        
        # Parent 2 cannot view Parent 1's child detail
        res = self.client.get(f'/children/{child_p1["id"]}', follow_redirects=True)
        self.assertIn(b"Child profile not found or access denied", res.data)

        # Parent 2 cannot delete Parent 1's child
        res_del = self.client.post(f'/children/{child_p1["id"]}/delete', follow_redirects=True)
        self.assertEqual(len(db_manager.get_children_by_parent(1)), 1)

if __name__ == '__main__':
    unittest.main()
