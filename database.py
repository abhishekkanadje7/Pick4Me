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

    # Clean up any legacy dummy demo accounts safely
    cursor.execute('''
        DELETE FROM payments WHERE order_id IN (
            SELECT id FROM orders WHERE customer_id IN (SELECT id FROM users WHERE email LIKE '%@pick4me.demo')
            OR shopper_id IN (SELECT id FROM users WHERE email LIKE '%@pick4me.demo')
        )
    ''')
    cursor.execute('''
        DELETE FROM orders WHERE customer_id IN (SELECT id FROM users WHERE email LIKE '%@pick4me.demo')
        OR shopper_id IN (SELECT id FROM users WHERE email LIKE '%@pick4me.demo')
    ''')
    cursor.execute('''
        DELETE FROM requests WHERE customer_id IN (SELECT id FROM users WHERE email LIKE '%@pick4me.demo')
        OR shopper_id IN (SELECT id FROM users WHERE email LIKE '%@pick4me.demo')
    ''')
    cursor.execute("DELETE FROM users WHERE email LIKE '%@pick4me.demo'")

    # Ensure Abhishek's Admin Account is permanently configured and active
    cursor.execute("SELECT id FROM users WHERE email = 'abhishekkanadje7@gmail.com'")
    existing_admin = cursor.fetchone()
    if not existing_admin:
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
            UPDATE users
            SET password_hash = ?, role = 'admin'
            WHERE email = 'abhishekkanadje7@gmail.com'
        ''', (generate_password_hash('Abhi*2007', method='pbkdf2:sha256'),))

    conn.commit()
    conn.close()
