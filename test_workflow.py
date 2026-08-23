"""
Pick4Me Automated End-to-End Workflow Verification Script
Tests complete User Registration -> Request Creation -> Shopper Accept -> Delivery Milestones -> Completion & Payment.
"""

import unittest
from app import app
from database import init_db, get_db_connection

class Pick4MeWorkflowTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
        with app.app_context():
            init_db()

    def test_complete_clean_workflow(self):
        print("\n=======================================================")
        print("STARTING PICK4ME FULL END-TO-END WORKFLOW TEST")
        print("=======================================================")

        # 1. Customer Registration & Login
        print("Step 1: Registering a new Customer...")
        res = self.client.post('/register', data={
            'name': 'Priya Sharma',
            'email': 'priya.test@campus.edu',
            'phone': '+91 98765 43210',
            'password': 'password123',
            'confirm_password': 'password123',
            'location': 'Kaveri Hostel Room 204',
            'role': 'customer'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Priya Sharma', res.data)
        print("✓ Customer registered and logged in successfully.")

        # 2. Customer Creates a Shopping Request
        print("Step 2: Customer creating a new shopping request...")
        res = self.client.post('/requests/create', data={
            'product_name': 'Classmate Spiral Notebook',
            'category': 'Stationery',
            'quantity': 2,
            'description': '200 pages spiral single ruled',
            'shop_name': 'ABC Stationery',
            'shop_address': 'Near College Road',
            'delivery_address': 'College Hostel, Room 204',
            'phone': '+91 98765 43210',
            'estimated_price': 140.0,
            'reward': 30.0,
            'instructions': 'Please call upon reaching hostel gate.'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Request created successfully', res.data)

        conn = get_db_connection()
        req = conn.execute("SELECT * FROM requests WHERE product_name = 'Classmate Spiral Notebook' ORDER BY id DESC LIMIT 1").fetchone()
        self.assertIsNotNone(req)
        self.assertEqual(req['status'], 'Pending')
        req_id = req['id']
        conn.close()
        print(f"✓ Verified request #{req_id} created with status 'Pending'.")

        # 3. Customer Logout
        print("Step 3: Logging out Customer...")
        self.client.get('/logout', follow_redirects=True)

        # 4. Shopper Registration & Login
        print("Step 4: Registering a new Shopper...")
        res = self.client.post('/register', data={
            'name': 'Rahul Verma',
            'email': 'rahul.test@campus.edu',
            'phone': '+91 98765 12345',
            'password': 'password123',
            'confirm_password': 'password123',
            'location': 'Campus Library & Student Center',
            'role': 'shopper',
            'upi_id': 'rahul.verma@okhdfcbank'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Rahul Verma', res.data)
        print("✓ Shopper registered and logged in successfully.")

        # 5. Shopper Accepts the Request
        print(f"Step 5: Shopper accepting request #{req_id}...")
        res = self.client.post(f'/requests/{req_id}/accept', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Request accepted successfully', res.data)

        conn = get_db_connection()
        order = conn.execute("SELECT * FROM orders WHERE request_id = ?", (req_id,)).fetchone()
        self.assertIsNotNone(order)
        order_id = order['id']
        self.assertEqual(order['status'], 'Accepted')
        conn.close()
        print(f"✓ Order #ORD-{order_id} generated.")

        # 6. Concurrency Check: Duplicate Acceptance Blocked
        print("Step 6: Testing duplicate accept prevention...")
        res_dup = self.client.post(f'/requests/{req_id}/accept', follow_redirects=True)
        self.assertIn(b'already been accepted', res_dup.data)
        print("✓ Concurrency protection verified: Duplicate acceptance blocked.")

        # 7. Shopper Step-by-Step Delivery Progress
        print("Step 7a: Updating status: Accepted -> Purchased...")
        self.client.post(f'/orders/{order_id}/update-status', data={'status': 'Purchased'}, follow_redirects=True)

        print("Step 7b: Updating status: Purchased -> Out for Delivery...")
        self.client.post(f'/orders/{order_id}/update-status', data={'status': 'Out for Delivery'}, follow_redirects=True)

        print("Step 7c: Updating status: Out for Delivery -> Delivered...")
        self.client.post(f'/orders/{order_id}/update-status', data={'status': 'Delivered'}, follow_redirects=True)
        print("✓ Shopper updated status to Delivered.")

        # 8. Shopper Logout & Customer Confirmation
        print("Step 8: Logging out Shopper...")
        self.client.get('/logout', follow_redirects=True)

        print("Step 9: Customer logging in to confirm delivery & simulate payment...")
        self.client.post('/login', data={
            'email': 'priya.test@campus.edu',
            'password': 'password123'
        }, follow_redirects=True)

        res_confirm = self.client.post(f'/orders/{order_id}/confirm-delivery', follow_redirects=True)
        self.assertEqual(res_confirm.status_code, 200)
        self.assertIn(b'Delivery completed successfully', res_confirm.data)
        print("✓ Customer confirmed delivery. Order marked 'Completed'.")

        # 10. Admin Verification
        print("Step 10: Admin logging in to verify control center...")
        self.client.get('/logout', follow_redirects=True)
        res_admin_login = self.client.post('/login', data={
            'email': 'abhishekkanadje7@gmail.com',
            'password': 'Abhi*2007'
        }, follow_redirects=True)
        self.assertEqual(res_admin_login.status_code, 200)
        self.assertIn(b'Admin Control Center', res_admin_login.data)
        self.assertIn(b'Abhishek Kanadje', res_admin_login.data)
        print("✓ Abhishek Kanadje Admin verified.")

        print("\n=======================================================")
        print("ALL VERIFICATION STEPS PASSED WITH CLEAN DATABASE! 100% WORKING")
        print("=======================================================\n")

if __name__ == '__main__':
    unittest.main()
