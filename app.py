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

from database import get_db_connection, init_db

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'pick4me-super-secret-key-college-demo-2026')
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max upload
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'svg'}

# Ensure upload directory exists
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
            return redirect(url_for('login'))
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
            return redirect(url_for('login'))
        if session.get('user_role') not in ('shopper', 'admin'):
            flash('Access restricted to Shopper accounts.', 'danger')
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
def inject_user():
    """Inject logged-in user profile and current year into all Jinja templates."""
    user = None
    if 'user_id' in session:
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        conn.close()
    return {'current_user': user, 'current_year': datetime.now().year}

# ==========================================
# PUBLIC ROUTES
# ==========================================

@app.route('/')
def index():
    conn = get_db_connection()
    total_requests = conn.execute("SELECT COUNT(*) FROM requests").fetchone()[0]
    completed_orders = conn.execute("SELECT COUNT(*) FROM orders WHERE status = 'Completed'").fetchone()[0]
    total_shopper_count = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'shopper'").fetchone()[0]
    
    # Recent public feed of requests (anonymized)
    recent_requests = conn.execute('''
        SELECT r.*, u.name as customer_name, u.location as customer_area
        FROM requests r
        JOIN users u ON r.customer_id = u.id
        WHERE r.status = 'Pending'
        ORDER BY r.created_at DESC
        LIMIT 4
    ''').fetchall()
    conn.close()

    return render_template(
        'index.html',
        stats={
            'requests': total_requests,
            'completed': completed_orders,
            'shoppers': total_shopper_count
        },
        recent_requests=recent_requests
    )

@app.route('/how-it-works')
def how_it_works():
    return render_template('index.html', scroll_to='how-it-works')

@app.route('/about')
def about():
    return render_template('index.html', scroll_to='about')

# ==========================================
# AUTHENTICATION ROUTES
# ==========================================

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for(f"{session.get('user_role', 'customer')}_dashboard"))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        location = request.form.get('location', '').strip()
        role = request.form.get('role', 'customer').strip().lower()
        upi_id = request.form.get('upi_id', '').strip()

        # Validations
        if not all([name, email, phone, password, location, role]):
            flash('Please fill in all required fields.', 'danger')
            return render_template('register.html', form_data=request.form)

        if role not in ('customer', 'shopper'):
            flash('Invalid role selected.', 'danger')
            return render_template('register.html', form_data=request.form)

        if password != confirm_password:
            flash('Passwords do not match. Please re-enter.', 'danger')
            return render_template('register.html', form_data=request.form)

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('register.html', form_data=request.form)

        conn = get_db_connection()
        existing_user = conn.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
        if existing_user:
            conn.close()
            flash('An account with this email address already exists. Please log in.', 'warning')
            return redirect(url_for('login'))

        password_hash = generate_password_hash(password, method='pbkdf2:sha256')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (name, email, phone, password_hash, role, location, upi_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (name, email, phone, password_hash, role, location, upi_id))
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()

        # Automatically log in user after registration
        session['user_id'] = user_id
        session['user_name'] = name
        session['user_role'] = role
        session['user_email'] = email

        flash(f'Welcome to Pick4Me, {name}! Your {role.capitalize()} account was created successfully.', 'success')
        return redirect(url_for(f'{role}_dashboard'))

    return render_template('register.html', form_data={})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        role = session.get('user_role', 'customer')
        if role == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif role == 'shopper':
            return redirect(url_for('shopper_dashboard'))
        return redirect(url_for('customer_dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Please provide both email and password.', 'warning')
            return render_template('login.html', email=email)

        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['user_role'] = user['role']
            session['user_email'] = user['email']

            flash(f"Welcome back, {user['name']}!", 'success')
            
            # Redirect according to role
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user['role'] == 'shopper':
                return redirect(url_for('shopper_dashboard'))
            else:
                return redirect(url_for('customer_dashboard'))
        else:
            flash('Invalid email or password. Please check your credentials.', 'danger')
            return render_template('login.html', email=email)

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))

# ==========================================
# CUSTOMER MODULE ROUTES
# ==========================================

@app.route('/customer/dashboard')
@customer_required
def customer_dashboard():
    user_id = session['user_id']
    conn = get_db_connection()

    # Metrics
    active_requests_count = conn.execute(
        "SELECT COUNT(*) FROM requests WHERE customer_id = ? AND status = 'Pending'",
        (user_id,)
    ).fetchone()[0]

    active_orders_count = conn.execute(
        "SELECT COUNT(*) FROM orders WHERE customer_id = ? AND status IN ('Accepted', 'Purchased', 'Out for Delivery', 'Delivered')",
        (user_id,)
    ).fetchone()[0]

    completed_orders_count = conn.execute(
        "SELECT COUNT(*) FROM orders WHERE customer_id = ? AND status = 'Completed'",
        (user_id,)
    ).fetchone()[0]

    # Recent requests
    recent_requests = conn.execute('''
        SELECT * FROM requests
        WHERE customer_id = ?
        ORDER BY created_at DESC
        LIMIT 5
    ''', (user_id,)).fetchall()

    # Active Orders needing attention (with shopper details)
    active_orders = conn.execute('''
        SELECT o.*, r.product_name, r.shop_name, r.delivery_address, u.name as shopper_name, u.phone as shopper_phone, u.upi_id as shopper_upi
        FROM orders o
        JOIN requests r ON o.request_id = r.id
        JOIN users u ON o.shopper_id = u.id
        WHERE o.customer_id = ? AND o.status != 'Completed' AND o.status != 'Cancelled'
        ORDER BY o.updated_at DESC
    ''', (user_id,)).fetchall()

    conn.close()

    return render_template(
        'customer_dashboard.html',
        active_requests_count=active_requests_count,
        active_orders_count=active_orders_count,
        completed_orders_count=completed_orders_count,
        recent_requests=recent_requests,
        active_orders=active_orders
    )

@app.route('/requests/create', methods=['GET', 'POST'])
@customer_required
def create_request():
    if request.method == 'POST':
        customer_id = session['user_id']
        product_name = request.form.get('product_name', '').strip()
        description = request.form.get('description', '').strip()
        category = request.form.get('category', 'General').strip()
        quantity = request.form.get('quantity', 1, type=int)
        shop_name = request.form.get('shop_name', '').strip()
        shop_address = request.form.get('shop_address', '').strip()
        delivery_address = request.form.get('delivery_address', '').strip()
        phone = request.form.get('phone', '').strip()
        estimated_price = request.form.get('estimated_price', 0.0, type=float)
        reward = request.form.get('reward', 0.0, type=float)
        instructions = request.form.get('instructions', '').strip()

        # Validation
        if not all([product_name, category, shop_name, shop_address, delivery_address, phone]):
            flash('Please fill in all mandatory product, shop, and delivery details.', 'danger')
            return render_template('create_request.html', form_data=request.form)

        if quantity < 1:
            flash('Quantity must be at least 1.', 'warning')
            return render_template('create_request.html', form_data=request.form)

        if estimated_price < 0 or reward < 5:
            flash('Please enter a valid estimated price and a minimum delivery reward of ₹5.', 'warning')
            return render_template('create_request.html', form_data=request.form)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO requests (
                customer_id, product_name, description, category, quantity,
                shop_name, shop_address, delivery_address, phone,
                estimated_price, reward, instructions, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending')
        ''', (
            customer_id, product_name, description, category, quantity,
            shop_name, shop_address, delivery_address, phone,
            estimated_price, reward, instructions
        ))
        conn.commit()
        request_id = cursor.lastrowid
        conn.close()

        flash('Request created successfully! Nearby shoppers can now see and accept it.', 'success')
        return redirect(url_for('request_details', id=request_id))

    # Prepopulate user phone and address if available
    conn = get_db_connection()
    user = conn.execute('SELECT phone, location FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    conn.close()

    default_form = {
        'phone': user['phone'] if user else '',
        'delivery_address': user['location'] if user else '',
        'quantity': 1,
        'reward': 20.0
    }
    return render_template('create_request.html', form_data=default_form)

@app.route('/customer/requests')
@customer_required
def customer_requests():
    status_filter = request.args.get('status', 'all')
    user_id = session['user_id']
    conn = get_db_connection()

    query = '''
        SELECT r.*, u.name as shopper_name
        FROM requests r
        LEFT JOIN users u ON r.shopper_id = u.id
        WHERE r.customer_id = ?
    '''
    params = [user_id]

    if status_filter != 'all':
        query += ' AND r.status = ?'
        params.append(status_filter)

    query += ' ORDER BY r.created_at DESC'
    requests_list = conn.execute(query, params).fetchall()
    conn.close()

    return render_template('requests.html', requests=requests_list, current_filter=status_filter, view_mode='customer')

@app.route('/requests/<int:id>/cancel', methods=['POST'])
@customer_required
def cancel_request(id):
    user_id = session['user_id']
    conn = get_db_connection()
    req = conn.execute('SELECT * FROM requests WHERE id = ?', (id,)).fetchone()

    if not req:
        conn.close()
        flash('Request not found.', 'danger')
        return redirect(url_for('customer_dashboard'))

    if req['customer_id'] != user_id and session.get('user_role') != 'admin':
        conn.close()
        flash('You are not authorized to cancel this request.', 'danger')
        return redirect(url_for('customer_dashboard'))

    if req['status'] != 'Pending':
        conn.close()
        flash('Cannot cancel a request that has already been accepted or processed.', 'warning')
        return redirect(url_for('request_details', id=id))

    conn.execute("UPDATE requests SET status = 'Cancelled', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    flash('Shopping request has been cancelled.', 'info')
    return redirect(url_for('customer_requests'))

# ==========================================
# SHOPPER MODULE ROUTES
# ==========================================

@app.route('/shopper/dashboard')
@shopper_required
def shopper_dashboard():
    shopper_id = session['user_id']
    conn = get_db_connection()

    # Metrics
    available_requests_count = conn.execute(
        "SELECT COUNT(*) FROM requests WHERE status = 'Pending'"
    ).fetchone()[0]

    active_deliveries_count = conn.execute(
        "SELECT COUNT(*) FROM orders WHERE shopper_id = ? AND status IN ('Accepted', 'Purchased', 'Out for Delivery', 'Delivered')",
        (shopper_id,)
    ).fetchone()[0]

    completed_deliveries_count = conn.execute(
        "SELECT COUNT(*) FROM orders WHERE shopper_id = ? AND status = 'Completed'",
        (shopper_id,)
    ).fetchone()[0]

    total_earnings_row = conn.execute(
        "SELECT COALESCE(SUM(reward), 0) FROM orders WHERE shopper_id = ? AND status = 'Completed'",
        (shopper_id,)
    ).fetchone()
    total_earnings = total_earnings_row[0] if total_earnings_row else 0.0

    # Top available requests
    available_requests = conn.execute('''
        SELECT r.*, u.name as customer_name, u.location as customer_area
        FROM requests r
        JOIN users u ON r.customer_id = u.id
        WHERE r.status = 'Pending'
        ORDER BY r.created_at DESC
        LIMIT 6
    ''').fetchall()

    # Current active deliveries
    active_deliveries = conn.execute('''
        SELECT o.*, r.product_name, r.shop_name, r.shop_address, r.delivery_address, r.phone as customer_phone, u.name as customer_name
        FROM orders o
        JOIN requests r ON o.request_id = r.id
        JOIN users u ON o.customer_id = u.id
        WHERE o.shopper_id = ? AND o.status != 'Completed' AND o.status != 'Cancelled'
        ORDER BY o.updated_at DESC
    ''', (shopper_id,)).fetchall()

    conn.close()

    return render_template(
        'shopper_dashboard.html',
        available_requests_count=available_requests_count,
        active_deliveries_count=active_deliveries_count,
        completed_deliveries_count=completed_deliveries_count,
        total_earnings=total_earnings,
        available_requests=available_requests,
        active_deliveries=active_deliveries
    )

@app.route('/requests')
def available_requests():
    """Browse requests - Public/Shopper view of pending requests with search & filter."""
    search_query = request.args.get('q', '').strip()
    category = request.args.get('category', 'all')
    status_filter = request.args.get('status', 'Pending')

    conn = get_db_connection()
    query = '''
        SELECT r.*, u.name as customer_name, u.location as customer_area
        FROM requests r
        JOIN users u ON r.customer_id = u.id
        WHERE 1=1
    '''
    params = []

    # If non-admin shopper, show Pending by default
    if status_filter != 'all':
        query += ' AND r.status = ?'
        params.append(status_filter)

    if category != 'all':
        query += ' AND r.category = ?'
        params.append(category)

    if search_query:
        query += ' AND (r.product_name LIKE ? OR r.shop_name LIKE ? OR r.delivery_address LIKE ?)'
        wildcard = f"%{search_query}%"
        params.extend([wildcard, wildcard, wildcard])

    query += ' ORDER BY r.created_at DESC'
    requests_list = conn.execute(query, params).fetchall()

    # Categories for filter bar
    categories = conn.execute('SELECT DISTINCT category FROM requests').fetchall()
    conn.close()

    return render_template(
        'requests.html',
        requests=requests_list,
        categories=[c['category'] for c in categories if c['category']],
        current_category=category,
        current_query=search_query,
        current_filter=status_filter,
        view_mode='shopper'
    )

@app.route('/requests/<int:id>')
def request_details(id):
    conn = get_db_connection()
    req = conn.execute('''
        SELECT r.*, c.name as customer_name, c.email as customer_email, c.location as customer_location,
               s.name as shopper_name, s.phone as shopper_phone
        FROM requests r
        JOIN users c ON r.customer_id = c.id
        LEFT JOIN users s ON r.shopper_id = s.id
        WHERE r.id = ?
    ''', (id,)).fetchone()

    # Check if there is an associated order
    order = None
    if req:
        order = conn.execute('SELECT * FROM orders WHERE request_id = ?', (id,)).fetchone()

    conn.close()

    if not req:
        abort(404)

    return render_template('request_details.html', req=req, order=order)

@app.route('/requests/<int:id>/accept', methods=['POST'])
@shopper_required
def accept_request(id):
    shopper_id = session['user_id']
    conn = get_db_connection()

    # Atomic transaction check: Ensure request is strictly 'Pending' and not already accepted
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM requests WHERE id = ? FOR UPDATE", (id,)) if 'sqlite' not in str(type(conn)) else cursor.execute("SELECT * FROM requests WHERE id = ?", (id,))
    req = cursor.fetchone()

    if not req:
        conn.close()
        flash('Request not found.', 'danger')
        return redirect(url_for('available_requests'))

    if req['customer_id'] == shopper_id:
        conn.close()
        flash('You cannot accept your own shopping request.', 'warning')
        return redirect(url_for('request_details', id=id))

    if req['status'] != 'Pending':
        conn.close()
        flash('This request has already been accepted by another shopper or is no longer available.', 'danger')
        return redirect(url_for('available_requests'))

    # Update request status and assign shopper
    cursor.execute('''
        UPDATE requests
        SET status = 'Accepted', shopper_id = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ? AND status = 'Pending'
    ''', (shopper_id, id))

    if cursor.rowcount == 0:
        conn.close()
        flash('Could not accept request. It may have just been claimed by another shopper.', 'danger')
        return redirect(url_for('available_requests'))

    # Create associated Order
    product_amount = float(req['estimated_price'])
    reward = float(req['reward'])
    total_amount = product_amount + reward

    cursor.execute('''
        INSERT INTO orders (
            request_id, customer_id, shopper_id,
            product_amount, reward, total_amount, status
        ) VALUES (?, ?, ?, ?, ?, ?, 'Accepted')
    ''', (id, req['customer_id'], shopper_id, product_amount, reward, total_amount))
    order_id = cursor.lastrowid

    # Create initial Payment record
    cursor.execute('''
        INSERT INTO payments (order_id, amount, status, payment_method)
        VALUES (?, ?, 'Pending', 'UPI')
    ''', (order_id, total_amount))

    conn.commit()
    conn.close()

    flash('Request accepted successfully! You are now the designated shopper for this order.', 'success')
    return redirect(url_for('order_details', id=order_id))

# ==========================================
# ORDER MANAGEMENT & TRACKING
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
            SELECT o.*, r.product_name, r.shop_name, r.delivery_address, u.name as counterpart_name, u.phone as counterpart_phone
            FROM orders o
            JOIN requests r ON o.request_id = r.id
            JOIN users u ON o.shopper_id = u.id
            WHERE o.customer_id = ?
        '''
        params = [user_id]
    elif role == 'shopper':
        query = '''
            SELECT o.*, r.product_name, r.shop_name, r.delivery_address, u.name as counterpart_name, u.phone as counterpart_phone
            FROM orders o
            JOIN requests r ON o.request_id = r.id
            JOIN users u ON o.customer_id = u.id
            WHERE o.shopper_id = ?
        '''
        params = [user_id]
    else:  # admin
        query = '''
            SELECT o.*, r.product_name, r.shop_name, r.delivery_address,
                   c.name as customer_name, s.name as shopper_name, s.name as counterpart_name
            FROM orders o
            JOIN requests r ON o.request_id = r.id
            JOIN users c ON o.customer_id = c.id
            JOIN users s ON o.shopper_id = s.id
            WHERE 1=1
        '''
        params = []

    if status_filter == 'active':
        query += " AND o.status IN ('Accepted', 'Purchased', 'Out for Delivery', 'Delivered')"
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
               r.product_name, r.description, r.category, r.quantity, r.shop_name, r.shop_address,
               r.delivery_address, r.phone as customer_contact_phone, r.instructions,
               c.name as customer_name, c.email as customer_email, c.location as customer_location,
               s.name as shopper_name, s.phone as shopper_phone, s.email as shopper_email,
               s.upi_id as shopper_upi, s.qr_code as shopper_qr_code
        FROM orders o
        JOIN requests r ON o.request_id = r.id
        JOIN users c ON o.customer_id = c.id
        JOIN users s ON o.shopper_id = s.id
        WHERE o.id = ?
    ''', (id,)).fetchone()

    if not order:
        conn.close()
        abort(404)

    # Access control
    if role != 'admin' and order['customer_id'] != user_id and order['shopper_id'] != user_id:
        conn.close()
        flash('You do not have permission to view this order.', 'danger')
        return redirect(url_for('index'))

    payment = conn.execute('SELECT * FROM payments WHERE order_id = ?', (id,)).fetchone()
    conn.close()

    # Determine allowed next step for shopper
    next_step = None
    if order['status'] == 'Accepted':
        next_step = {'action': 'Purchased', 'label': 'Mark as Purchased (Item Bought)', 'class': 'btn-primary'}
    elif order['status'] == 'Purchased':
        next_step = {'action': 'Out for Delivery', 'label': 'Mark as Out for Delivery', 'class': 'btn-warning'}
    elif order['status'] == 'Out for Delivery':
        next_step = {'action': 'Delivered', 'label': 'Mark as Delivered at Destination', 'class': 'btn-success'}

    return render_template(
        'order_details.html',
        order=order,
        payment=payment,
        next_step=next_step,
        user_role=role,
        current_user_id=user_id
    )

@app.route('/orders/<int:id>/update-status', methods=['POST'])
@shopper_required
def update_order_status(id):
    shopper_id = session['user_id']
    new_status = request.form.get('status', '').strip()

    conn = get_db_connection()
    order = conn.execute('SELECT * FROM orders WHERE id = ?', (id,)).fetchone()

    if not order:
        conn.close()
        flash('Order not found.', 'danger')
        return redirect(url_for('orders_list'))

    if order['shopper_id'] != shopper_id and session.get('user_role') != 'admin':
        conn.close()
        flash('Only the assigned shopper can update the delivery status of this order.', 'danger')
        return redirect(url_for('order_details', id=id))

    current_status = order['status']

    # Strict state-machine validation
    valid_transitions = {
        'Accepted': 'Purchased',
        'Purchased': 'Out for Delivery',
        'Out for Delivery': 'Delivered'
    }

    if current_status not in valid_transitions or valid_transitions[current_status] != new_status:
        conn.close()
        flash(f'Invalid status transition from "{current_status}" to "{new_status}".', 'danger')
        return redirect(url_for('order_details', id=id))

    # Update both order and request status
    cursor = conn.cursor()
    cursor.execute('UPDATE orders SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', (new_status, id))
    cursor.execute('UPDATE requests SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?', (new_status, order['request_id']))
    conn.commit()
    conn.close()

    flash(f'Order status updated to: {new_status}', 'success')
    return redirect(url_for('order_details', id=id))

@app.route('/orders/<int:id>/confirm-delivery', methods=['POST'])
@customer_required
def confirm_delivery(id):
    customer_id = session['user_id']
    conn = get_db_connection()
    order = conn.execute('SELECT * FROM orders WHERE id = ?', (id,)).fetchone()

    if not order:
        conn.close()
        flash('Order not found.', 'danger')
        return redirect(url_for('orders_list'))

    if order['customer_id'] != customer_id and session.get('user_role') != 'admin':
        conn.close()
        flash('Only the customer who placed this order can confirm its delivery.', 'danger')
        return redirect(url_for('order_details', id=id))

    if order['status'] != 'Delivered':
        conn.close()
        flash('Order must be marked as "Delivered" by the shopper before delivery confirmation.', 'warning')
        return redirect(url_for('order_details', id=id))

    cursor = conn.cursor()
    cursor.execute("UPDATE orders SET status = 'Completed', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (id,))
    cursor.execute("UPDATE requests SET status = 'Completed', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (order['request_id'],))
    
    # Auto-confirm payment status on completion if not already done
    cursor.execute("UPDATE payments SET status = 'Confirmed' WHERE order_id = ?", (id,))
    
    conn.commit()
    conn.close()

    flash('Delivery completed successfully! Thank you for using Pick4Me.', 'success')
    return redirect(url_for('order_details', id=id))

# ==========================================
# PAYMENT DEMO SYSTEM
# ==========================================

@app.route('/orders/<int:id>/payment', methods=['GET'])
@customer_required
def payment_page(id):
    customer_id = session['user_id']
    conn = get_db_connection()
    order = conn.execute('''
        SELECT o.*, r.product_name, r.shop_name,
               s.name as shopper_name, s.upi_id as shopper_upi, s.qr_code as shopper_qr, s.phone as shopper_phone
        FROM orders o
        JOIN requests r ON o.request_id = r.id
        JOIN users s ON o.shopper_id = s.id
        WHERE o.id = ?
    ''', (id,)).fetchone()

    if not order:
        conn.close()
        abort(404)

    if order['customer_id'] != customer_id and session.get('user_role') != 'admin':
        conn.close()
        flash('Unauthorized access to payment page.', 'danger')
        return redirect(url_for('orders_list'))

    payment = conn.execute('SELECT * FROM payments WHERE order_id = ?', (id,)).fetchone()
    conn.close()

    return render_template('payment.html', order=order, payment=payment)

@app.route('/orders/<int:id>/payment/confirm', methods=['POST'])
@customer_required
def confirm_payment(id):
    customer_id = session['user_id']
    conn = get_db_connection()
    order = conn.execute('SELECT * FROM orders WHERE id = ?', (id,)).fetchone()

    if not order or (order['customer_id'] != customer_id and session.get('user_role') != 'admin'):
        conn.close()
        flash('Unauthorized.', 'danger')
        return redirect(url_for('orders_list'))

    conn.execute("UPDATE payments SET status = 'Confirmed' WHERE order_id = ?", (id,))
    conn.commit()
    conn.close()

    flash('Demo Payment Confirmed! The shopper has been notified.', 'success')
    return redirect(url_for('order_details', id=id))

# ==========================================
# SHOPPER EARNINGS
# ==========================================

@app.route('/shopper/earnings')
@shopper_required
def shopper_earnings():
    shopper_id = session['user_id']
    conn = get_db_connection()

    # Total Cleared Earnings (Completed Orders)
    total_cleared = conn.execute('''
        SELECT COALESCE(SUM(reward), 0)
        FROM orders
        WHERE shopper_id = ? AND status = 'Completed'
    ''', (shopper_id,)).fetchone()[0]

    # Completed Deliveries Count
    completed_count = conn.execute('''
        SELECT COUNT(*)
        FROM orders
        WHERE shopper_id = ? AND status = 'Completed'
    ''', (shopper_id,)).fetchone()[0]

    # Pending Earnings (In-progress deliveries)
    pending_earnings = conn.execute('''
        SELECT COALESCE(SUM(reward), 0)
        FROM orders
        WHERE shopper_id = ? AND status IN ('Accepted', 'Purchased', 'Out for Delivery', 'Delivered')
    ''', (shopper_id,)).fetchone()[0]

    # Detailed history of deliveries
    deliveries_history = conn.execute('''
        SELECT o.*, r.product_name, r.shop_name, u.name as customer_name, p.status as payment_status
        FROM orders o
        JOIN requests r ON o.request_id = r.id
        JOIN users u ON o.customer_id = u.id
        LEFT JOIN payments p ON o.id = p.order_id
        WHERE o.shopper_id = ?
        ORDER BY o.updated_at DESC
    ''', (shopper_id,)).fetchall()

    conn.close()

    return render_template(
        'earnings.html',
        total_cleared=total_cleared,
        completed_count=completed_count,
        pending_earnings=pending_earnings,
        deliveries=deliveries_history
    )

# ==========================================
# PROFILE MANAGEMENT
# ==========================================

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
        upi_id = request.form.get('upi_id', '').strip()

        if not name or not phone or not location:
            conn.close()
            flash('Name, Phone, and Location are required.', 'warning')
            return render_template('profile.html', user=user)

        qr_code_filename = user['qr_code']

        # Handle optional QR code image upload for shoppers
        if 'qr_code_file' in request.files:
            file = request.files['qr_code_file']
            if file and file.filename != '':
                if allowed_file(file.filename):
                    ext = secure_filename(file.filename).rsplit('.', 1)[1].lower()
                    unique_name = f"qr_{user_id}_{uuid.uuid4().hex[:8]}.{ext}"
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
                    file.save(filepath)
                    qr_code_filename = unique_name
                else:
                    conn.close()
                    flash('Invalid file format. Allowed formats: PNG, JPG, JPEG, WEBP, SVG.', 'danger')
                    return render_template('profile.html', user=user)

        # Update user profile
        conn.execute('''
            UPDATE users
            SET name = ?, phone = ?, location = ?, upi_id = ?, qr_code = ?
            WHERE id = ?
        ''', (name, phone, location, upi_id, qr_code_filename, user_id))
        conn.commit()

        # Update session name
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

    total_users = conn.execute("SELECT COUNT(*) FROM users WHERE role != 'admin'").fetchone()[0]
    total_customers = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'customer'").fetchone()[0]
    total_shoppers = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'shopper'").fetchone()[0]
    total_requests = conn.execute("SELECT COUNT(*) FROM requests").fetchone()[0]
    active_orders = conn.execute("SELECT COUNT(*) FROM orders WHERE status IN ('Accepted', 'Purchased', 'Out for Delivery', 'Delivered')").fetchone()[0]
    completed_orders = conn.execute("SELECT COUNT(*) FROM orders WHERE status = 'Completed'").fetchone()[0]

    users_list = conn.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
    requests_list = conn.execute('''
        SELECT r.*, c.name as customer_name, s.name as shopper_name
        FROM requests r
        JOIN users c ON r.customer_id = c.id
        LEFT JOIN users s ON r.shopper_id = s.id
        ORDER BY r.created_at DESC
        LIMIT 10
    ''').fetchall()
    orders_list = conn.execute('''
        SELECT o.*, r.product_name, c.name as customer_name, s.name as shopper_name
        FROM orders o
        JOIN requests r ON o.request_id = r.id
        JOIN users c ON o.customer_id = c.id
        JOIN users s ON o.shopper_id = s.id
        ORDER BY o.updated_at DESC
        LIMIT 10
    ''').fetchall()

    conn.close()

    return render_template(
        'admin_dashboard.html',
        stats={
            'total_users': total_users,
            'customers': total_customers,
            'shoppers': total_shoppers,
            'requests': total_requests,
            'active_orders': active_orders,
            'completed_orders': completed_orders
        },
        users=users_list,
        requests=requests_list,
        orders=orders_list
    )

@app.route('/admin/users/<int:id>/delete', methods=['POST'])
@admin_required
def admin_delete_user(id):
    if id == session['user_id']:
        flash('You cannot delete your own admin account.', 'danger')
        return redirect(url_for('admin_dashboard'))

    conn = get_db_connection()
    conn.execute('DELETE FROM users WHERE id = ?', (id,))
    conn.commit()
    conn.close()

    flash('User deleted successfully.', 'info')
    return redirect(url_for('admin_dashboard'))

# ==========================================
# ERROR HANDLERS
# ==========================================

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
