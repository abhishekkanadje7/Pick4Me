"""
Pick4Me 2.0 Dynamic SLA, Distance Tiers, Speed Bonus & Rush Mode Verification Test
"""

import unittest
from app import app
from database import init_db, get_db_connection

class Pick4MeSLAMarketplaceTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
        with app.app_context():
            init_db()

    def test_complete_dynamic_sla_and_distance_flow(self):
        print("\n=======================================================")
        print("STARTING PICK4ME 2.0 DYNAMIC SLA & DISTANCE REWARD TEST")
        print("=======================================================")

        # 1. Register Shopper / Store Merchant
        print("Step 1: Registering Shopper/Merchant (Rahul Verma)...")
        res = self.client.post('/register', data={
            'name': 'Rahul Verma',
            'email': 'rahul.merchant@campus.edu',
            'phone': '+91 98765 12345',
            'password': 'password123',
            'confirm_password': 'password123',
            'location': 'Gate 1 Commercial Complex',
            'role': 'shopper',
            'upi_id': '7387157739@upi'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        # 2. Register Shop & Add Product
        print("Step 2: Setting up Store & Catalog Item (₹90 Lab Manual)...")
        self.client.post('/merchant/shop', data={
            'shop_name': 'Campus Tech & Stationery Hub',
            'category': 'Stationery',
            'address': 'Gate 1, Shop #2',
            'landmark': 'Near Main Entrance',
            'phone': '+91 98765 12345',
            'description': 'Lab manuals and calculators'
        }, follow_redirects=True)

        self.client.post('/merchant/products/add', data={
            'name': 'Physics Lab Manual 2026',
            'category': 'Stationery',
            'price': 90.0,
            'description': 'Latest curriculum standard manual'
        }, follow_redirects=True)

        conn = get_db_connection()
        prod = conn.execute("SELECT * FROM products WHERE name = 'Physics Lab Manual 2026'").fetchone()
        self.assertIsNotNone(prod)
        prod_id = prod['id']
        conn.close()

        # 3. Customer Registration
        print("Step 3: Registering Customer (Priya Sharma)...")
        self.client.get('/logout', follow_redirects=True)
        self.client.post('/register', data={
            'name': 'Priya Sharma',
            'email': 'priya.student@campus.edu',
            'phone': '+91 98765 43210',
            'password': 'password123',
            'confirm_password': 'password123',
            'location': 'Hostel Kaveri Room 102',
            'role': 'customer'
        }, follow_redirects=True)

        # 4. Customer adds to cart & checks out with Near Gate Tier (₹35) + Rush Mode (+₹15)
        print("Step 4: Customer adding to cart & checking out with Near Gate Tier + Rush Mode...")
        self.client.post('/cart/add', data={'product_id': prod_id, 'quantity': 1}, follow_redirects=True)

        res = self.client.post('/cart/checkout', data={
            'delivery_address': 'Hostel Kaveri, Room 102',
            'phone': '+91 98765 43210',
            'distance_tier': 'near_gate', # ₹35 base fee
            'is_urgent': '1', # +₹15 surge = ₹50 delivery fee
            'instructions': 'Exam starts in 40 mins, please deliver fast!'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        # Verify Order in DB: Product ₹90 + Delivery ₹50 (35+15) = Total ₹140
        conn = get_db_connection()
        order = conn.execute("SELECT * FROM orders ORDER BY id DESC LIMIT 1").fetchone()
        self.assertIsNotNone(order)
        order_id = order['id']
        delivery_otp = order['delivery_otp']
        self.assertEqual(order['distance_tier'], 'near_gate')
        self.assertEqual(order['is_urgent'], 1)
        self.assertEqual(float(order['product_amount']), 90.0)
        self.assertEqual(float(order['delivery_fee']), 50.0)
        self.assertEqual(float(order['total_amount']), 140.0)
        conn.close()
        print(f"✓ Order #ORD-{order_id} verified: Items ₹90 + Dynamic SLA Delivery ₹50 = Total ₹140.00")

        # 5. Customer Confirms Advance Escrow Payment
        print("Step 5: Customer confirming Advance Escrow Payment...")
        self.client.post(f'/pay/escrow/{order_id}/confirm', follow_redirects=True)

        # 6. Commuter Accepts Order
        print("Step 6: Commuter logging in & accepting order...")
        self.client.get('/logout', follow_redirects=True)
        self.client.post('/login', data={'email': 'rahul.merchant@campus.edu', 'password': 'password123'}, follow_redirects=True)
        self.client.post(f'/orders/{order_id}/accept', follow_redirects=True)

        # 7. Commuter Milestones & Fast Handover OTP Verification (Speed Bonus awarded)
        print("Step 7: Commuter completing delivery and verifying 4-digit OTP...")
        self.client.post(f'/orders/{order_id}/update-status', data={'status': 'Purchased'}, follow_redirects=True)
        self.client.post(f'/orders/{order_id}/update-status', data={'status': 'Out for Delivery'}, follow_redirects=True)
        self.client.post(f'/orders/{order_id}/update-status', data={'status': 'Delivered'}, follow_redirects=True)

        res_otp = self.client.post(f'/orders/{order_id}/verify-otp', data={'delivery_otp': delivery_otp}, follow_redirects=True)
        self.assertEqual(res_otp.status_code, 200)
        self.assertIn(b'OTP Verified', res_otp.data)

        # 8. Verify Wallet Balance (Product ₹90 + Fee ₹50 + Speed Bonus ₹10 = ₹150)
        conn = get_db_connection()
        user = conn.execute("SELECT * FROM users WHERE email = 'rahul.merchant@campus.edu'").fetchone()
        self.assertEqual(float(user['wallet_balance']), 150.0)
        conn.close()
        print(f"✓ Commuter Wallet credited ₹150.00 (includes ₹10 Speed Bonus for fast delivery)!")

        # 9. Test Late Delivery Penalty Scenario
        print("\nTesting Delayed Delivery Penalty (-₹10)...")
        with self.client.session_transaction() as sess:
            current_shopper_id = sess['user_id']

        conn = get_db_connection()
        conn.execute('''
            INSERT INTO orders (
                order_type, customer_id, shopper_id, items_summary, product_amount, delivery_fee, total_amount,
                distance_tier, distance_km, is_urgent, target_duration_mins, accepted_at,
                payment_status, delivery_otp, delivery_address, phone, status
            ) VALUES (
                'custom_request', 3, ?, 'Urgent Medicines', 100.0, 30.0, 130.0,
                'within_campus', 0.8, 0, 25, '2026-08-23 18:00:00',
                'Escrow_Held', '9999', 'Hostel Kaveri Room 102', '+91 98765 43210', 'Delivered'
            )
        ''', (current_shopper_id,))
        conn.commit()
        late_order_id = conn.execute("SELECT id FROM orders ORDER BY id DESC LIMIT 1").fetchone()['id']
        conn.close()

        # Commuter enters OTP for delayed order
        res_late = self.client.post(f'/orders/{late_order_id}/verify-otp', data={'delivery_otp': '9999'}, follow_redirects=True)
        self.assertEqual(res_late.status_code, 200)
        self.assertIn(b'OTP Verified', res_late.data)
        
        conn = get_db_connection()
        late_order = conn.execute("SELECT * FROM orders WHERE id = ?", (late_order_id,)).fetchone()
        self.assertEqual(float(late_order['delay_penalty']), 10.0)
        self.assertEqual(float(late_order['final_payout']), 120.0) # 100 item + (30 fee - 10 penalty)
        conn.close()
        print(f"✓ Late Penalty verified: ₹10 deducted for delayed delivery past SLA window.")

        print("\n=======================================================")
        print("ALL DYNAMIC DISTANCE, SPEED BONUS & PENALTY TESTS PASSED!")
        print("=======================================================\n")

if __name__ == '__main__':
    unittest.main()
