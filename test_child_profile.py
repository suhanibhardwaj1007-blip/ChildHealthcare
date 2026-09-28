import unittest
import time
from datetime import date, timedelta
from app import app
from database import db_manager

class ChildProfileTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

        # Register a test parent
        self.parent_email = f"parent.test.{int(time.time()*1000)}@example.com"
        self.client.post('/register', data={
            'full_name': 'Rohan Sharma',
            'email': self.parent_email,
            'phone': '+91 9876543210',
            'password': 'SecurePassword123',
            'confirm_password': 'SecurePassword123',
            'role': 'parent'
        }, follow_redirects=True)

    def test_01_unauthorized_access_redirects(self):
        """Test accessing /children/add without login redirects to /login"""
        self.client.get('/logout', follow_redirects=True)
        response = self.client.get('/children/add', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.headers['Location'])
        print("PASS: Unauthorized access to child routes properly protected.")

    def test_02_render_add_child_form(self):
        """Test GET /children/add renders the registration form"""
        response = self.client.get('/children/add')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Add Child Profile', response.data)
        self.assertIn(b'Date of Birth', response.data)
        self.assertIn(b'Blood Group', response.data)
        print("PASS: Add child profile form renders with all required fields.")

    def test_03_create_child_success(self):
        """Test adding a child profile successfully"""
        payload = {
            'name': 'Aarav Sharma',
            'dob': '2024-06-15',
            'gender': 'male',
            'blood_group': 'B+',
            'birth_weight_kg': '3.4',
            'birth_height_cm': '51.0',
            'allergies': 'Cow milk protein sensitivity',
            'medical_notes': 'Vaccinated at birth with BCG and OPV'
        }
        response = self.client.post('/children/add', data=payload, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Aarav Sharma', response.data)
        self.assertIn(b'Cow milk protein sensitivity', response.data)
        print("PASS: Child profile created and redirects to digital health card.")

    def test_04_create_child_future_dob_rejected(self):
        """Test child DOB in the future is rejected"""
        future_date = (date.today() + timedelta(days=10)).isoformat()
        payload = {
            'name': 'Future Child',
            'dob': future_date,
            'gender': 'female'
        }
        response = self.client.post('/children/add', data=payload, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Date of birth cannot be in the future', response.data)
        print("PASS: Future date of birth correctly rejected.")

    def test_05_create_child_empty_name_rejected(self):
        """Test child with empty name is rejected"""
        payload = {
            'name': '   ',
            'dob': '2025-01-01',
            'gender': 'male'
        }
        response = self.client.post('/children/add', data=payload, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Please enter the child', response.data)
        print("PASS: Empty child name properly validated.")

    def test_06_dashboard_displays_child_card(self):
        """Test that registered children appear on the dashboard"""
        self.client.post('/children/add', data={
            'name': 'Ananya Sharma',
            'dob': '2023-08-20',
            'gender': 'female',
            'blood_group': 'O+'
        }, follow_redirects=True)

        response = self.client.get('/dashboard')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Ananya Sharma', response.data)
        self.assertIn(b'Registered Children (1)', response.data)
        print("PASS: Registered children rendered on dashboard with health cards.")

    def test_07_parent_data_isolation(self):
        """Test that parent B cannot access parent A's child profile"""
        # Create child for parent A
        res = self.client.post('/children/add', data={
            'name': 'Child of Parent A',
            'dob': '2024-01-10',
            'gender': 'male'
        }, follow_redirects=True)
        
        # Extract child ID from database
        user = db_manager.get_user_by_email(self.parent_email)
        children = db_manager.get_children_by_parent(user['id'])
        child_id = children[0]['id']

        # Logout Parent A and register Parent B
        self.client.get('/logout', follow_redirects=True)
        parent_b_email = f"parent.b.{int(time.time()*1000)}@example.com"
        self.client.post('/register', data={
            'full_name': 'Parent B',
            'email': parent_b_email,
            'password': 'SecurePassword123',
            'confirm_password': 'SecurePassword123',
            'role': 'parent'
        }, follow_redirects=True)

        # Parent B tries to access Parent A's child profile
        response = self.client.get(f'/children/{child_id}', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Child profile not found or access denied', response.data)
        print("PASS: Parent data isolation verified (cross-parent access prevented).")

    def test_08_delete_child_profile(self):
        """Test deleting a child profile"""
        # Add child
        self.client.post('/children/add', data={
            'name': 'Temporary Child',
            'dob': '2024-02-14',
            'gender': 'male'
        }, follow_redirects=True)

        user = db_manager.get_user_by_email(self.parent_email)
        children = db_manager.get_children_by_parent(user['id'])
        child_id = children[0]['id']

        # Delete child
        response = self.client.post(f'/children/{child_id}/delete', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'deleted successfully', response.data)
        
        # Verify child no longer exists
        remaining = db_manager.get_children_by_parent(user['id'])
        self.assertEqual(len(remaining), 0)
        print("PASS: Child profile deleted successfully.")

    def test_09_render_edit_child_form(self):
        """Test GET /children/<id>/edit renders the edit form with pre-filled data"""
        self.client.post('/children/add', data={
            'name': 'Aarav Original',
            'dob': '2024-05-10',
            'gender': 'male',
            'blood_group': 'O+'
        }, follow_redirects=True)

        user = db_manager.get_user_by_email(self.parent_email)
        children = db_manager.get_children_by_parent(user['id'])
        child_id = children[0]['id']

        response = self.client.get(f'/children/{child_id}/edit')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Edit Child Profile', response.data)
        self.assertIn(b'Aarav Original', response.data)
        self.assertIn(b'2024-05-10', response.data)
        print("PASS: Edit child profile form renders with pre-filled data.")

    def test_10_update_child_success(self):
        """Test POST /children/<id>/edit updates child details successfully"""
        self.client.post('/children/add', data={
            'name': 'Aarav Sharma',
            'dob': '2024-05-10',
            'gender': 'male',
            'blood_group': 'O+'
        }, follow_redirects=True)

        user = db_manager.get_user_by_email(self.parent_email)
        children = db_manager.get_children_by_parent(user['id'])
        child_id = children[0]['id']

        # Update child details
        response = self.client.post(f'/children/{child_id}/edit', data={
            'name': 'Aarav S. Sharma',
            'dob': '2024-05-12',
            'gender': 'male',
            'blood_group': 'AB+',
            'birth_weight_kg': '3.6',
            'birth_height_cm': '52.0',
            'allergies': 'Peanut allergy',
            'medical_notes': 'Updated pediatric notes'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Aarav S. Sharma', response.data)
        self.assertIn(b'Peanut allergy', response.data)
        self.assertIn(b'updated successfully', response.data)

        # Verify in DB
        updated_child = db_manager.get_child_by_id(child_id, parent_id=user['id'])
        self.assertEqual(updated_child['name'], 'Aarav S. Sharma')
        self.assertEqual(str(updated_child['dob'])[:10], '2024-05-12')
        self.assertEqual(updated_child['blood_group'], 'AB+')
        self.assertEqual(updated_child['birth_weight_kg'], 3.6)
        print("PASS: Child profile updated successfully and reflected in database.")

    def test_11_update_child_unauthorized_parent_blocked(self):
        """Test that Parent B cannot edit Parent A's child profile"""
        self.client.post('/children/add', data={
            'name': 'Parent A Child',
            'dob': '2024-03-01',
            'gender': 'female'
        }, follow_redirects=True)

        user_a = db_manager.get_user_by_email(self.parent_email)
        child_id = db_manager.get_children_by_parent(user_a['id'])[0]['id']

        # Log in as Parent B
        self.client.get('/logout', follow_redirects=True)
        parent_b_email = f"parent.b2.{int(time.time()*1000)}@example.com"
        self.client.post('/register', data={
            'full_name': 'Parent B2',
            'email': parent_b_email,
            'password': 'SecurePassword123',
            'confirm_password': 'SecurePassword123',
            'role': 'parent'
        }, follow_redirects=True)

        # Try to GET edit page
        res_get = self.client.get(f'/children/{child_id}/edit', follow_redirects=True)
        self.assertIn(b'Child profile not found or access denied', res_get.data)

        # Try to POST edit update
        res_post = self.client.post(f'/children/{child_id}/edit', data={
            'name': 'Hacked Name',
            'dob': '2024-03-01',
            'gender': 'female'
        }, follow_redirects=True)
        self.assertIn(b'Child profile not found or access denied', res_post.data)

        # Verify child name was not modified
        original_child = db_manager.get_child_by_id(child_id, parent_id=user_a['id'])
        self.assertEqual(original_child['name'], 'Parent A Child')
        print("PASS: Unauthorized parent cannot edit another user's child profile.")

if __name__ == '__main__':
    unittest.main()
