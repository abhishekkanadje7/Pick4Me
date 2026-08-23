import sqlite3
import os
import random
from werkzeug.security import generate_password_hash

DATABASE_NAME = os.environ.get('DATABASE_PATH', os.path.join(os.path.dirname(__file__), 'pick4me.db'))

def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Users Table (with Verification and Wallet)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('customer', 'shopper', 'admin')),
            location TEXT NOT NULL,
            upi_id TEXT DEFAULT '7387157739@upi',
            qr_code TEXT DEFAULT 'upi_qr.png',
            is_verified INTEGER NOT NULL DEFAULT 1,
            wallet_balance REAL NOT NULL DEFAULT 0.0,
            id_proof TEXT DEFAULT 'Verified Campus Member',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 2. Shops Table (Local Stores created by Shoppers/Merchants)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS shops (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_id INTEGER NOT NULL,
            shop_name TEXT NOT NULL,
            category TEXT NOT NULL,
            address TEXT NOT NULL,
            landmark TEXT DEFAULT '',
            phone TEXT NOT NULL,
            description TEXT DEFAULT '',
            image TEXT DEFAULT '',
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (owner_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')

    # 3. Products Table (Shop Catalog)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            shop_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            description TEXT DEFAULT '',
            image TEXT DEFAULT '',
            in_stock INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (shop_id) REFERENCES shops (id) ON DELETE CASCADE
        )
    ''')

    # 4. Cart Items Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cart_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
        )
    ''')

    # 5. Orders Table (Store Orders & Custom Peer Errands with Escrow & OTP)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_type TEXT NOT NULL DEFAULT 'shop_order', -- 'shop_order' or 'custom_request'
            customer_id INTEGER NOT NULL,
            shopper_id INTEGER DEFAULT NULL,
            shop_id INTEGER DEFAULT NULL,
            items_summary TEXT NOT NULL,
            product_amount REAL NOT NULL,
            delivery_fee REAL NOT NULL,
            total_amount REAL NOT NULL,
            payment_status TEXT NOT NULL DEFAULT 'Pending_Payment', -- 'Pending_Payment', 'Escrow_Held', 'Released_To_Shopper', 'Refunded'
            delivery_otp TEXT NOT NULL, -- 4-digit code for delivery confirmation
            delivery_address TEXT NOT NULL,
            phone TEXT NOT NULL,
            instructions TEXT DEFAULT '',
            status TEXT NOT NULL DEFAULT 'Paid_Pending_Shopper', -- 'Pending_Payment', 'Paid_Pending_Shopper', 'Accepted', 'Purchased', 'Out for Delivery', 'Delivered', 'Completed', 'Cancelled'
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES users (id),
            FOREIGN KEY (shopper_id) REFERENCES users (id),
            FOREIGN KEY (shop_id) REFERENCES shops (id)
        )
    ''')

    # 6. Wallet Transactions Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS wallet_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            order_id INTEGER DEFAULT NULL,
            amount REAL NOT NULL,
            type TEXT NOT NULL, -- 'credit_earnings', 'credit_product_sale', 'debit_withdrawal'
            description TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # 7. Ensure Abhishek Kanadje's Verified Admin is configured
    cursor.execute("SELECT id FROM users WHERE email = 'abhishekkanadje7@gmail.com'")
    existing_admin = cursor.fetchone()
    if not existing_admin:
        cursor.execute('''
            INSERT INTO users (name, email, phone, password_hash, role, location, upi_id, qr_code, is_verified, wallet_balance)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, 0.0)
        ''', (
            'Abhishek Kanadje',
            'abhishekkanadje7@gmail.com',
            '+91 73871 57739',
            generate_password_hash('Abhi*2007', method='pbkdf2:sha256'),
            'admin',
            'Campus Central Headquarters',
            '7387157739@upi',
            'upi_qr.png'
        ))
    else:
        cursor.execute('''
            UPDATE users
            SET password_hash = ?, role = 'admin', upi_id = '7387157739@upi', qr_code = 'upi_qr.png', is_verified = 1
            WHERE email = 'abhishekkanadje7@gmail.com'
        ''', (generate_password_hash('Abhi*2007', method='pbkdf2:sha256'),))

    conn.commit()
    conn.close()

def generate_otp():
    """Generates a secure 4-digit delivery handover OTP."""
    return str(random.randint(1000, 9999))
