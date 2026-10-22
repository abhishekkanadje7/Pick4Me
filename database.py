"""
========================================================================================
  PICK4ME DATABASE MODULE (PostgreSQL Neon + SQLite Dual Engine)
========================================================================================
  Architecture:
  1. Cloud / Production (Render):
     - Uses Neon Serverless PostgreSQL via DATABASE_URL environment variable.
     - Automatically adapts schema (SERIAL PRIMARY KEY, %s parameter binding, RETURNING id).
  2. Local Offline Development:
     - Uses local SQLite database (pick4me.db).
  3. Resilience:
     - Automatically falls back to SQLite if PostgreSQL connection fails or times out.
     - Auto-recovers from failed transactions with connection rollback.
========================================================================================
"""
import sqlite3
import os
import random
import re
from werkzeug.security import generate_password_hash

# Database Configuration (Neon PostgreSQL on Cloud, SQLite for Local)
DATABASE_URL = os.environ.get('DATABASE_URL')
DEFAULT_DB = os.path.join(os.path.dirname(__file__), 'pick4me.db')
DATABASE_NAME = os.environ.get('DATABASE_PATH', DEFAULT_DB)

# Optional PostgreSQL driver support via psycopg2
try:
    import psycopg2
    import psycopg2.extras
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False


class PostgresCursorWrapper:
    def __init__(self, pg_cursor):
        self._cursor = pg_cursor
        self.lastrowid = None

    def execute(self, sql, params=None):
        if params is None:
            params = ()
        
        # Replace ? placeholder with %s for PostgreSQL
        sql_pg = sql.replace('?', '%s')
        
        # In PostgreSQL, ignore SQLite PRAGMA
        if sql_pg.strip().upper().startswith('PRAGMA'):
            return self

        # Check if INSERT without RETURNING
        is_insert = bool(re.match(r'^\s*INSERT\s+INTO\s+', sql_pg, re.IGNORECASE))
        has_returning = bool(re.search(r'\bRETURNING\b', sql_pg, re.IGNORECASE))
        
        appended_returning = False
        if is_insert and not has_returning:
            sql_pg = sql_pg.rstrip('; \t\r\n') + ' RETURNING id;'
            appended_returning = True

        try:
            self._cursor.execute(sql_pg, params)
        except Exception as e:
            try:
                self._cursor.connection.rollback()
            except Exception:
                pass
            raise e

        if appended_returning:
            try:
                res = self._cursor.fetchone()
                if res:
                    self.lastrowid = res[0]
            except Exception:
                self.lastrowid = None
        
        return self

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    def fetchmany(self, size=None):
        return self._cursor.fetchmany(size) if size else self._cursor.fetchmany()

    @property
    def description(self):
        return self._cursor.description

    @property
    def rowcount(self):
        return self._cursor.rowcount

    def close(self):
        return self._cursor.close()

    def __iter__(self):
        return iter(self._cursor)


class PostgresConnectionWrapper:
    def __init__(self, pg_conn):
        self._conn = pg_conn
        self.row_factory = None  # Compatible with conn.row_factory = sqlite3.Row

    def cursor(self):
        cur = self._conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        return PostgresCursorWrapper(cur)

    def execute(self, sql, params=None):
        if sql.strip().upper().startswith('PRAGMA'):
            return None
        cur = self.cursor()
        cur.execute(sql, params)
        return cur

    def commit(self):
        try:
            return self._conn.commit()
        except Exception:
            try:
                self._conn.rollback()
            except Exception:
                pass

    def rollback(self):
        try:
            return self._conn.rollback()
        except Exception:
            pass

    def close(self):
        try:
            return self._conn.close()
        except Exception:
            pass


def get_db_connection():
    if DATABASE_URL and PSYCOPG2_AVAILABLE:
        url = DATABASE_URL
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        try:
            pg_conn = psycopg2.connect(url, connect_timeout=10)
            return PostgresConnectionWrapper(pg_conn)
        except Exception as e:
            print(f"[Pick4Me DB Warning] PostgreSQL connection failed: {e}. Falling back to SQLite.")

    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    try:
        conn = get_db_connection()
    except Exception as e:
        print(f"[Pick4Me DB Warning] Could not open database connection in init_db: {e}")
        return

    cursor = conn.cursor()
    is_postgres = hasattr(conn, '_conn')

    def adapt_schema(sql):
        if is_postgres:
            return sql.replace('INTEGER PRIMARY KEY AUTOINCREMENT', 'SERIAL PRIMARY KEY')
        return sql

    # 1. Users Table
    cursor.execute(adapt_schema('''
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
    '''))

    # 2. Shops Table (Managed by Shoppers/Merchants)
    cursor.execute(adapt_schema('''
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
    '''))

    # 3. Products Table
    cursor.execute(adapt_schema('''
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
    '''))

    # 4. Cart Items Table
    cursor.execute(adapt_schema('''
        CREATE TABLE IF NOT EXISTS cart_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
        )
    '''))

    # 5. Orders Table: 3-Party Logistics (Customer A + Customer B Commuter + Shopper Store + Admin Escrow)
    cursor.execute(adapt_schema('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_type TEXT NOT NULL DEFAULT 'shop_order',
            customer_id INTEGER NOT NULL,
            commuter_id INTEGER DEFAULT NULL,
            shop_id INTEGER DEFAULT NULL,
            items_summary TEXT NOT NULL,
            product_amount REAL NOT NULL,
            delivery_fee REAL NOT NULL,
            total_amount REAL NOT NULL,
            distance_tier TEXT NOT NULL DEFAULT 'within_campus',
            distance_km REAL NOT NULL DEFAULT 0.8,
            is_urgent INTEGER NOT NULL DEFAULT 0,
            target_duration_mins INTEGER NOT NULL DEFAULT 30,
            accepted_at TIMESTAMP DEFAULT NULL,
            picked_up_at TIMESTAMP DEFAULT NULL,
            delivered_at TIMESTAMP DEFAULT NULL,
            actual_duration_mins INTEGER DEFAULT NULL,
            speed_bonus REAL NOT NULL DEFAULT 0.0,
            delay_penalty REAL NOT NULL DEFAULT 0.0,
            final_payout REAL DEFAULT NULL,
            payment_status TEXT NOT NULL DEFAULT 'Pending_Payment',
            shop_payment_status TEXT NOT NULL DEFAULT 'Pending',
            delivery_payment_status TEXT NOT NULL DEFAULT 'Pending',
            pickup_otp TEXT NOT NULL,
            delivery_otp TEXT NOT NULL,
            delivery_address TEXT NOT NULL,
            phone TEXT NOT NULL,
            instructions TEXT DEFAULT '',
            status TEXT NOT NULL DEFAULT 'Paid_Pending_Commuter',
            feedback_rating INTEGER DEFAULT NULL,
            feedback_comment TEXT DEFAULT '',
            feedback_submitted_at TIMESTAMP DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES users (id),
            FOREIGN KEY (commuter_id) REFERENCES users (id),
            FOREIGN KEY (shop_id) REFERENCES shops (id)
        )
    '''))

    # Safe schema migration for ALL columns across users, shops, products, and orders
    all_table_migrations = [
        # Users table migrations
        ('users', 'upi_id', "TEXT DEFAULT '7387157739@upi'"),
        ('users', 'qr_code', "TEXT DEFAULT 'upi_qr.png'"),
        ('users', 'is_verified', "INTEGER DEFAULT 1"),
        ('users', 'wallet_balance', "REAL DEFAULT 0.0"),
        ('users', 'id_proof', "TEXT DEFAULT 'Verified Campus Member'"),

        # Shops table migrations
        ('shops', 'landmark', "TEXT DEFAULT ''"),
        ('shops', 'description', "TEXT DEFAULT ''"),
        ('shops', 'image', "TEXT DEFAULT ''"),
        ('shops', 'is_active', "INTEGER DEFAULT 1"),

        # Products table migrations
        ('products', 'description', "TEXT DEFAULT ''"),
        ('products', 'image', "TEXT DEFAULT ''"),
        ('products', 'in_stock', "INTEGER DEFAULT 1"),

        # Orders table migrations (Ensures all 3-party logistics and escrow columns exist)
        ('orders', 'order_type', "TEXT DEFAULT 'shop_order'"),
        ('orders', 'customer_id', "INTEGER"),
        ('orders', 'commuter_id', "INTEGER DEFAULT NULL"),
        ('orders', 'shop_id', "INTEGER DEFAULT NULL"),
        ('orders', 'items_summary', "TEXT DEFAULT 'Campus Delivery'"),
        ('orders', 'product_amount', "REAL DEFAULT 0.0"),
        ('orders', 'delivery_fee', "REAL DEFAULT 20.0"),
        ('orders', 'total_amount', "REAL DEFAULT 20.0"),
        ('orders', 'distance_tier', "TEXT DEFAULT 'within_campus'"),
        ('orders', 'distance_km', "REAL DEFAULT 0.8"),
        ('orders', 'is_urgent', "INTEGER DEFAULT 0"),
        ('orders', 'target_duration_mins', "INTEGER DEFAULT 30"),
        ('orders', 'accepted_at', "TIMESTAMP DEFAULT NULL"),
        ('orders', 'picked_up_at', "TIMESTAMP DEFAULT NULL"),
        ('orders', 'delivered_at', "TIMESTAMP DEFAULT NULL"),
        ('orders', 'actual_duration_mins', "INTEGER DEFAULT NULL"),
        ('orders', 'speed_bonus', "REAL DEFAULT 0.0"),
        ('orders', 'delay_penalty', "REAL DEFAULT 0.0"),
        ('orders', 'final_payout', "REAL DEFAULT NULL"),
        ('orders', 'payment_status', "TEXT DEFAULT 'Pending_Payment'"),
        ('orders', 'shop_payment_status', "TEXT DEFAULT 'Pending'"),
        ('orders', 'delivery_payment_status', "TEXT DEFAULT 'Pending'"),
        ('orders', 'pickup_otp', "TEXT DEFAULT '1234'"),
        ('orders', 'delivery_otp', "TEXT DEFAULT '5678'"),
        ('orders', 'delivery_address', "TEXT DEFAULT 'Campus'"),
        ('orders', 'phone', "TEXT DEFAULT ''"),
        ('orders', 'instructions', "TEXT DEFAULT ''"),
        ('orders', 'status', "TEXT DEFAULT 'Paid_Pending_Commuter'"),
        ('orders', 'feedback_rating', "INTEGER DEFAULT NULL"),
        ('orders', 'feedback_comment', "TEXT DEFAULT ''"),
        ('orders', 'feedback_submitted_at', "TIMESTAMP DEFAULT NULL"),
        ('orders', 'created_at', "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ('orders', 'updated_at', "TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    ]

    for table, col, col_type in all_table_migrations:
        try:
            if is_postgres:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col} {col_type}")
                conn.commit()
            else:
                cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col} {col_type}")
                conn.commit()
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass

    # For PostgreSQL: Drop NOT NULL on legacy columns if they exist from early schemas
    if is_postgres:
        for legacy_col in ['request_id', 'shopper_id', 'reward', 'shop_id', 'commuter_id', 'pickup_otp', 'delivery_otp', 'items_summary']:
            try:
                cursor.execute(f"ALTER TABLE orders ALTER COLUMN {legacy_col} DROP NOT NULL")
                conn.commit()
            except Exception:
                try:
                    conn.rollback()
                except Exception:
                    pass

    # 6. Wallet Transactions Table
    cursor.execute(adapt_schema('''
        CREATE TABLE IF NOT EXISTS wallet_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            order_id INTEGER DEFAULT NULL,
            amount REAL NOT NULL,
            type TEXT NOT NULL,
            description TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    '''))

    # 7. Ensure Abhishek Kanadje's Verified Admin is configured
    try:
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
    except Exception as e:
        print(f"[Pick4Me Admin Setup Notice] {e}")
        try:
            conn.rollback()
        except Exception:
            pass

    try:
        conn.commit()
    except Exception:
        pass
    try:
        conn.close()
    except Exception:
        pass


def generate_otp():
    """Generates a secure 4-digit handover OTP."""
    return str(random.randint(1000, 9999))

