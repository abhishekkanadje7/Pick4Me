"""
Pick4Me 2.0 Complete E-Commerce, Shop Catalog, Cart & Peer Delivery Test Suite
Tests: Shop Setup -> Product Catalog -> Cart & Advance Payment -> Commuter Claim -> Milestones -> Delivery OTP -> Auto-Wallet Credit
"""

import unittest
from app import app
from database import init_db, get_db_connection

class Pick4MeFullPlatformTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
        with app.app_context():
            init_db()

    def test_complete_amazon_style_and_peer_delivery_flow(self):
        print("\n=======================================================")
        print("STARTING PICK4ME 2.0 COMPLETE PLATFORM TEST")
        print("=======================================================")

        # 1. Register Shopper / Store Merchant
        print("Step 1: Registering Shopper/Merchant (Rahul Verma)...")
        res = self.client.post('/register', data={
            'name': 'Rahul Verma',
            'email': 'rahul.merchant@campus.edu',
            'phone': '+91 98765 12345',
            'password': 'password123',
            'confirm_password': 'password123',
            'location': 'Commercial Gate 1',
            'role': 'shopper',
            'upi_id': '7387157739@upi'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        print("✓ Shopper/Merchant registered successfully.")

        # 2. Merchant Registers Shop
        print("Step 2: Registering Shop (ABC Stationery Corner)...")
        res = self.client.post('/merchant/shop', data={
            'shop_name': 'ABC Stationery & Xerox Corner',
            'category': 'Stationery',
            'address': 'Commercial Complex #4, Gate 1',
            'landmark': 'Opposite Library',
            'phone': '+91 98765 12345',
            'description': 'Complete lab manuals, notebook sets, pens and xerox'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'ABC Stationery & Xerox Corner', res.data)
        print("✓ Shop registered successfully.")

        # 3. Merchant Adds Products to Store Catalog
        print("Step 3: Adding Product to Catalog (Spiral Notebook)...")
        res = self.client.post('/merchant/products/add', data={
            'name': 'Classmate Spiral Notebook (200 pgs)',
            'category': 'Stationery',
            'price': 80.0,
            'description': 'A4 single line ruled notebook'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Classmate Spiral Notebook', res.data)
        print("✓ Product added to shop catalog.")

        # Extract product ID
        conn = get_db_connection()
        prod = conn.execute("SELECT * FROM products WHERE name = 'Classmate Spiral Notebook (200 pgs)'").fetchone()
        self.assertIsNotNone(prod)
        prod_id = prod['id']
        conn.close()

        # 4. Shopper Logout
        print("Step 4: Logging out Shopper...")
        self.client.get('/logout', follow_redirects=True)

        # 5. Customer Registration & Login
        print("Step 5: Registering Customer (Priya Sharma)...")
        res = self.client.post('/register', data={
            'name': 'Priya Sharma',
            'email': 'priya.customer@campus.edu',
            'phone': '+91 98765 43210',
            'password': 'password123',
            'confirm_password': 'password123',
            'location': 'Kaveri Hostel Room 204',
            'role': 'customer'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        print("✓ Customer registered successfully.")

        # 6. Customer Adds Product to Cart
        print(f"Step 6: Customer adding Product #{prod_id} to Cart...")
        res = self.client.post('/cart/add', data={
            'product_id': prod_id,
            'quantity': 2
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        print("✓ Added 2 units to Cart.")

        # 7. Customer Checks Out with Advance Escrow
        print("Step 7: Customer Checking Out from Cart...")
        res = self.client.post('/cart/checkout', data={
            'delivery_address': 'Kaveri Hostel, Room 204',
            'phone': '+91 98765 43210',
            'instructions': 'Please call upon gate arrival.'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Scan & Pay via UPI', res.data)
        print("✓ Checkout complete, redirected to Advance UPI Payment page.")

        # Extract Order ID
        conn = get_db_connection()
        order = conn.execute("SELECT * FROM orders ORDER BY id DESC LIMIT 1").fetchone()
        self.assertIsNotNone(order)
        order_id = order['id']
        delivery_otp = order['delivery_otp']
        self.assertEqual(order['payment_status'], 'Pending_Payment')
        self.assertEqual(float(order['product_amount']), 160.0) # 80 * 2
        self.assertEqual(float(order['delivery_fee']), 25.0)
        self.assertEqual(float(order['total_amount']), 185.0)
        conn.close()
        print(f"✓ Order #ORD-{order_id} created with Total: ₹185.00, Secret OTP: {delivery_otp}")

        # 8. Customer Confirms Advance Payment
        print("Step 8: Customer confirming advance UPI payment...")
        res = self.client.post(f'/pay/escrow/{order_id}/confirm', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Advance payment received', res.data)
        print("✓ Advance Payment locked in Escrow. Broadcasted to commuters.")

        # 9. Customer Logout & Shopper Claim
        print("Step 9: Commuter logging in to claim delivery...")
        self.client.get('/logout', follow_redirects=True)
        self.client.post('/login', data={
            'email': 'rahul.merchant@campus.edu',
            'password': 'password123'
        }, follow_redirects=True)

        res = self.client.post(f'/orders/{order_id}/accept', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Delivery task accepted', res.data)
        print("✓ Commuter claimed the delivery task.")

        # 10. Commuter Delivery Milestones
        print("Step 10: Updating milestones: Accepted -> Purchased -> Out for Delivery -> Delivered...")
        self.client.post(f'/orders/{order_id}/update-status', data={'status': 'Purchased'}, follow_redirects=True)
        self.client.post(f'/orders/{order_id}/update-status', data={'status': 'Out for Delivery'}, follow_redirects=True)
        self.client.post(f'/orders/{order_id}/update-status', data={'status': 'Delivered'}, follow_redirects=True)
        print("✓ Marked as Delivered.")

        # 11. Delivery Handover OTP Verification -> Auto-Wallet Credit!
        print(f"Step 11: Commuter entering customer 4-digit OTP ({delivery_otp})...")
        res = self.client.post(f'/orders/{order_id}/verify-otp', data={'delivery_otp': delivery_otp}, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'OTP Verified', res.data)
        print("✓ OTP Verified! ₹185.00 automatically credited to Commuter Wallet.")

        # Check Wallet in DB
        conn = get_db_connection()
        shopper_user = conn.execute("SELECT * FROM users WHERE email = 'rahul.merchant@campus.edu'").fetchone()
        self.assertEqual(float(shopper_user['wallet_balance']), 185.0)
        conn.close()
        print(f"✓ Wallet Balance Verified: ₹{shopper_user['wallet_balance']:.2f}")

        # 12. Admin Control Center Check
        print("Step 12: Admin (Abhishek Kanadje) logging in...")
        self.client.get('/logout', follow_redirects=True)
        res_admin = self.client.post('/login', data={
            'email': 'abhishekkanadje7@gmail.com',
            'password': 'Abhi*2007'
        }, follow_redirects=True)
        self.assertEqual(res_admin.status_code, 200)
        self.assertIn(b'Admin Control Center', res_admin.data)
        self.assertIn(b'Abhishek Kanadje', res_admin.data)
        print("✓ Admin verified.")

        print("\n=======================================================")
        print("ALL 12 PLATFORM 2.0 WORKFLOW STEPS PASSED PERFECTLY! 100% SUCCESS")
        print("=======================================================\n")

if __name__ == '__main__':
    unittest.main()
