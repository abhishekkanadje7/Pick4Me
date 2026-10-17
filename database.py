import sqlite3
import os
import random
import re
from werkzeug.security import generate_password_hash

DATABASE_URL = os.environ.get('DATABASE_URL')
DATABASE_NAME = os.environ.get('DATABASE_PATH', os.path.join(os.path.dirname(__file__), 'pick4me.db'))

# Optional PostgreSQL support via psycopg2
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

        self._cursor.execute(sql_pg, params)

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
        return self._conn.commit()

    def rollback(self):
        return self._conn.rollback()

    def close(self):
        return self._conn.close()


def get_db_connection():
    if DATABASE_URL and PSYCOPG2_AVAILABLE:
        url = DATABASE_URL
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        pg_conn = psycopg2.connect(url)
        return PostgresConnectionWrapper(pg_conn)
    else:
        conn = sqlite3.connect(DATABASE_NAME)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    is_postgres = bool(DATABASE_URL and PSYCOPG2_AVAILABLE)

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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES users (id),
            FOREIGN KEY (commuter_id) REFERENCES users (id),
            FOREIGN KEY (shop_id) REFERENCES shops (id)
        )
    '''))

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

    # 8. Check if sample demonstration data is needed
    cursor.execute("SELECT COUNT(*) FROM shops")
    shop_count_row = cursor.fetchone()
    shop_count = shop_count_row[0] if shop_count_row else 0
    if shop_count == 0:
        seed_demo_data(conn)

    conn.close()


def seed_demo_data(conn):
    """Populates realistic campus shops, products, and demonstration orders for evaluation/presentation."""
    cursor = conn.cursor()
    pwd_hash = generate_password_hash('Demo*1234', method='pbkdf2:sha256')

    # 1. Sample Shoppers / Merchants
    sample_shoppers = [
        ('Ramesh Xerox & Stationery', 'ramesh.xerox@pick4me.campus', '+91 98221 44556', 'Campus Library Arcade, Stall #3'),
        ('Chef Anand Canteen', 'anand.canteen@pick4me.campus', '+91 98222 55667', 'Main Food Court, Central Block'),
        ('NextGen Campus Tech', 'nextgen.tech@pick4me.campus', '+91 98223 66778', 'Activity Center, Shop #12'),
        ('Sanjivani Medical & First Aid', 'sanjivani.med@pick4me.campus', '+91 98224 77889', 'Hostel Gate 2 Commercial Wing'),
        ('QuickMart Campus Superette', 'quickmart.campus@pick4me.campus', '+91 98225 88990', 'Hostel Block B Common Hub')
    ]

    shopper_ids = []
    for name, email, phone, loc in sample_shoppers:
        cursor.execute("SELECT id FROM users WHERE LOWER(email) = LOWER(?)", (email,))
        row = cursor.fetchone()
        if not row:
            cursor.execute('''
                INSERT INTO users (name, email, phone, password_hash, role, location, upi_id, is_verified, wallet_balance)
                VALUES (?, ?, ?, ?, 'shopper', ?, '7387157739@upi', 1, 450.0)
            ''', (name, email, phone, pwd_hash, loc))
            s_id = cursor.lastrowid
            if not s_id:
                cursor.execute("SELECT id FROM users WHERE LOWER(email) = LOWER(?)", (email,))
                s_id = cursor.fetchone()[0]
        else:
            s_id = row['id'] if hasattr(row, 'keys') else row[0]
        shopper_ids.append(s_id)

    # 2. Sample Commuter
    commuter_email = 'rohit.commuter@pick4me.campus'
    cursor.execute("SELECT id FROM users WHERE LOWER(email) = LOWER(?)", (commuter_email,))
    c_row = cursor.fetchone()
    if not c_row:
        cursor.execute('''
            INSERT INTO users (name, email, phone, password_hash, role, location, upi_id, is_verified, wallet_balance)
            VALUES ('Rohit Sharma (Daily Commuter)', ?, '+91 98901 23456', ?, 'customer', 'Boys Hostel D, Room 304', '7387157739@upi', 1, 280.0)
        ''', (commuter_email, pwd_hash))
        c_res = cursor.lastrowid
        if not c_res:
            cursor.execute("SELECT id FROM users WHERE LOWER(email) = LOWER(?)", (commuter_email,))
            c_res = cursor.fetchone()[0]
        commuter_id = c_res
    else:
        commuter_id = c_row['id'] if hasattr(c_row, 'keys') else c_row[0]

    # 3. Create 5 Campus Shops
    shops_data = [
        (shopper_ids[0], 'Campus Xerox & Stationery Hub', 'Stationery', 'Opposite Central Library, Ground Floor', 'Library Fountain', '+91 98221 44556', 'Official student printing center: assignment prints, engineering drawing tools, hardbound project records, spiral books, and stationery essentials.'),
        (shopper_ids[1], 'Campus Central Food Court & Canteen', 'Food & Beverages', 'Main Student Canteen, Food Plaza', 'Clock Tower Lawn', '+91 98222 55667', 'Fresh cooked campus favorites: hot meals, cheesy sandwiches, dosas, fresh fruit juices, and evening tea/snacks.'),
        (shopper_ids[2], 'NextGen Tech & Electronics Repairs', 'Electronics', 'Student Activity Center, Stall #12', 'SAC Auditorium Gate', '+91 98223 66778', 'Fast cables, OTG drives, ergonomic mice, laptop accessories, earphones, and quick tech peripherals.'),
        (shopper_ids[3], 'Sanjivani Campus Pharmacy & First Aid', 'Medicines & Pharmacy', 'Commercial Complex, Hostel Gate 2', 'Medical Dispensary Annex', '+91 98224 77889', '24/7 OTC wellness essentials: first aid kits, instant pain sprays, electrolyte hydration, vitamins, and hygiene care.'),
        (shopper_ids[4], 'QuickMart Daily Essentials & Snacks', 'Groceries & Essentials', 'Hostel Block B Amenities Hub', 'Hostel Common Room', '+91 98225 88990', 'Hostel daily essentials: instant noodles, laundry detergent, soaps, dry fruits, packaged drinking water, and night study snacks.')
    ]

    shop_ids = []
    for s in shops_data:
        cursor.execute("SELECT id FROM shops WHERE shop_name = ?", (s[1],))
        s_row = cursor.fetchone()
        if not s_row:
            cursor.execute('''
                INSERT INTO shops (owner_id, shop_name, category, address, landmark, phone, description, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)
            ''', s)
            sh_res = cursor.lastrowid
            if not sh_res:
                cursor.execute("SELECT id FROM shops WHERE shop_name = ?", (s[1],))
                sh_res = cursor.fetchone()[0]
            sh_id = sh_res
        else:
            sh_id = s_row['id'] if hasattr(s_row, 'keys') else s_row[0]
        shop_ids.append(sh_id)

    # 4. Products for each Shop
    products_data = [
        # Stationery
        (shop_ids[0], 'Assignment Spiral Notebook (Pack of 3, 200 Pages)', 'Stationery', 160.0, 'High quality smooth 70 GSM ruled pages ideal for lecture notes & assignments.'),
        (shop_ids[0], 'Engineering Graphics Drawing Kit (T-Scale + Clips + Sheet Holder)', 'Stationery', 185.0, 'Mandatory first year engineering graphics tools set with heavy-duty clips.'),
        (shop_ids[0], 'Micro-Tip Technical Black & Blue Gel Pens (Box of 10)', 'Stationery', 85.0, 'Waterproof quick-dry pens approved for university semester exams.'),
        (shop_ids[0], 'Hardbound Lab Record & Practical Project File', 'Stationery', 65.0, 'Standard university embossed hard cover practical record submission folder.'),
        (shop_ids[0], 'Laser Color Printout & Spiral Binding Voucher (30 Pages)', 'Stationery', 50.0, 'Instant document printing voucher with thick protective transparent binding sheet.'),
        (shop_ids[0], 'Sticky Notes & Colorful Bookmark Page Flags Combo', 'Stationery', 45.0, 'Multi-colored neon self-adhesive memo pads for textbook reference indexing.'),

        # Food & Beverages
        (shop_ids[1], 'Grilled Cheesy Paneer Sandwich + Chilled Cold Coffee Combo', 'Food & Beverages', 99.0, 'Crispy spiced paneer loaded toast with creamy thick cocoa cold coffee.'),
        (shop_ids[1], 'Crispy Hakka Noodles with Veg Manchurian Gravy Bowl', 'Food & Beverages', 85.0, 'Steaming hot street-style wok tossed noodles served with crunchy Manchurian balls.'),
        (shop_ids[1], 'South Indian Butter Masala Dosa + Sambar & Coconut Chutney', 'Food & Beverages', 55.0, 'Crispy golden crepe filled with potato masala, served with fresh coconut dip.'),
        (shop_ids[1], 'Double Egg Masala Kathi Roll with Mint Sauce', 'Food & Beverages', 75.0, 'Flaky paratha wrapped with double masala eggs, shredded onions & chatpata chutney.'),
        (shop_ids[1], 'Fresh Mosambi / Orange Fruit Juice (Cold, 350ml)', 'Food & Beverages', 40.0, '100% natural pulpy vitamin C citrus juice extracted live on order.'),
        (shop_ids[1], 'Desi Ginger Chai + 2 Crispy Punjabi Samosas Combo', 'Food & Beverages', 35.0, 'Hot aromatic kadak chai with crispy spiced aloo samosas.'),

        # Electronics
        (shop_ids[2], '65W Fast-Charging Braided Type-C Cable (1.5 Meter)', 'Electronics', 199.0, 'Durable nylon-braided cable supporting fast charging and 480Mbps data sync.'),
        (shop_ids[2], 'Silent Click Ergonomic 2.4GHz Wireless Optical Mouse', 'Electronics', 349.0, 'Ultra-quiet clicks perfect for library study and late night hostel coding sessions.'),
        (shop_ids[2], 'SanDisk 64GB Dual USB 3.2 OTG Metal Flash Drive', 'Electronics', 499.0, 'Plug & play pen drive with Type-C and USB-A plugs for easy mobile-to-laptop file sharing.'),
        (shop_ids[2], 'High-Bass In-Ear Wired Earphones with HD Microphone (3.5mm)', 'Electronics', 179.0, 'Tangle-free rubber cable with crisp sound and noise-cancelling in-line mic.'),
        (shop_ids[2], 'Silicon Universal Laptop Keyboard Protector Shield', 'Electronics', 89.0, 'Washable ultra-thin waterproof skin preventing dust, crumbs, and liquid spills.'),
        (shop_ids[2], '4-Port High Speed USB Hub with Individual LED Power Switches', 'Electronics', 249.0, 'Expands one laptop port into 4 powered ports for pendrive, mouse, and keyboard.'),

        # Medicines & Pharmacy
        (shop_ids[3], 'Volini / Moov Instant Pain Relief Spray (55g Aerosol)', 'Medicines & Pharmacy', 120.0, 'Quick-absorbing deep penetrating spray for muscle stiffness and sports sprains.'),
        (shop_ids[3], 'Electral / Enerzal Energy Hydration Sachets (Pack of 5)', 'Medicines & Pharmacy', 80.0, 'WHO recommended formula for restoring essential electrolytes during weakness & exams.'),
        (shop_ids[3], 'Waterproof Antiseptic Band-Aid Strips (Box of 30)', 'Medicines & Pharmacy', 60.0, 'Sterile medical strips with antiseptic pad for cuts, scrapes, and blisters.'),
        (shop_ids[3], 'D-Cold Total & Paracetamol Night Care Kit (Doctor Approved)', 'Medicines & Pharmacy', 45.0, 'Quick soothing relief from campus weather change, fever, runny nose & headaches.'),
        (shop_ids[3], 'Instant Pocket Hand Sanitizer Spray (70% Ethyl Alcohol, 50ml)', 'Medicines & Pharmacy', 35.0, 'Kills 99.9% germs without water; fits easily in student pocket or backpack.'),
        (shop_ids[3], 'Digital Fever Thermometer with LCD Display & Auto-Buzzer', 'Medicines & Pharmacy', 140.0, 'Fast 60-second oral/underarm temperature reading with memory recall.'),

        # Daily Essentials
        (shop_ids[4], 'Roasted California Almonds & Cashews Energy Mix (150g)', 'Groceries & Essentials', 149.0, 'Nutrient-rich healthy brain snack pouch for late-night exams and study sessions.'),
        (shop_ids[4], 'Instant Masala Noodles Family Pack (6-in-1 Value Pack)', 'Groceries & Essentials', 78.0, 'Classic 2-minute snack pack, an absolute hostel room staple.'),
        (shop_ids[4], 'Hostel Toiletries & Hygiene Kit (Soap + Shampoo + Toothpaste)', 'Groceries & Essentials', 95.0, 'Complete personal grooming trio including Dettol soap, shampoo sachet strip, and paste.'),
        (shop_ids[4], 'Packaged Natural Mineral Drinking Water (1L Pack of 2 Bottles)', 'Groceries & Essentials', 30.0, 'Bisleri / Kinley sealed hygienic bottled drinking water.'),
        (shop_ids[4], 'Chocolate Crunchy Peanut Butter Jar (350g, High Protein)', 'Groceries & Essentials', 139.0, 'Rich protein bread spread perfect for gym enthusiasts and quick hostel breakfasts.'),
        (shop_ids[4], 'Surf Excel Easy Wash Detergent Powder (500g Pouch)', 'Groceries & Essentials', 70.0, 'Quick foaming fabric washing powder for easy hostel clothes washing.')
    ]

    for p in products_data:
        cursor.execute("SELECT id FROM products WHERE shop_id = ? AND name = ?", (p[0], p[1]))
        if not cursor.fetchone():
            cursor.execute('''
                INSERT INTO products (shop_id, name, category, price, description, in_stock)
                VALUES (?, ?, ?, ?, ?, 1)
            ''', p)

    # 5. Sample Live Orders to demonstrate Commuter & Escrow workflow
    cursor.execute("SELECT COUNT(*) FROM orders")
    order_count_row = cursor.fetchone()
    order_count = order_count_row[0] if order_count_row else 0
    if order_count == 0:
        # Get admin user ID for customer
        cursor.execute("SELECT id FROM users WHERE email = 'abhishekkanadje7@gmail.com'")
        admin_row = cursor.fetchone()
        admin_id = admin_row[0] if admin_row else 1

        # Order 1: Completed Delivery
        cursor.execute('''
            INSERT INTO orders (
                order_type, customer_id, commuter_id, shop_id, items_summary,
                product_amount, delivery_fee, total_amount, distance_tier, distance_km,
                is_urgent, target_duration_mins, actual_duration_mins, speed_bonus,
                payment_status, shop_payment_status, delivery_payment_status,
                pickup_otp, delivery_otp, delivery_address, phone, status
            ) VALUES (
                'shop_order', ?, ?, ?, 'Assignment Spiral Notebook (Pack of 3) x 1, Pen Box x 1',
                245.0, 35.0, 280.0, 'near_gate', 1.8,
                0, 35, 24, 10.0,
                'Fully_Settled', 'Released_To_Shop', 'Released_To_Commuter',
                '4219', '8834', 'Hostel Block C, Room 214', '+91 73871 57739', 'Completed'
            )
        ''', (admin_id, commuter_id, shop_ids[0]))

        # Order 2: Available Open Delivery for Commuters to Accept on /deliveries!
        cursor.execute('''
            INSERT INTO orders (
                order_type, customer_id, shop_id, items_summary,
                product_amount, delivery_fee, total_amount, distance_tier, distance_km,
                is_urgent, target_duration_mins,
                payment_status, pickup_otp, delivery_otp, delivery_address, phone, instructions, status
            ) VALUES (
                'shop_order', ?, ?, 'Grilled Cheesy Paneer Sandwich Combo x 1',
                99.0, 35.0, 134.0, 'within_campus', 0.8,
                1, 20,
                'Escrow_Held', '6172', '9045', 'Library Study Hall 2, Desk 14', '+91 98221 44556', 'Please deliver quickly before seminar starts! Extra surge tip added.', 'Paid_Pending_Commuter'
            )
        ''', (admin_id, shop_ids[1]))

        # Order 3: In Progress Delivery
        cursor.execute('''
            INSERT INTO orders (
                order_type, customer_id, commuter_id, shop_id, items_summary,
                product_amount, delivery_fee, total_amount, distance_tier, distance_km,
                is_urgent, target_duration_mins,
                payment_status, pickup_otp, delivery_otp, delivery_address, phone, status
            ) VALUES (
                'shop_order', ?, ?, ?, '65W Fast-Charging Braided Type-C Cable x 1',
                199.0, 25.0, 224.0, 'within_campus', 0.9,
                0, 25,
                'Escrow_Held', '1823', '7491', 'Mechanical Dept Lab 4', '+91 98901 23456', 'Picked_Up_From_Shop'
            )
        ''', (admin_id, commuter_id, shop_ids[2]))

    conn.commit()


def generate_otp():
    """Generates a secure 4-digit handover OTP."""
    return str(random.randint(1000, 9999))
