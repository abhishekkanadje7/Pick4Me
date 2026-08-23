# Pick4Me 🛍️🚴
> **Your Community, Your Delivery**  
> *A Hyperlocal Community Shopping and Peer-to-Peer Delivery Platform*

---

## 🌟 Project Overview

**Pick4Me** is a full-stack, community-driven web application built for college campuses, hostels, residential complexes, and local neighbourhoods. 

The idea is simple:
1. **A customer** needs a product from a nearby shop (stationery, medicine, snacks, groceries, printouts) but cannot or does not want to go in person.
2. The customer creates a shopping request on **Pick4Me** detailing the item, shop location, destination, and a delivery reward.
3. **A nearby shopper** (e.g. a fellow student already heading to the market or library) sees the request and accepts it.
4. The shopper purchases the product, delivers it to the customer, and receives the product cost plus the reward.
5. The customer confirms receipt and completes payment seamlessly via **Demo UPI QR**.

---

## ✨ Key Features

### 👤 1. Role-Based Portals & Dashboards
- **Customer Portal**: Create requests, track active deliveries in real-time, view invoice breakdowns, confirm deliveries, and simulate payments.
- **Shopper Portal**: Browse available requests with keyword/category search, claim tasks, update step-by-step delivery progress, and monitor cleared vs. pending earnings.
- **Admin Control Center**: Monitor platform health, oversee all registered users, inspect requests, track orders, and delete test accounts.

### 🛡️ 2. Step-by-Step Order State Machine
Enforces strict lifecycle progression:
$$\text{Pending} \longrightarrow \text{Accepted} \longrightarrow \text{Purchased} \longrightarrow \text{Out for Delivery} \longrightarrow \text{Delivered} \longrightarrow \text{Completed}$$
- **Atomic Concurrency Protection**: Prevents multiple shoppers from claiming the same shopping request simultaneously.
- **Delivery Confirmation**: Only the customer who placed the order can mark the delivery as `Completed`.

### 💳 3. Demo UPI Payment System
- Displays the shopper's personal UPI ID and QR code image.
- Transparent price breakdown ($\text{Product Price} + \text{Shopper Reward} = \text{Total Amount}$).
- One-click copy for UPI VPA and interactive demo payment confirmation.
- Clearly marked as an academic demo (no real banking credentials required).

### 📱 4. Modern, Responsive UI / UX
- Emerald green primary theme with warm amber accents.
- Responsive mobile drawer navigation, clean cards, status badges, and animated progress timeline.
- One-click **Demo Quick-Fill buttons** on the login page for effortless presentations.

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Frontend** | HTML5, CSS3 (Modern Flex/Grid & Variables), Vanilla JavaScript |
| **Backend** | Python 3, Flask 3.0, Jinja2 Template Engine |
| **Database** | SQLite3 (Normalized tables with foreign keys and cascading) |
| **Security** | Werkzeug Password Hashing (`scrypt`), Role-based Session Guards |
| **Deployment** | Gunicorn WSGI Server, Procfile |

---

## 📁 Project Directory Structure

```text
Pick4Me/
│
├── app.py                  # Main Flask application & route controllers
├── database.py             # SQLite schema initialization & demo seed data
├── requirements.txt        # Python package dependencies
├── Procfile                # WSGI deployment configuration (Gunicorn)
├── .gitignore              # Git ignored files (venv, db, caches)
├── README.md               # Project documentation & setup manual
├── test_workflow.py        # Automated end-to-end test suite
│
├── templates/              # Jinja2 HTML Templates
│   ├── base.html           # Base layout with navbar, alerts & footer
│   ├── index.html          # Homepage (Hero, How It Works, Why Pick4Me, Roadmap)
│   ├── login.html          # Authentication with 1-click Demo Fill
│   ├── register.html       # User registration with role selection
│   ├── customer_dashboard.html # Customer hub & order tracking
│   ├── shopper_dashboard.html  # Shopper hub & available jobs feed
│   ├── admin_dashboard.html    # Admin panel for user & order management
│   ├── create_request.html     # Request creation form with live price calculator
│   ├── requests.html       # Marketplace & searchable request board
│   ├── request_details.html    # Request details & Accept Request action
│   ├── orders.html         # Filterable orders & deliveries list
│   ├── order_details.html  # Visual progress tracker & step updates
│   ├── payment.html        # UPI QR Scan & Pay demo interface
│   ├── earnings.html       # Shopper earnings analytics & task history
│   ├── profile.html        # Profile management & custom QR upload
│   └── 404.html            # Friendly error handler page
│
└── static/                 # Static Assets
    ├── css/
    │   └── style.css       # Complete responsive styling & design system
    ├── js/
    │   └── script.js       # Dynamic totals, clipboard copy, mobile toggle
    ├── images/
    │   ├── logo.svg        # Pick4Me brand vector logo
    │   ├── logo.png        # Pick4Me brand raster logo
    │   └── demo_qr.png     # Default UPI QR graphic
    └── uploads/            # User-uploaded QR code storage
```

---

## 🚀 Local Installation & Setup Guide

### 1. Prerequisites
- Python 3.8 or higher installed on your machine.
- Git (optional, for cloning).

### 2. Step-by-Step Commands

```bash
# 1. Navigate to project folder
cd Pick4Me

# 2. Create a virtual environment
python3 -m venv venv

# 3. Activate the virtual environment
# On macOS / Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# 4. Install required dependencies
pip install -r requirements.txt

# 5. Run the application
python app.py
```

### 3. Open in Browser
Visit **`http://127.0.0.1:5001`** in any web browser.

> **Note on macOS:** We use port `5001` by default to avoid conflicts with macOS AirPlay Receiver (which reserves port 5000). The SQLite database `pick4me.db` initializes and seeds automatically on the first run!

---

## 🔑 Demo Login Credentials

You can log in directly using the credentials below, or click the **One-Click Demo buttons** on the Login page:

| Role | Email | Password | Pre-seeded Profile |
|---|---|---|---|
| 👤 **Customer** | `customer@pick4me.demo` | `customer123` | Priya Sharma (Kaveri Hostel) |
| 🚴 **Shopper** | `shopper@pick4me.demo` | `shopper123` | Rahul Verma (Campus Central) |
| 🛡️ **Admin** | `admin@pick4me.demo` | `admin123` | System Administrator |

---

## 🔄 Complete Demo Workflow Walkthrough

To demonstrate the full lifecycle to evaluators or during hackathon presentations:

1. **Step 1 - Login as Customer**:
   - Go to `http://127.0.0.1:5000/login` &rarr; click **👤 Customer**.
2. **Step 2 - Post a Request**:
   - Click **+ Create New Request**.
   - Enter: Product: *Classmate Notebook*, Shop: *ABC Stationery*, Reward: *₹30*.
   - Submit the form. Status becomes `Pending`.
3. **Step 3 - Switch to Shopper**:
   - Log out, then log in using **🚴 Shopper**.
4. **Step 4 - Accept Request**:
   - Open **Find Requests**, select the Notebook request, and click **Accept Request**.
   - Status changes to `Accepted` and an Order is generated.
5. **Step 5 - Update Delivery Milestones**:
   - Click **Mark as Purchased** &rarr; status becomes `Purchased`.
   - Click **Mark as Out for Delivery** &rarr; status becomes `Out for Delivery`.
   - Click **Mark as Delivered** &rarr; status becomes `Delivered`.
6. **Step 6 - Customer Confirms & Pays**:
   - Log back in as **Customer**.
   - Open the Order &rarr; click **Pay via UPI** to view the Demo QR and confirm payment.
   - Click **Confirm Delivery**.
   - Status transitions to `Completed`.
7. **Step 7 - Verify Earnings**:
   - Log in as **Shopper** &rarr; open **Earnings**. The reward (₹30) is now cleared in Total Earnings!

---

## 🧪 Automated Testing

Run the automated test suite to verify the entire system in under 2 seconds:

```bash
python test_workflow.py
```

---

## ☁️ Deployment Instructions

### Deploying to Render.com / Railway
1. Push your repository to GitHub.
2. Log into [Render.com](https://render.com) & click **New Web Service**.
3. Select your GitHub repository.
4. Configure settings:
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
5. Click **Deploy Web Service**.

---

## 🔮 Future Scope & Roadmap

- [ ] **Real Payment Gateway Integration**: Automated escrow via Razorpay / Paytm APIs.
- [ ] **Interactive Maps**: Real-time Google Maps integration with route planning.
- [ ] **Live GPS Tracking**: Shopper live location sharing during transit.
- [ ] **Push & WhatsApp Notifications**: Instant alerts when status changes.
- [ ] **Native Mobile Application**: Cross-platform Flutter / React Native client.
- [ ] **Shopper Ratings & Reviews**: Community trust scores and badges.

---

## 📄 License
Academic Mini-Project Demo &copy; 2026 Pick4Me. Built for education and community commerce.
