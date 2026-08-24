# Pick4Me 🛍️🚴
> **Local Marketplace & Crowdsourced Peer Delivery Network**  
> *Connecting Local Stores, Campus Students, and Daily Commuters*

---

## 🌟 Project Overview

**Pick4Me** is a full-stack, Amazon/Blinkit-style community e-commerce marketplace and crowdsourced peer delivery platform.

It solves two primary community problems:
1. **Local Campus Stores & Merchants**: Allows campus shopkeepers and student entrepreneurs to register their stores and catalog real products with photos and prices.
2. **Crowdsourced Commute Delivery**: Anyone travelling from a market, canteen, or store can pick up orders for fellow peers on their route, earn delivery rewards, and build a local earnings balance.
3. **Advance Escrow Payment & Handover OTP**: Eliminates customer refusal/fraud. Customers pay in advance via **UPI QR (`7387157739@upi`)**. Funds are locked in **Platform Escrow** and released to the deliverer's wallet **only when the deliverer verifies the customer's 4-digit Delivery OTP**.

---

## ✨ Key Features

### 🏪 1. Amazon-Style Storefront & Product Catalog
- **Store Directory (`/shops`)**: Browse registered campus shops by category.
- **Product Search & Filtering (`/products`)**: Live search, price filters, category tabs, and real-time stock indicators.
- **Shopping Cart (`/cart`)**: Multi-item cart, automatic subtotal, and delivery fee calculation.
- **Merchant Hub (`/merchant/shop`)**: Merchants can register their store, manage address/phone, and add/delete products in real-time.

### ⚡ 2. Custom Peer Errands
- Can't find an item in registered stores? Customers can create a **Custom Errand Request** detailing item, shop location, estimated cost, and delivery reward.

### 👥 3-Party Peer Logistics Architecture (Customer A & B + Merchant Shop + Admin Escrow)
```text
[ Customer A (Buyer) ] 
       │ Places Order & Pays (Item Price + Delivery Reward) in Advance
       ▼
[ Admin / Platform Escrow (7387157739@upi) ]
       │ Holds 100% Funds Securely
       ├───► Customer B (Peer Commuter) Accepts Delivery Task
       │
       ├───► [ STAGE 1: Shop Handover ]
       │     Customer B reaches Shop & picks up item.
       │     Shopkeeper confirms pickup.
       │     💰 AUTOMATIC PAYOUT 1: Admin transfers Item Cost directly to Shopkeeper's Wallet!
       │
       └───► [ STAGE 2: Customer Handover ]
             Customer B delivers item to Customer A's room/hostel.
             Customer A verifies item & gives 4-Digit Delivery OTP.
             Customer B verifies OTP.
             💰 AUTOMATIC PAYOUT 2: Admin transfers Delivery Reward (+ Speed Bonus) to Customer B's Wallet!
             ✅ Order Completed!
```

### 💰 4. Commuter Wallet & Payouts (`/wallet`)
- Real-time wallet balance tracking.
- Instant transaction ledger (`#TXN-xxx`).
- Registered UPI VPA (`7387157739@upi`) for automatic payouts.

### 🔐 5. Dedicated Portals & Role-Based Access Control
- **Customer Portal**: Store shopping, cart checkout, errand creation, live order tracking with OTP.
- **Shopper / Merchant Portal**: Store inventory manager, available tasks board, wallet analytics.
- **Admin Control Center**: System metrics, KYC verification toggle, store directory, escrow fund ledger.

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Frontend** | HTML5, CSS3 (Variables, Flexbox/Grid), Vanilla JavaScript |
| **Backend** | Python 3, Flask 3.0, Jinja2 Template Engine |
| **Database** | SQLite3 (`pick4me.db`) with relational foreign keys |
| **Security** | Werkzeug Password Hashing (`pbkdf2:sha256`), Advance Escrow, 4-digit Delivery OTP |
| **Payment Integration** | UPI QR Scanner (`7387157739@upi`) |
| **Production WSGI** | Gunicorn WSGI Server, Procfile |

---

## 📁 Project Structure

```text
Pick4Me/
├── app.py                      # Core Flask controller & API endpoints
├── database.py                 # SQLite schema, tables & admin seed
├── requirements.txt            # Python dependencies (Flask, Werkzeug, Gunicorn)
├── Procfile                    # WSGI configuration for Render cloud deployment
├── .gitignore                  # Git ignore rules
├── README.md                   # Documentation & setup manual
├── test_workflow.py            # Automated 12-step verification suite
│
├── templates/                  # Jinja2 HTML Templates
│   ├── base.html               # Global responsive layout with cart badge & nav
│   ├── index.html              # Amazon-style marketplace landing page
│   ├── products.html           # Product catalog with live search & cart
│   ├── shops.html              # Local campus store directory
│   ├── shop_detail.html        # Storefront profile & item list
│   ├── cart.html               # Shopping cart & advance checkout
│   ├── merchant_shop.html      # Shop profile setup & product catalog manager
│   ├── wallet.html             # Shopper wallet with ledger & balance
│   ├── payment.html            # Advance Escrow UPI payment screen with QR
│   ├── order_details.html      # Live progress tracker & 4-digit OTP handover
│   ├── customer_dashboard.html # Customer order tracking hub
│   ├── shopper_dashboard.html  # Commuter deliveries board & task claim
│   ├── admin_dashboard.html    # Admin panel (KYC, Stores, Escrow ledger)
│   ├── login.html              # Clean portal login
│   ├── login_customer.html     # Dedicated customer login
│   ├── login_shopper.html      # Dedicated commuter/store login
│   ├── register.html           # Account registration with role selection
│   └── 404.html                # Friendly error page
│
└── static/                     # Static Assets
    ├── css/
    │   └── style.css           # Clean modern responsive stylesheet
    ├── js/
    │   └── script.js           # Dynamic totals, clipboard copy, mobile menu
    ├── images/
    │   ├── logo.svg            # Pick4Me vector brand logo
    │   ├── logo.png            # Pick4Me brand logo
    │   └── upi_qr.png          # Real UPI QR Code image (7387157739@upi)
    └── uploads/                # Custom user images
```

---

## 🚀 Local Installation & Running

```bash
# 1. Navigate to project folder
cd /Users/abhishekkanadje7/.gemini/antigravity/scratch/Pick4Me

# 2. Activate virtual environment
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run application
python app.py
```
Open **`http://127.0.0.1:5001`** in your browser.

---

## 🛡️ Admin Login Credentials

| Role | Email | Password | Scope |
|---|---|---|---|
| 🛡️ **System Administrator** | `abhishekkanadje7@gmail.com` | `Abhi*2007` | Full Platform Oversight & KYC Control |

---

## 🧪 Automated Testing

Run the automated test suite:

```bash
python test_workflow.py
```

---

## 📄 License
Academic Mini-Project &copy; 2026 Pick4Me.
