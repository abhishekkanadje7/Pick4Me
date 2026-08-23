# 🏆 Prasunethon 2.0 — Final Project Submission Guide

---

## 📌 Project Overview & Quick Links

- **Project Title**: Pick4Me — Hyperlocal Campus E-Commerce & Crowdsourced Commute Delivery Platform
- **Tagline**: *Empowering Local Stores & Everyday Commuters through Smart SLA & Escrow-Protected Deliveries*
- **GitHub Source Code Repository**: [https://github.com/abhishekkanadje7/Pick4Me](https://github.com/abhishekkanadje7/Pick4Me)
- **Live Deployed Application**: [https://pick4me-l868.onrender.com](https://pick4me-l868.onrender.com)
- **Primary Admin Credentials**: 
  - **Email**: `abhishekkanadje7@gmail.com`
  - **Password**: `Abhi*2007`

---

## 📝 Unstop Form Fields (Ready to Copy-Paste)

### 1. Project Title
```text
Pick4Me — Local Marketplace & Crowdsourced Peer Delivery Network
```

### 2. Short Description / Elevator Pitch (1-2 sentences)
```text
Pick4Me is a full-stack hyperlocal marketplace that connects local campus shops with students while leveraging daily commuter foot traffic to provide zero-emission, peer-to-peer deliveries powered by dynamic SLA pricing and advance escrow security.
```

---

### 3. Problem Statement
```text
In university campuses, hostels, and residential communities:
1. High Delivery Costs & Minimum Order Limits: Major commercial delivery apps (Swiggy/Blinkit) charge exorbitant delivery and surge fees on small essential items (e.g., a notebook, lab manual, printout, or medicine), often refusing campus hostel room delivery.
2. Local Shopkeeper Invisibility: Campus stationery stores, canteens, and local medical shops lack an affordable e-commerce presence to showcase their real-time catalog.
3. Unmonetized Daily Commutes: Hundreds of students travel daily between gates, markets, and hostels with empty backpacks and no way to monetize their routine routes.
4. Trust & Payment Security Risks: Informal peer requests often suffer from order cancellations, customer ghosting after purchase, or lack of payment confirmation.
```

---

### 4. Proposed Solution & Architecture
```text
Pick4Me resolves these challenges by creating a closed-loop hyperlocal marketplace and crowdsourced logistics ecosystem:
1. Local Storefront & Cataloging: Local merchants and student entrepreneurs register their shop profiles and catalog products with real prices, descriptions, and stock status.
2. Peer Commute Logistics: Students commuting past stores can accept delivery tasks on their route, earning fair distance-based rewards and speed bonuses.
3. Advance Escrow & 4-Digit Handover OTP: Customers pay in advance via UPI QR (7387157739@upi). Funds are held securely in Platform Escrow and automatically released to the deliverer's wallet ONLY when the deliverer verifies the customer's private 4-digit delivery OTP.
4. Dynamic Distance & Time SLA Engine: Calculates fair base fees across campus zones (0–1 km, 1–2.5 km, 2.5–5 km+), rewards superfast deliveries with +₹10 Speed Bonuses, penalizes excessive delays (-₹10), and supports 'Rush Mode' for urgent requirements.
```

---

### 5. Key Features & Innovations
```text
- 🏪 Amazon-Style Storefront & Multi-Item Cart: Real-time search, price filters, category tabs, and instant cart checkout.
- ⚡ Custom Errand Requests: Capability to request off-catalog items from any local shop with custom instructions.
- 🛡️ Advance Escrow Payment Safety: Complete protection against customer fraud and refusal.
- 🔑 Secure 4-Digit Handover OTP: Eliminates false delivery claims through physical handover verification.
- ⏱️ Dynamic Distance & SLA Speed Bonus:
    • Within Campus (0–1 km): ₹20 Base (25m SLA)
    • Near Gate Market (1–2.5 km): ₹35 Base (35m SLA)
    • Outer Town Market (2.5–5 km+): ₹55 Base (50m SLA)
    • Early Delivery: +₹10 Speed Bonus credited automatically to wallet
    • Urgent Rush Delivery (+₹15 Surge) with top-of-board priority
- 💰 Instant Wallet Settlement & Ledger: Real-time credit of product costs and rewards with complete transaction history.
- 🛡️ Role-Based Portals & KYC Verification: Dedicated interfaces for Customers, Commuters/Merchants, and an Admin Control Center with KYC verification toggles.
```

---

### 6. Technology Stack
```text
- Frontend: HTML5, Modern CSS3 (Variables, Flexbox/Grid, Responsive Media Queries), Vanilla JavaScript
- Backend: Python 3, Flask 3.0, Jinja2 Template Engine, Werkzeug Security Architecture
- Database: SQLite3 with relational foreign keys, strict constraints, and transactional consistency
- Security: PBKDF2:SHA256 Password Hashing, 4-Digit Handover OTP, Escrow Fund Isolation
- Payment Integration: UPI QR Code & VPA Gateway (7387157739@upi)
- Production WSGI & Cloud Hosting: Gunicorn WSGI Server, Render Cloud Service, Git/GitHub CI/CD
```

---

### 7. Scalability, Feasibility & Real-World Impact
```text
1. Zero Capital & Carbon Neutral: Eliminates dedicated delivery vehicle fleets by utilizing natural commuter pedestrian and bicycle traffic, achieving zero extra carbon emissions.
2. High Scalability: Easily replicable across 500+ Indian university campuses, engineering colleges, IT tech parks, and gated residential townships with zero hardware infrastructure costs.
3. Economic Empowerment: Provides local campus vendors with digital retail visibility while offering students a flexible, dignity-centered micro-earning platform during their routine commutes.
```

---

### 8. Verification & Test Suite Summary
```text
The system includes a fully automated 12-step end-to-end integration test suite (`test_workflow.py`) verifying:
✓ User Registration & KYC
✓ Store Setup & Product Cataloging
✓ Cart Management & Advance Escrow Payment
✓ Commuter Order Acceptance
✓ Delivery Progress Milestones
✓ 4-Digit Handover OTP Verification
✓ Automatic Wallet Payout with Speed Bonuses and Delay Penalty checks
✓ Admin Control Center & Platform Oversight
Test Result: 100% Passed.
```
