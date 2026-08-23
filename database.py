import sqlite3
import os
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

    # Create Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('customer', 'shopper', 'admin')),
            location TEXT NOT NULL,
            upi_id TEXT DEFAULT '',
            qr_code TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create Requests table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            shopper_id INTEGER DEFAULT NULL,
            product_name TEXT NOT NULL,
            description TEXT DEFAULT '',
            category TEXT NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            shop_name TEXT NOT NULL,
            shop_address TEXT NOT NULL,
            delivery_address TEXT NOT NULL,
            phone TEXT NOT NULL,
            estimated_price REAL NOT NULL,
            reward REAL NOT NULL,
            instructions TEXT DEFAULT '',
            status TEXT NOT NULL DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES users (id),
            FOREIGN KEY (shopper_id) REFERENCES users (id)
        )
    ''')

    # Create Orders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id INTEGER UNIQUE NOT NULL,
            customer_id INTEGER NOT NULL,
            shopper_id INTEGER NOT NULL,
            product_amount REAL NOT NULL,
            reward REAL NOT NULL,
            total_amount REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'Accepted',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (request_id) REFERENCES requests (id),
            FOREIGN KEY (customer_id) REFERENCES users (id),
            FOREIGN KEY (shopper_id) REFERENCES users (id)
        )
    ''')

    # Create Payments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pending',
            payment_method TEXT NOT NULL DEFAULT 'UPI',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (order_id) REFERENCES orders (id)
        )
    ''')

    conn.commit()

    # Seed demo users if not present
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        seed_demo_data(conn)
    else:
        # Ensure Abhishek's admin account is always updated and ready
        cursor.execute("SELECT id FROM users WHERE email = 'abhishekkanadje7@gmail.com'")
        if not cursor.fetchone():
            cursor.execute('''
                INSERT INTO users (name, email, phone, password_hash, role, location, upi_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                'Abhishek Kanadje',
                'abhishekkanadje7@gmail.com',
                '+91 98765 00000',
                generate_password_hash('Abhi*2007', method='pbkdf2:sha256'),
                'admin',
                'Campus Admin Block, Room 101',
                'abhishek@upi'
            ))
        else:
            cursor.execute('''
                UPDATE users SET password_hash = ?, role = 'admin' WHERE email = 'abhishekkanadje7@gmail.com'
            ''', (generate_password_hash('Abhi*2007', method='pbkdf2:sha256'),))
        conn.commit()

    conn.close()

def seed_demo_data(conn):
    cursor = conn.cursor()

    # Seed Customer
    cursor.execute('''
        INSERT INTO users (name, email, phone, password_hash, role, location, upi_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        'Priya Sharma',
        'customer@pick4me.demo',
        '+91 98765 43210',
        generate_password_hash('customer123', method='pbkdf2:sha256'),
        'customer',
        'Kaveri Hostel, Room 204, Campus East',
        ''
    ))
    customer_id = cursor.lastrowid

    # Seed Shopper
    cursor.execute('''
        INSERT INTO users (name, email, phone, password_hash, role, location, upi_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        'Rahul Verma',
        'shopper@pick4me.demo',
        '+91 98765 12345',
        generate_password_hash('shopper123', method='pbkdf2:sha256'),
        'shopper',
        'Campus Library & Student Center',
        'rahul.verma@okhdfcbank'
    ))
    shopper_id = cursor.lastrowid

    # Seed Admin (Abhishek Kanadje)
    cursor.execute('''
        INSERT INTO users (name, email, phone, password_hash, role, location, upi_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        'Abhishek Kanadje',
        'abhishekkanadje7@gmail.com',
        '+91 98765 00000',
        generate_password_hash('Abhi*2007', method='pbkdf2:sha256'),
        'admin',
        'Campus Admin Block, Room 101',
        'abhishek@upi'
    ))

    # Seed initial requests
    # 1. Available Pending request for instant demonstration
    cursor.execute('''
        INSERT INTO requests (customer_id, product_name, description, category, quantity, shop_name, shop_address, delivery_address, phone, estimated_price, reward, instructions, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        customer_id,
        'Classmate Spiral Notebook (200 pgs) + Blue Pen',
        'Need single ruled spiral notebook and one blue ballpoint pen for tomorrow\'s lab submission.',
        'Stationery',
        2,
        'ABC Stationery & Xerox Corner',
        'Near College Main Gate, Shop #4',
        'Kaveri Hostel, Room 204, 2nd Floor',
        '+91 98765 43210',
        140.0,
        35.0,
        'Please call when you reach hostel gate.',
        'Pending'
    ))

    # 2. Another pending request
    cursor.execute('''
        INSERT INTO requests (customer_id, product_name, description, category, quantity, shop_name, shop_address, delivery_address, phone, estimated_price, reward, instructions, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        customer_id,
        'Cold Coffee & Grilled Sandwich',
        'One iced hazelnut cold coffee and veg cheese sandwich from canteen.',
        'Food & Beverages',
        1,
        'Campus Central Canteen',
        'Food Court, Student Activity Center',
        'Department of Computer Engineering, Lab 3',
        '+91 98765 43210',
        120.0,
        25.0,
        'I am in the lab, please text on WhatsApp upon arrival.',
        'Pending'
    ))

    # 3. Seed an already completed request & order to show history
    cursor.execute('''
        INSERT INTO requests (customer_id, shopper_id, product_name, description, category, quantity, shop_name, shop_address, delivery_address, phone, estimated_price, reward, instructions, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        customer_id,
        shopper_id,
        'Paracetamol 650mg + ORS Sachet',
        'Mild fever medicines from pharmacy.',
        'Medicines & Pharmacy',
        1,
        'Apollo Campus Pharmacy',
        'Gate 2 Commercial Complex',
        'Kaveri Hostel, Room 204',
        '+91 98765 43210',
        60.0,
        30.0,
        'Urgent delivery please.',
        'Completed'
    ))
    past_req_id = cursor.lastrowid

    cursor.execute('''
        INSERT INTO orders (request_id, customer_id, shopper_id, product_amount, reward, total_amount, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        past_req_id,
        customer_id,
        shopper_id,
        60.0,
        30.0,
        90.0,
        'Completed'
    ))
    past_order_id = cursor.lastrowid

    cursor.execute('''
        INSERT INTO payments (order_id, amount, status, payment_method)
        VALUES (?, ?, ?, ?)
    ''', (
        past_order_id,
        90.0,
        'Confirmed',
        'UPI'
    ))

    conn.commit()
