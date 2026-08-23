import os
import uuid
from functools import wraps
from datetime import datetime
from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, session, abort, jsonify
)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from database import get_db_connection, init_db, generate_otp

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'pick4me-super-secret-key-college-demo-2026')
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max upload
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'svg'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize database schema and seeds on startup
with app.app_context():
    init_db()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ==========================================
# AUTHENTICATION HELPERS & DECORATORS
# ==========================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def customer_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.', 'warning')
            return redirect(url_for('login_customer'))
        if session.get('user_role') not in ('customer', 'admin'):
            flash('Access restricted to Customer accounts.', 'danger')
            return redirect(url_for('shopper_dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def shopper_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.', 'warning')
            return redirect(url_for('login_shopper'))
        if session.get('user_role') not in ('shopper', 'admin'):
            flash('Access restricted to Shopper & Merchant accounts.', 'danger')
            return redirect(url_for('customer_dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in as an administrator.', 'warning')
            return redirect(url_for('login'))
        if session.get('user_role') != 'admin':
            flash('Admin privileges required to access this area.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.context_processor
def inject_globals():
    """Inject user profile, cart item count, and current year into all templates."""
    user = None
    cart_count = 0
    user_shop = None
    if 'user_id' in session:
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        
        # Calculate cart items count
        cart_row = conn.execute('SELECT COALESCE(SUM(quantity), 0) FROM cart_items WHERE user_id = ?', (session['user_id'],)).fetchone()
        cart_count = cart_row[0] if cart_row else 0

        # Check if shopper has a registered shop
        if user and user['role'] in ('shopper', 'admin'):
            user_shop = conn.execute('SELECT * FROM shops WHERE owner_id = ?', (session['user_id'],)).fetchone()

        conn.close()

    return {
        'current_user': user,
        'cart_count': cart_count,
        'user_shop': user_shop,
        'current_year': datetime.now().year
    }

# ==========================================
# PUBLIC MARKETPLACE & STOREFRONT ROUTES
# ==========================================

@app.route('/')
def index():
    conn = get_db_connection()
    
    # Featured shops
    shops = conn.execute('''
        SELECT s.*, u.name as owner_name, u.is_verified as owner_verified,
               (SELECT COUNT(*) FROM products p WHERE p.shop_id = s.id) as product_count
        FROM shops s
        JOIN users u ON s.owner_id = u.id
        WHERE s.is_active = 1
        ORDER BY s.created_at DESC
        LIMIT 6
    ''').fetchall()

    # Popular products
    featured_products = conn.execute('''
        SELECT p.*, s.shop_name, s.address as shop_address
        FROM products p
        JOIN shops s ON p.shop_id = s.id
        WHERE p.in_stock = 1
        ORDER BY p.created_at DESC
        LIMIT 8
    ''').fetchall()

    # Live available peer requests (Advance Escrow Paid)
    available_deliveries = conn.execute('''
        SELECT o.*, u.name as customer_name, u.location as customer_area
        FROM orders o
        JOIN users u ON o.customer_id = u.id
        WHERE o.status = 'Paid_Pending_Shopper'
        ORDER BY o.created_at DESC
        LIMIT 4
    ''').fetchall()

    # Metrics
    total_shops = conn.execute("SELECT COUNT(*) FROM shops WHERE is_active = 1").fetchone()[0]
    total_products = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    completed_orders = conn.execute("SELECT COUNT(*) FROM orders WHERE status = 'Completed'").fetchone()[0]

    conn.close()

    return render_template(
        'index.html',
        shops=shops,
        featured_products=featured_products,
        available_deliveries=available_deliveries,
        stats={
            'shops': total_shops,
            'products': total_products,
            'completed': completed_orders
        }
    )

@app.route('/shops')
def shops_directory():
    category = request.args.get('category', 'all')
    search_query = request.args.get('q', '').strip()

    conn = get_db_connection()
    query = '''
        SELECT s.*, u.name as owner_name, u.is_verified as owner_verified,
               (SELECT COUNT(*) FROM products p WHERE p.shop_id = s.id) as product_count
        FROM shops s
        JOIN users u ON s.owner_id = u.id
        WHERE s.is_active = 1
    '''
    params = []

    if category != 'all':
        query += ' AND s.category = ?'
        params.append(category)

    if search_query:
        query += ' AND (s.shop_name LIKE ? OR s.address LIKE ? OR s.description LIKE ?)'
        wildcard = f"%{search_query}%"
        params.extend([wildcard, wildcard, wildcard])

    query += ' ORDER BY s.created_at DESC'
    shops = conn.execute(query, params).fetchall()

    categories = conn.execute('SELECT DISTINCT category FROM shops WHERE is_active = 1').fetchall()
    conn.close()

    return render_template(
        'shops.html',
        shops=shops,
        categories=[c['category'] for c in categories if c['category']],
        current_category=category,
        current_query=search_query
    )

@app.route('/shops/<int:id>')
def shop_detail(id):
    conn = get_db_connection()
    shop = conn.execute('''
        SELECT s.*, u.name as owner_name, u.phone as owner_phone, u.is_verified as owner_verified
        FROM shops s
        JOIN users u ON s.owner_id = u.id
        WHERE s.id = ?
    ''', (id,)).fetchone()

    if not shop:
        conn.close()
        abort(404)

    products = conn.execute('SELECT * FROM products WHERE shop_id = ? ORDER BY in_stock DESC, created_at DESC', (id,)).fetchall()
    conn.close()

    return render_template('shop_detail.html', shop=shop, products=products)

@app.route('/products')
def products_catalog():
    category = request.args.get('category', 'all')
    search_query = request.args.get('q', '').strip()
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)

    conn = get_db_connection()
    query = '''
        SELECT p.*, s.shop_name, s.address as shop_address, s.id as shop_id
        FROM products p
        JOIN shops s ON p.shop_id = s.id
        WHERE s.is_active = 1
    '''
    params = []

    if category != 'all':
        query += ' AND p.category = ?'
        params.append(category)

    if search_query:
        query += ' AND (p.name LIKE ? OR p.description LIKE ? OR s.shop_name LIKE ?)'
        wildcard = f"%{search_query}%"
        params.extend([wildcard, wildcard, wildcard])

    if min_price is not None:
        query += ' AND p.price >= ?'
        params.append(min_price)

    if max_price is not None:
        query += ' AND p.price <= ?'
        params.append(max_price)

    query += ' ORDER BY p.in_stock DESC, p.created_at DESC'
    products = conn.execute(query, params).fetchall()

    categories = conn.execute('SELECT DISTINCT category FROM products').fetchall()
    conn.close()

    return render_template(
        'products.html',
        products=products,
        categories=[c['category'] for c in categories if c['category']],
        current_category=category,
        current_query=search_query
    )

# ==========================================
# SHOPPING CART & CHECKOUT WITH ADVANCE ESCROW
# ==========================================

@app.route('/cart')
@customer_required
def view_cart():
    user_id = session['user_id']
    conn = get_db_connection()
    items = conn.execute('''
        SELECT c.*, p.name as product_name, p.price, p.image as product_image, p.in_stock,
               s.id as shop_id, s.shop_name, s.address as shop_address
        FROM cart_items c
        JOIN products p ON c.product_id = p.id
        JOIN shops s ON p.shop_id = s.id
        WHERE c.user_id = ?
    ''', (user_id,)).fetchall()

    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()

    subtotal = sum(item['price'] * item['quantity'] for item in items)
    delivery_fee = 25.0 if items else 0.0  # Fixed peer delivery fee
    total = subtotal + delivery_fee

    return render_template(
        'cart.html',
        items=items,
        subtotal=subtotal,
        delivery_fee=delivery_fee,
        total=total,
        user=user
    )

@app.route('/cart/add', methods=['POST'])
@customer_required
def add_to_cart():
    user_id = session['user_id']
    product_id = request.form.get('product_id', type=int)
    quantity = request.form.get('quantity', 1, type=int)

    if not product_id:
        flash('Invalid product selected.', 'danger')
        return redirect(url_for('products_catalog'))

    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    if not product:
        conn.close()
        flash('Product not found.', 'danger')
        return redirect(url_for('products_catalog'))

    # Check if already in cart
    existing_item = conn.execute(
        'SELECT * FROM cart_items WHERE user_id = ? AND product_id = ?',
        (user_id, product_id)
    ).fetchone()

    if existing_item:
        conn.execute(
            'UPDATE cart_items SET quantity = quantity + ? WHERE id = ?',
            (quantity, existing_item['id'])
        )
    else:
        conn.execute(
            'INSERT INTO cart_items (user_id, product_id, quantity) VALUES (?, ?, ?)',
            (user_id, product_id, quantity)
        )

    conn.commit()
    conn.close()

    flash(f'"{product["name"]}" added to your cart!', 'success')
    return redirect(request.referrer or url_for('view_cart'))

@app.route('/cart/remove/<int:id>', methods=['POST'])
@customer_required
def remove_from_cart(id):
    user_id = session['user_id']
    conn = get_db_connection()
    conn.execute('DELETE FROM cart_items WHERE id = ? AND user_id = ?', (id, user_id))
    conn.commit()
    conn.close()
    flash('Item removed from cart.', 'info')
    return redirect(url_for('view_cart'))

@app.route('/cart/checkout', methods=['POST'])
@customer_required
def checkout_cart():
    user_id = session['user_id']
    delivery_address = request.form.get('delivery_address', '').strip()
    phone = request.form.get('phone', '').strip()
    instructions = request.form.get('instructions', '').strip()

    if not delivery_address or not phone:
        flash('Please provide delivery address and contact phone.', 'danger')
        return redirect(url_for('view_cart'))

    conn = get_db_connection()
    items = conn.execute('''
        SELECT c.*, p.name as product_name, p.price, s.id as shop_id, s.shop_name
        FROM cart_items c
        JOIN products p ON c.product_id = p.id
        JOIN shops s ON p.shop_id = s.id
        WHERE c.user_id = ?
    ''', (user_id,)).fetchall()

    if not items:
        conn.close()
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('products_catalog'))

    subtotal = sum(item['price'] * item['quantity'] for item in items)
    delivery_fee = 25.0
    total_amount = subtotal + delivery_fee
    
    # Format items summary
    items_list_str = ", ".join([f"{item['product_name']} (x{item['quantity']})" for item in items])
    shop_id = items[0]['shop_id']
    otp_code = generate_otp()

    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO orders (
            order_type, customer_id, shop_id, items_summary,
            product_amount, delivery_fee, total_amount,
            payment_status, delivery_otp, delivery_address, phone, instructions, status
        ) VALUES ('shop_order', ?, ?, ?, ?, ?, ?, 'Pending_Payment', ?, ?, ?, ?, 'Pending_Payment')
    ''', (
        user_id, shop_id, items_list_str,
        subtotal, delivery_fee, total_amount,
        otp_code, delivery_address, phone, instructions
    ))
    order_id = cursor.lastrowid

    # Clear cart after creating order
    cursor.execute('DELETE FROM cart_items WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

    flash('Order created! Please complete advance payment to broadcast order to nearby commuters.', 'info')
    return redirect(url_for('advance_payment_page', order_id=order_id))

# ==========================================
# CUSTOM PEER ERRANDS & SHOPPING REQUESTS
# ==========================================

@app.route('/requests/create', methods=['GET', 'POST'])
@customer_required
def create_custom_request():
    if request.method == 'POST':
        customer_id = session['user_id']
        product_name = request.form.get('product_name', '').strip()
        description = request.form.get('description', '').strip()
        category = request.form.get('category', 'General').strip()
        shop_name = request.form.get('shop_name', '').strip()
        shop_address = request.form.get('shop_address', '').strip()
        delivery_address = request.form.get('delivery_address', '').strip()
        phone = request.form.get('phone', '').strip()
        estimated_price = request.form.get('estimated_price', 0.0, type=float)
        delivery_fee = request.form.get('reward', 25.0, type=float)
        instructions = request.form.get('instructions', '').strip()

        if not all([product_name, category, shop_name, delivery_address, phone]):
            flash('Please fill in product, shop, and delivery details.', 'danger')
            return render_template('create_request.html', form_data=request.form)

        if estimated_price <= 0 or delivery_fee < 5:
            flash('Please enter a valid estimated price and minimum delivery reward of ₹5.', 'warning')
            return render_template('create_request.html', form_data=request.form)

        total_amount = estimated_price + delivery_fee
        otp_code = generate_otp()
        items_summary = f"{product_name} (from {shop_name})"

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO orders (
                order_type, customer_id, items_summary,
                product_amount, delivery_fee, total_amount,
                payment_status, delivery_otp, delivery_address, phone, instructions, status
            ) VALUES ('custom_request', ?, ?, ?, ?, ?, 'Pending_Payment', ?, ?, ?, ?, 'Pending_Payment')
        ''', (
            customer_id, items_summary,
            estimated_price, delivery_fee, total_amount,
            otp_code, delivery_address, phone, instructions
        ))
        order_id = cursor.lastrowid
        conn.commit()
        conn.close()

        flash('Custom request created! Complete advance escrow payment to notify nearby commuters.', 'info')
        return redirect(url_for('advance_payment_page', order_id=order_id))

    conn = get_db_connection()
    user = conn.execute('SELECT phone, location FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    conn.close()

    default_form = {
        'phone': user['phone'] if user else '',
        'delivery_address': user['location'] if user else '',
        'reward': 25.0
    }
    return render_template('create_request.html', form_data=default_form)

# ==========================================
# ADVANCE PAYMENT & ESCROW FLOW
# ==========================================

@app.route('/pay/escrow/<int:order_id>')
@customer_required
def advance_payment_page(order_id):
    customer_id = session['user_id']
    conn = get_db_connection()
    order = conn.execute('''
        SELECT o.*, s.shop_name, s.address as shop_address
        FROM orders o
        LEFT JOIN shops s ON o.shop_id = s.id
        WHERE o.id = ?
    ''', (order_id,)).fetchone()

    if not order or (order['customer_id'] != customer_id and session.get('user_role') != 'admin'):
        conn.close()
        flash('Order not found or unauthorized access.', 'danger')
        return redirect(url_for('customer_dashboard'))

    conn.close()
    return render_template('payment.html', order=order)

@app.route('/pay/escrow/<int:order_id>/confirm', methods=['POST'])
@customer_required
def confirm_advance_payment(order_id):
    customer_id = session['user_id']
    conn = get_db_connection()
    order = conn.execute('SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()

    if not order or (order['customer_id'] != customer_id and session.get('user_role') != 'admin'):
        conn.close()
        flash('Unauthorized.', 'danger')
        return redirect(url_for('customer_dashboard'))

    # Lock funds into platform Escrow and make order available on the Deliveries board
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE orders
        SET payment_status = 'Escrow_Held', status = 'Paid_Pending_Shopper', updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (order_id,))
    conn.commit()
    conn.close()

    flash('Advance payment received! Your order is now active and nearby commuters are notified.', 'success')
    return redirect(url_for('order_details', id=order_id))

# ==========================================
# ORDER TRACKING, DELIVERY MILESTONES & OTP RELEASE
# ==========================================

@app.route('/orders')
@login_required
def orders_list():
    user_id = session['user_id']
    role = session.get('user_role', 'customer')
    status_filter = request.args.get('status', 'all')

    conn = get_db_connection()
    if role == 'customer':
        query = '''
            SELECT o.*, s.shop_name, u.name as counterpart_name, u.phone as counterpart_phone
            FROM orders o
            LEFT JOIN shops s ON o.shop_id = s.id
            LEFT JOIN users u ON o.shopper_id = u.id
            WHERE o.customer_id = ?
        '''
        params = [user_id]
    elif role == 'shopper':
        query = '''
            SELECT o.*, s.shop_name, u.name as counterpart_name, u.phone as counterpart_phone
            FROM orders o
            LEFT JOIN shops s ON o.shop_id = s.id
            LEFT JOIN users u ON o.customer_id = u.id
            WHERE o.shopper_id = ?
        '''
        params = [user_id]
    else:  # admin
        query = '''
            SELECT o.*, s.shop_name, c.name as customer_name, sh.name as shopper_name, sh.name as counterpart_name
            FROM orders o
            LEFT JOIN shops s ON o.shop_id = s.id
            JOIN users c ON o.customer_id = c.id
            LEFT JOIN users sh ON o.shopper_id = sh.id
            WHERE 1=1
        '''
        params = []

    if status_filter == 'active':
        query += " AND o.status IN ('Paid_Pending_Shopper', 'Accepted', 'Purchased', 'Out for Delivery', 'Delivered')"
    elif status_filter == 'completed':
        query += " AND o.status = 'Completed'"
    elif status_filter == 'cancelled':
        query += " AND o.status = 'Cancelled'"

    query += ' ORDER BY o.updated_at DESC'
    orders = conn.execute(query, params).fetchall()
    conn.close()

    return render_template('orders.html', orders=orders, current_filter=status_filter, role=role)

@app.route('/orders/<int:id>')
@login_required
def order_details(id):
    user_id = session['user_id']
    role = session.get('user_role', 'customer')

    conn = get_db_connection()
    order = conn.execute('''
        SELECT o.*,
               c.name as customer_name, c.email as customer_email, c.location as customer_location,
               sh.name as shopper_name, sh.phone as shopper_phone, sh.email as shopper_email,
               s.shop_name, s.address as shop_address, s.phone as shop_phone
        FROM orders o
        JOIN users c ON o.customer_id = c.id
        LEFT JOIN users sh ON o.shopper_id = sh.id
        LEFT JOIN shops s ON o.shop_id = s.id
        WHERE o.id = ?
    ''', (id,)).fetchone()

    if not order:
        conn.close()
        abort(404)

    if role != 'admin' and order['customer_id'] != user_id and order['shopper_id'] != user_id:
        conn.close()
        flash('Unauthorized access to this order.', 'danger')
        return redirect(url_for('index'))

    conn.close()

    # Shopper next step determination
    next_step = None
    if order['status'] == 'Accepted':
        next_step = {'action': 'Purchased', 'label': 'Mark as Purchased (Items Picked Up)', 'class': 'btn-primary'}
    elif order['status'] == 'Purchased':
        next_step = {'action': 'Out for Delivery', 'label': 'Mark as Out for Delivery', 'class': 'btn-warning'}
    elif order['status'] == 'Out for Delivery':
        next_step = {'action': 'Delivered', 'label': 'Mark as Reached Destination', 'class': 'btn-success'}

    return render_template(
        'order_details.html',
        order=order,
        next_step=next_step,
        user_role=role,
        current_user_id=user_id
    )

@app.route('/orders/<int:id>/accept', methods=['POST'])
@shopper_required
def accept_delivery_task(id):
    shopper_id = session['user_id']
    conn = get_db_connection()

    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE id = ?", (id,))
    order = cursor.fetchone()

    if not order:
        conn.close()
        flash('Order not found.', 'danger')
        return redirect(url_for('shopper_dashboard'))

    if order['customer_id'] == shopper_id:
        conn.close()
        flash('You cannot accept your own order for delivery.', 'warning')
        return redirect(url_for('order_details', id=id))

    if order['status'] != 'Paid_Pending_Shopper':
        conn.close()
        flash('This delivery task has already been claimed by another commuter.', 'danger')
        return redirect(url_for('shopper_dashboard'))

    cursor.execute('''
        UPDATE orders
        SET status = 'Accepted', shopper_id = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ? AND status = 'Paid_Pending_Shopper'
    ''', (shopper_id, id))

    conn.commit()
    conn.close()

    flash('Delivery task accepted! Pick up the items and follow the progress milestones.', 'success')
    return redirect(url_for('order_details', id=id))

@app.route('/orders/<int:id>/update-status', methods=['POST'])
@shopper_required
def update_order_status(id):
    shopper_id = session['user_id']
    new_status = request.form.get('status', '').strip()

    conn = get_db_connection()
    order = conn.execute('SELECT * FROM orders WHERE id = ?', (id,)).fetchone()

    if not order or (order['shopper_id'] != shopper_id and session.get('user_role') != 'admin'):
        conn.close()
        flash('Unauthorized to update this order.', 'danger')
        return redirect(url_for('orders_list'))

    valid_transitions = {
        'Accepted': 'Purchased',
        'Purchased': 'Out for Delivery',
        'Out for Delivery': 'Delivered'
    }

    if order['status'] not in valid_transitions or valid_transitions[order['status']] != new_status:
        conn.close()
        flash(f'Invalid milestone transition.', 'danger')
        return redirect(url_for('order_details', id=id))

    cursor = conn.cursor()
    cursor.execute('UPDATE orders SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', (new_status, id))
    conn.commit()
    conn.close()

    flash(f'Delivery milestone updated: {new_status}', 'success')
    return redirect(url_for('order_details', id=id))

@app.route('/orders/<int:id>/verify-otp', methods=['POST'])
@shopper_required
def verify_delivery_otp(id):
    """Deliverer enters customer's 4-digit OTP upon physical handover -> Releases Escrow Payment to Deliverer's Wallet!"""
    shopper_id = session['user_id']
    entered_otp = request.form.get('delivery_otp', '').strip()

    conn = get_db_connection()
    order = conn.execute('SELECT * FROM orders WHERE id = ?', (id,)).fetchone()

    if not order or (order['shopper_id'] != shopper_id and session.get('user_role') != 'admin'):
        conn.close()
        flash('Unauthorized.', 'danger')
        return redirect(url_for('orders_list'))

    if order['status'] not in ('Out for Delivery', 'Delivered'):
        conn.close()
        flash('Order must be delivered before entering the delivery handover OTP.', 'warning')
        return redirect(url_for('order_details', id=id))

    if entered_otp != order['delivery_otp']:
        conn.close()
        flash('Incorrect Delivery OTP! Please ask the customer to read their 4-digit code.', 'danger')
        return redirect(url_for('order_details', id=id))

    # Release payment to deliverer's wallet
    payout_amount = float(order['total_amount'])
    cursor = conn.cursor()

    # 1. Update Order Status
    cursor.execute('''
        UPDATE orders
        SET status = 'Completed', payment_status = 'Released_To_Shopper', updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (id,))

    # 2. Credit Wallet Balance
    cursor.execute('''
        UPDATE users
        SET wallet_balance = wallet_balance + ?
        WHERE id = ?
    ''', (payout_amount, shopper_id))

    # 3. Record Wallet Transaction
    cursor.execute('''
        INSERT INTO wallet_transactions (user_id, order_id, amount, type, description)
        VALUES (?, ?, ?, 'credit_earnings', ?)
    ''', (shopper_id, id, payout_amount, f"Earnings & Product Payout for Order #ORD-{id}"))

    conn.commit()
    conn.close()

    flash(f'🎉 OTP Verified! ₹{payout_amount:.2f} has been automatically credited to your Wallet!', 'success')
    return redirect(url_for('wallet_dashboard'))

# ==========================================
# SHOPPER & MERCHANT DASHBOARD
# ==========================================

@app.route('/shopper/dashboard')
@shopper_required
def shopper_dashboard():
    shopper_id = session['user_id']
    conn = get_db_connection()

    # Available deliveries (Advance Escrow Paid)
    available_tasks = conn.execute('''
        SELECT o.*, u.name as customer_name, u.location as customer_area, s.shop_name, s.address as shop_address
        FROM orders o
        JOIN users u ON o.customer_id = u.id
        LEFT JOIN shops s ON o.shop_id = s.id
        WHERE o.status = 'Paid_Pending_Shopper'
        ORDER BY o.created_at DESC
    ''').fetchall()

    # Active deliveries assigned to shopper
    active_deliveries = conn.execute('''
        SELECT o.*, u.name as customer_name, u.phone as customer_phone, s.shop_name, s.address as shop_address
        FROM orders o
        JOIN users u ON o.customer_id = u.id
        LEFT JOIN shops s ON o.shop_id = s.id
        WHERE o.shopper_id = ? AND o.status IN ('Accepted', 'Purchased', 'Out for Delivery', 'Delivered')
        ORDER BY o.updated_at DESC
    ''', (shopper_id,)).fetchall()

    user = conn.execute('SELECT * FROM users WHERE id = ?', (shopper_id,)).fetchone()
    shop = conn.execute('SELECT * FROM shops WHERE owner_id = ?', (shopper_id,)).fetchone()
    products_count = conn.execute('SELECT COUNT(*) FROM products WHERE shop_id = ?', (shop['id'],)).fetchone()[0] if shop else 0

    conn.close()

    return render_template(
        'shopper_dashboard.html',
        available_tasks=available_tasks,
        active_deliveries=active_deliveries,
        user=user,
        shop=shop,
        products_count=products_count
    )

@app.route('/merchant/shop', methods=['GET', 'POST'])
@shopper_required
def merchant_shop_setup():
    user_id = session['user_id']
    conn = get_db_connection()
    shop = conn.execute('SELECT * FROM shops WHERE owner_id = ?', (user_id,)).fetchone()

    if request.method == 'POST':
        shop_name = request.form.get('shop_name', '').strip()
        category = request.form.get('category', 'General').strip()
        address = request.form.get('address', '').strip()
        landmark = request.form.get('landmark', '').strip()
        phone = request.form.get('phone', '').strip()
        description = request.form.get('description', '').strip()

        if not shop_name or not address or not phone:
            flash('Shop name, address, and phone are mandatory.', 'danger')
            return render_template('merchant_shop.html', shop=shop)

        cursor = conn.cursor()
        if shop:
            cursor.execute('''
                UPDATE shops
                SET shop_name = ?, category = ?, address = ?, landmark = ?, phone = ?, description = ?
                WHERE id = ?
            ''', (shop_name, category, address, landmark, phone, description, shop['id']))
            shop_id = shop['id']
            flash('Shop profile updated successfully!', 'success')
        else:
            cursor.execute('''
                INSERT INTO shops (owner_id, shop_name, category, address, landmark, phone, description)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, shop_name, category, address, landmark, phone, description))
            shop_id = cursor.lastrowid
            flash('Store registered on Pick4Me! You can now add products to your catalog.', 'success')

        conn.commit()
        shop = conn.execute('SELECT * FROM shops WHERE id = ?', (shop_id,)).fetchone()

    products = conn.execute('SELECT * FROM products WHERE shop_id = ? ORDER BY created_at DESC', (shop['id'],)).fetchall() if shop else []
    conn.close()

    return render_template('merchant_shop.html', shop=shop, products=products)

@app.route('/merchant/products/add', methods=['POST'])
@shopper_required
def add_product_to_shop():
    user_id = session['user_id']
    conn = get_db_connection()
    shop = conn.execute('SELECT * FROM shops WHERE owner_id = ?', (user_id,)).fetchone()

    if not shop:
        conn.close()
        flash('Please register your shop first.', 'warning')
        return redirect(url_for('merchant_shop_setup'))

    name = request.form.get('name', '').strip()
    category = request.form.get('category', shop['category']).strip()
    price = request.form.get('price', 0.0, type=float)
    description = request.form.get('description', '').strip()

    if not name or price <= 0:
        conn.close()
        flash('Please provide a valid product name and price.', 'danger')
        return redirect(url_for('merchant_shop_setup'))

    conn.execute('''
        INSERT INTO products (shop_id, name, category, price, description, in_stock)
        VALUES (?, ?, ?, ?, ?, 1)
    ''', (shop['id'], name, category, price, description))
    conn.commit()
    conn.close()

    flash(f'Product "{name}" added to your shop catalog!', 'success')
    return redirect(url_for('merchant_shop_setup'))

@app.route('/merchant/products/<int:id>/delete', methods=['POST'])
@shopper_required
def delete_product(id):
    user_id = session['user_id']
    conn = get_db_connection()
    shop = conn.execute('SELECT * FROM shops WHERE owner_id = ?', (user_id,)).fetchone()

    if shop:
        conn.execute('DELETE FROM products WHERE id = ? AND shop_id = ?', (id, shop['id']))
        conn.commit()
        flash('Product removed from catalog.', 'info')

    conn.close()
    return redirect(url_for('merchant_shop_setup'))

@app.route('/wallet')
@shopper_required
def wallet_dashboard():
    user_id = session['user_id']
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
    transactions = conn.execute('''
        SELECT * FROM wallet_transactions
        WHERE user_id = ?
        ORDER BY created_at DESC
    ''', (user_id,)).fetchall()
    conn.close()

    return render_template('wallet.html', user=user, transactions=transactions)

# ==========================================
# CUSTOMER DASHBOARD
# ==========================================

@app.route('/customer/dashboard')
@customer_required
def customer_dashboard():
    user_id = session['user_id']
    conn = get_db_connection()

    active_orders = conn.execute('''
        SELECT o.*, s.shop_name, u.name as shopper_name, u.phone as shopper_phone
        FROM orders o
        LEFT JOIN shops s ON o.shop_id = s.id
        LEFT JOIN users u ON o.shopper_id = u.id
        WHERE o.customer_id = ? AND o.status != 'Completed' AND o.status != 'Cancelled'
        ORDER BY o.updated_at DESC
    ''', (user_id,)).fetchall()

    past_orders = conn.execute('''
        SELECT o.*, s.shop_name, u.name as shopper_name
        FROM orders o
        LEFT JOIN shops s ON o.shop_id = s.id
        LEFT JOIN users u ON o.shopper_id = u.id
        WHERE o.customer_id = ? AND o.status = 'Completed'
        ORDER BY o.updated_at DESC
        LIMIT 5
    ''', (user_id,)).fetchall()

    conn.close()

    return render_template('customer_dashboard.html', active_orders=active_orders, past_orders=past_orders)

# ==========================================
# PROFILE & AUTHENTICATION
# ==========================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        role = session.get('user_role', 'customer')
        return redirect(url_for(f'{role}_dashboard' if role != 'admin' else 'admin_dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_role'] = user['role']
            session['user_email'] = user['email']

            flash(f"Welcome back, {user['name']}!", 'success')
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user['role'] == 'shopper':
                return redirect(url_for('shopper_dashboard'))
            return redirect(url_for('customer_dashboard'))
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('login.html')

@app.route('/login/customer')
def login_customer():
    return render_template('login_customer.html')

@app.route('/login/shopper')
def login_shopper():
    return render_template('login_shopper.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('index'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        location = request.form.get('location', '').strip()
        role = request.form.get('role', 'customer').strip().lower()
        upi_id = request.form.get('upi_id', '7387157739@upi').strip()

        if not all([name, email, phone, password, location]):
            flash('Please fill in all mandatory fields.', 'danger')
            return render_template('register.html', form_data=request.form)

        if password != confirm_password or len(password) < 6:
            flash('Passwords do not match or are shorter than 6 characters.', 'danger')
            return render_template('register.html', form_data=request.form)

        conn = get_db_connection()
        if conn.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone():
            conn.close()
            flash('An account with this email already exists. Please log in.', 'warning')
            return redirect(url_for('login'))

        password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (name, email, phone, password_hash, role, location, upi_id, is_verified)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1)
        ''', (name, email, phone, password_hash, role, location, upi_id))
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()

        session['user_id'] = user_id
        session['user_name'] = name
        session['user_role'] = role
        session['user_email'] = email

        flash(f'Account created successfully! Welcome to Pick4Me, {name}.', 'success')
        return redirect(url_for(f'{role}_dashboard'))

    return render_template('register.html', form_data={'role': request.args.get('role', 'customer')})

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    user_id = session['user_id']
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        location = request.form.get('location', '').strip()
        upi_id = request.form.get('upi_id', '7387157739@upi').strip()

        qr_code_filename = user['qr_code']
        if 'qr_code_file' in request.files:
            file = request.files['qr_code_file']
            if file and file.filename != '' and allowed_file(file.filename):
                ext = secure_filename(file.filename).rsplit('.', 1)[1].lower()
                unique_name = f"qr_{user_id}_{uuid.uuid4().hex[:8]}.{ext}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_name))
                qr_code_filename = unique_name

        conn.execute('''
            UPDATE users
            SET name = ?, phone = ?, location = ?, upi_id = ?, qr_code = ?
            WHERE id = ?
        ''', (name, phone, location, upi_id, qr_code_filename, user_id))
        conn.commit()
        session['user_name'] = name
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        conn.close()

        flash('Profile updated successfully!', 'success')
        return render_template('profile.html', user=user)

    conn.close()
    return render_template('profile.html', user=user)

# ==========================================
# ADMIN DASHBOARD
# ==========================================

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    conn = get_db_connection()
    stats = {
        'total_users': conn.execute("SELECT COUNT(*) FROM users WHERE role != 'admin'").fetchone()[0],
        'total_shops': conn.execute("SELECT COUNT(*) FROM shops").fetchone()[0],
        'total_products': conn.execute("SELECT COUNT(*) FROM products").fetchone()[0],
        'active_orders': conn.execute("SELECT COUNT(*) FROM orders WHERE status NOT IN ('Completed', 'Cancelled')").fetchone()[0],
        'completed_orders': conn.execute("SELECT COUNT(*) FROM orders WHERE status = 'Completed'").fetchone()[0],
        'escrow_funds': conn.execute("SELECT COALESCE(SUM(total_amount), 0) FROM orders WHERE payment_status = 'Escrow_Held'").fetchone()[0]
    }

    users = conn.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
    shops = conn.execute("SELECT s.*, u.name as owner_name FROM shops s JOIN users u ON s.owner_id = u.id ORDER BY s.created_at DESC").fetchall()
    orders = conn.execute('''
        SELECT o.*, c.name as customer_name, sh.name as shopper_name, s.shop_name
        FROM orders o
        JOIN users c ON o.customer_id = c.id
        LEFT JOIN users sh ON o.shopper_id = sh.id
        LEFT JOIN shops s ON o.shop_id = s.id
        ORDER BY o.created_at DESC
        LIMIT 15
    ''').fetchall()

    conn.close()
    return render_template('admin_dashboard.html', stats=stats, users=users, shops=shops, orders=orders)

@app.route('/admin/users/<int:id>/toggle-verify', methods=['POST'])
@admin_required
def toggle_user_verification(id):
    conn = get_db_connection()
    conn.execute('UPDATE users SET is_verified = 1 - is_verified WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash('User KYC verification status updated.', 'info')
    return redirect(url_for('admin_dashboard'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('404.html', error_code=500, error_message="Internal Server Error"), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    print(f"\n=======================================================")
    print(f"  🚀 Pick4Me server running at: http://127.0.0.1:{port}")
    print(f"=======================================================\n")
    app.run(host='0.0.0.0', port=port, debug=True)
