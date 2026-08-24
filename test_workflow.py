import unittest
import os
import sqlite3
from app import app
from database import init_db, get_db_connection

class TestPick4Me3PartyArchitecture(unittest.TestCase):
    def setUp(self):
        self.db_path = 'pick4me.db'
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except Exception:
                pass
        
        init_db()
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

    def test_full_3_party_peer_workflow(self):
        print("\n=======================================================")
        print("STARTING PICK4ME 3-PARTY PEER LOGISTICS TEST")
        print("=======================================================")

        # Step 1: Register Shopper/Merchant (Shop Owner)
        print("Step 1: Registering Store Owner (Amit Shopkeeper)...")
        res = self.client.post('/register', data={
            'name': 'Amit Xerox & Books',
            'email': 'amit.books@campus.edu',
            'phone': '+91 98765 11111',
            'password': 'password123',
            'confirm_password': 'password123',
            'location': 'Near Main Gate Market',
            'role': 'shopper',
            'upi_id': 'amitbooks@upi'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        # Step 2: Store Owner sets up Shop & catalogs a ₹120 Lab Kit
        print("Step 2: Store Owner setting up Shop profile & ₹120 Lab Kit...")
        res = self.client.post('/merchant/shop', data={
            'shop_name': 'Amit Campus Book Store',
            'category': 'Stationery',
            'address': 'Commercial Block #2, Gate 1',
            'landmark': 'Main Gate',
            'phone': '+91 98765 11111',
            'description': 'All engineering stationery, lab kits, and notebooks.'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        res = self.client.post('/merchant/products/add', data={
            'name': 'Chemistry Lab Kit',
            'category': 'Stationery',
            'price': '120.0',
            'description': 'Complete manual, goggles & apron'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        conn = get_db_connection()
        product = conn.execute("SELECT * FROM products WHERE name = 'Chemistry Lab Kit'").fetchone()
        shop = conn.execute("SELECT * FROM shops WHERE owner_id = (SELECT id FROM users WHERE email='amit.books@campus.edu')").fetchone()
        shopper_user_id = shop['owner_id']
        conn.close()
        self.assertIsNotNone(product)
        self.assertIsNotNone(shop)

        # Step 3: Register Customer A (Order Placer / Buyer)
        print("Step 3: Registering Customer A (Priya Sharma - Buyer)...")
        self.client.get('/logout', follow_redirects=True)
        res = self.client.post('/register', data={
            'name': 'Priya Sharma',
            'email': 'priya.customer@campus.edu',
            'phone': '+91 98765 22222',
            'password': 'password123',
            'confirm_password': 'password123',
            'location': 'Hostel 4, Room 102',
            'role': 'customer',
            'upi_id': 'priya@okhdfcbank'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        # Step 4: Customer A adds Lab Kit to cart & checks out (Near Gate tier ₹35 reward)
        print("Step 4: Customer A checking out with Near Gate Tier (₹35 Delivery Fee)...")
        self.client.post('/cart/add', data={'product_id': product['id'], 'quantity': 1}, follow_redirects=True)
        res = self.client.post('/cart/checkout', data={
            'delivery_address': 'Hostel 4, Room 102',
            'phone': '+91 98765 22222',
            'distance_tier': 'near_gate',
            'is_urgent': '0'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        conn = get_db_connection()
        order = conn.execute("SELECT * FROM orders WHERE customer_id = (SELECT id FROM users WHERE email='priya.customer@campus.edu')").fetchone()
        conn.close()
        self.assertIsNotNone(order)
        self.assertEqual(order['product_amount'], 120.0)
        self.assertEqual(order['delivery_fee'], 35.0)
        self.assertEqual(order['total_amount'], 155.0)
        print(f"✓ Order #ORD-{order['id']} created: Item ₹120 + Commuter Reward ₹35 = Total ₹155.00")

        # Step 5: Customer A pays ₹155 to Admin Escrow
        print("Step 5: Customer A paying ₹155 in advance to Admin Escrow...")
        res = self.client.post(f"/pay/escrow/{order['id']}/confirm", follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        conn = get_db_connection()
        order_paid = conn.execute("SELECT * FROM orders WHERE id = ?", (order['id'],)).fetchone()
        conn.close()
        self.assertEqual(order_paid['status'], 'Paid_Pending_Commuter')
        self.assertEqual(order_paid['payment_status'], 'Escrow_Held')

        # Step 6: Register Customer B (Peer Commuter / Deliverer)
        print("Step 6: Registering Customer B (Rahul Verma - Peer Commuter)...")
        self.client.get('/logout', follow_redirects=True)
        res = self.client.post('/register', data={
            'name': 'Rahul Verma',
            'email': 'rahul.commuter@campus.edu',
            'phone': '+91 98765 33333',
            'password': 'password123',
            'confirm_password': 'password123',
            'location': 'Hostel 2, Room 301',
            'role': 'customer',
            'upi_id': 'rahul@paytm'
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        # Step 7: Customer B browses Deliveries board and claims order
        print("Step 7: Customer B claiming the delivery task...")
        res = self.client.post(f"/orders/{order['id']}/claim", follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        conn = get_db_connection()
        order_claimed = conn.execute("SELECT * FROM orders WHERE id = ?", (order['id'],)).fetchone()
        commuter_user_id = order_claimed['commuter_id']
        conn.close()
        self.assertEqual(order_claimed['status'], 'Accepted_By_Commuter')

        # Step 8: STAGE 1 - Shopkeeper (or Commuter) confirms Shop Pickup
        print("Step 8: STAGE 1 - Confirming Shop Pickup Handover...")
        res = self.client.post(f"/orders/{order['id']}/confirm-pickup", follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        conn = get_db_connection()
        order_picked = conn.execute("SELECT * FROM orders WHERE id = ?", (order['id'],)).fetchone()
        shopper_wallet = conn.execute("SELECT wallet_balance FROM users WHERE id = ?", (shopper_user_id,)).fetchone()
        conn.close()
        self.assertEqual(order_picked['status'], 'Picked_Up_From_Shop')
        self.assertEqual(order_picked['shop_payment_status'], 'Released_To_Shop')
        self.assertEqual(shopper_wallet['wallet_balance'], 120.0)
        print("✓ STAGE 1 SUCCESS: ₹120.00 Item Cost automatically credited to Shopkeeper's Wallet!")

        # Step 9: STAGE 2 - Customer B delivers to Customer A and enters Customer A's Delivery OTP
        print("Step 9: STAGE 2 - Verifying Customer Delivery OTP Handover...")
        delivery_otp = order_picked['delivery_otp']
        res = self.client.post(f"/orders/{order['id']}/verify-delivery-otp", data={
            'delivery_otp': delivery_otp
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)

        conn = get_db_connection()
        order_completed = conn.execute("SELECT * FROM orders WHERE id = ?", (order['id'],)).fetchone()
        commuter_wallet = conn.execute("SELECT wallet_balance FROM users WHERE id = ?", (commuter_user_id,)).fetchone()
        conn.close()

        self.assertEqual(order_completed['status'], 'Completed')
        self.assertEqual(order_completed['delivery_payment_status'], 'Released_To_Commuter')
        self.assertEqual(order_completed['payment_status'], 'Fully_Settled')
        # Fast delivery awards ₹35 base + ₹10 Speed Bonus = ₹45.00
        self.assertEqual(commuter_wallet['wallet_balance'], 45.0)
        print("✓ STAGE 2 SUCCESS: ₹45.00 (₹35 Reward + ₹10 Speed Bonus) automatically credited to Customer B's Wallet!")

        print("\n=======================================================")
        print("ALL 3-PARTY PEER LOGISTICS & 2-STAGE PAYOUT TESTS PASSED!")
        print("=======================================================\n")

if __name__ == '__main__':
    unittest.main()
