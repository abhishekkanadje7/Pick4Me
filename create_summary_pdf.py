import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY

def build_pdf(output_path):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Premium Brand Palette
    c_primary = colors.HexColor('#0D9488')       # Deep Teal
    c_primary_dark = colors.HexColor('#0F766E')
    c_primary_light = colors.HexColor('#F0FDFA')  # Subtle Teal tint
    c_accent = colors.HexColor('#D97706')        # Warm Amber
    c_slate = colors.HexColor('#0F172A')         # Dark Slate
    c_body = colors.HexColor('#334155')          # Body Slate
    c_muted = colors.HexColor('#64748B')         # Muted
    c_card_bg = colors.HexColor('#F8FAFC')       # Card Light Gray
    c_border = colors.HexColor('#E2E8F0')        # Border line
    c_success_bg = colors.HexColor('#ECFDF5')
    c_success_text = colors.HexColor('#065F46')

    # Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        fontName='Helvetica-Bold',
        fontSize=22,
        textColor=c_slate,
        leading=26,
        alignment=TA_LEFT
    )
    subtitle_style = ParagraphStyle(
        'DocSub',
        fontName='Helvetica-Bold',
        fontSize=12,
        textColor=c_primary,
        leading=16,
        alignment=TA_LEFT
    )
    sec_heading = ParagraphStyle(
        'SecHeading',
        fontName='Helvetica-Bold',
        fontSize=13,
        textColor=c_slate,
        leading=17,
        spaceBefore=10,
        spaceAfter=4
    )
    body_style = ParagraphStyle(
        'Body',
        fontName='Helvetica',
        fontSize=9,
        textColor=c_body,
        leading=12.5,
        alignment=TA_LEFT
    )
    body_bold = ParagraphStyle(
        'BodyBold',
        fontName='Helvetica-Bold',
        fontSize=9,
        textColor=c_slate,
        leading=12.5
    )
    card_title = ParagraphStyle(
        'CardTitle',
        fontName='Helvetica-Bold',
        fontSize=10,
        textColor=c_primary_dark,
        leading=13
    )
    table_cell = ParagraphStyle(
        'TableCell',
        fontName='Helvetica',
        fontSize=8.5,
        textColor=c_body,
        leading=11.5
    )
    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        fontName='Helvetica-Bold',
        fontSize=8.5,
        textColor=c_slate,
        leading=11.5
    )
    meta_style = ParagraphStyle(
        'Meta',
        fontName='Helvetica',
        fontSize=8.5,
        textColor=c_muted,
        leading=12
    )

    story = []

    # ==========================================
    # HEADER BANNER & PROJECT IDENTITY
    # ==========================================
    header_data = [
        [
            Paragraph("<b>PICK4ME 🛍️🚴</b>", title_style),
            Paragraph("<b>EXECUTIVE PROJECT SUMMARY</b><br/><font color='#64748B'>Academic & Hackathon Presentation</font>", ParagraphStyle('HRight', fontName='Helvetica-Bold', fontSize=10, textColor=c_primary, alignment=TA_RIGHT, leading=13))
        ],
        [
            Paragraph("Hyperlocal Campus Marketplace & Crowdsourced Peer Commute Delivery Platform", subtitle_style),
            Paragraph("<b>Developer:</b> Abhishek Kanadje<br/><b>Live App:</b> pick4me-l868.onrender.com", ParagraphStyle('HRight2', fontName='Helvetica', fontSize=8.5, textColor=c_muted, alignment=TA_RIGHT, leading=11))
        ]
    ]
    header_table = Table(header_data, colWidths=[360, 180])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=1.5, color=c_primary, spaceBefore=4, spaceAfter=8))

    # ==========================================
    # SECTION 1: PROBLEM STATEMENT & CORE SOLUTION
    # ==========================================
    story.append(Paragraph("1. PROBLEM STATEMENT VS. PICK4ME SOLUTION", sec_heading))
    
    comp_data = [
        [
            Paragraph("<b>Campus & Hostel Pain Points (Existing System)</b>", ParagraphStyle('C1H', fontName='Helvetica-Bold', fontSize=8.5, textColor=colors.HexColor('#991B1B'))),
            Paragraph("<b>Pick4Me Innovations (Engineered Solution)</b>", ParagraphStyle('C2H', fontName='Helvetica-Bold', fontSize=8.5, textColor=c_primary_dark))
        ],
        [
            Paragraph("• <b>High Fees & Minimum Orders:</b> Apps like Blinkit/Swiggy charge ₹30-₹60 delivery/surge fees on small essentials (₹10 pen, Xerox, lab kit).<br/>• <b>Gate Restrictions:</b> Outside delivery riders are blocked at main security gates; students walk late at night to fetch orders.<br/>• <b>Invisible Local Vendors:</b> Campus canteens, stationery and Xerox hubs lack an online catalog to showcase real-time stock.<br/>• <b>Unmonetized Daily Commutes:</b> Hundreds of students walk daily between gates and hostels with zero earnings opportunities.", table_cell),
            Paragraph("• <b>Dynamic Micro-Fees (₹20-₹35):</b> Affordable, fair distance-based fees with zero minimum order quantity limits.<br/>• <b>Direct Doorstep Handover:</b> Fellow peer students deliver directly to hostel rooms, bypassing gate bans.<br/>• <b>Zero-Commission Storefronts:</b> Campus shops list their full inventory online, receiving instant sales without middlemen.<br/>• <b>Zero-Carbon Foot Traffic Deliveries:</b> Converts routine daily walking commutes into dignified micro-earnings (₹200-₹500/day).", table_cell)
        ]
    ]
    comp_table = Table(comp_data, colWidths=[270, 270])
    comp_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#FEF2F2')),
        ('BACKGROUND', (1,0), (1,-1), c_primary_light),
        ('BOX', (0,0), (-1,-1), 1, c_border),
        ('INNERGRID', (0,0), (-1,-1), 0.5, c_border),
        ('PADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(comp_table)
    story.append(Spacer(1, 8))

    # ==========================================
    # SECTION 2: 3-PARTY PEER LOGISTICS & 2-STAGE ESCROW PROTOCOL
    # ==========================================
    story.append(Paragraph("2. 3-PARTY PEER LOGISTICS & ADVANCE ESCROW PROTOCOL", sec_heading))
    
    escrow_desc = (
        "<b>Zero Fraud Architecture:</b> The buyer pays 100% upfront (Product Cost + Delivery Fee) via UPI QR into "
        "<b>Platform Escrow</b>. Funds are securely locked and disbursed in two automated verification stages:"
    )
    story.append(Paragraph(escrow_desc, body_style))
    story.append(Spacer(1, 4))

    workflow_data = [
        [
            Paragraph("<b>Stage 1: Store Pickup Handover</b>", card_title),
            Paragraph("<b>Stage 2: Customer Handover & OTP Verification</b>", card_title)
        ],
        [
            Paragraph("• Peer commuter arrives at the campus merchant store.<br/>• Commuter inspects and collects the ordered items.<br/>• Shopkeeper confirms physical handover on their dashboard.<br/>• <b>Automatic Payout 1:</b> System instantly transfers 100% of the Product Amount directly to the <b>Shopkeeper's Wallet</b>.", table_cell),
            Paragraph("• Commuter reaches buyer's hostel room.<br/>• Buyer physically verifies products and gives secret <b>4-digit Delivery OTP</b>.<br/>• Commuter inputs OTP in app for cryptographic verification.<br/>• <b>Automatic Payout 2:</b> System transfers Delivery Fee + <b>Speed Bonus</b> directly to <b>Commuter's Wallet</b>.", table_cell)
        ]
    ]
    workflow_table = Table(workflow_data, colWidths=[270, 270])
    workflow_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), c_card_bg),
        ('BOX', (0,0), (-1,-1), 1, c_border),
        ('INNERGRID', (0,0), (-1,-1), 0.5, c_border),
        ('PADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(workflow_table)
    story.append(Spacer(1, 8))

    # ==========================================
    # SECTION 3: DYNAMIC SLA & SPEED BONUS ENGINE
    # ==========================================
    story.append(Paragraph("3. DYNAMIC DISTANCE SLA & SPEED BONUS ENGINE", sec_heading))
    
    sla_data = [
        [Paragraph("<b>Delivery Zone</b>", table_cell_bold), Paragraph("<b>Distance Range</b>", table_cell_bold), Paragraph("<b>Base Fee</b>", table_cell_bold), Paragraph("<b>Target SLA</b>", table_cell_bold), Paragraph("<b>Incentives & Rules</b>", table_cell_bold)],
        [Paragraph("Within Campus", table_cell), Paragraph("0.0 – 1.0 km", table_cell), Paragraph("₹20.00", table_cell_bold), Paragraph("25 Mins", table_cell), Paragraph("Hostel-to-hostel or library delivery", table_cell)],
        [Paragraph("Near Gate Market", table_cell), Paragraph("1.0 – 2.5 km", table_cell), Paragraph("₹35.00", table_cell_bold), Paragraph("35 Mins", table_cell), Paragraph("Main gate shops and student plaza", table_cell)],
        [Paragraph("Outer Town Market", table_cell), Paragraph("2.5 – 5.0+ km", table_cell), Paragraph("₹55.00", table_cell_bold), Paragraph("50 Mins", table_cell), Paragraph("External city pharmacies & bookstores", table_cell)],
        [Paragraph("<b>Speed Bonus</b>", table_cell_bold), Paragraph("Any Zone", table_cell), Paragraph("<b>+₹10.00</b>", table_cell_bold), Paragraph("Early Arrival", table_cell), Paragraph("Auto-awarded for delivering before SLA window", table_cell)],
        [Paragraph("<b>Rush Delivery</b>", table_cell_bold), Paragraph("Any Zone", table_cell), Paragraph("<b>+₹15.00</b>", table_cell_bold), Paragraph("Fast-Tracked", table_cell), Paragraph("Priority surge placing order at top of tasks board", table_cell)]
    ]
    sla_table = Table(sla_data, colWidths=[105, 85, 75, 75, 200])
    sla_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F1F5F9')),
        ('BOX', (0,0), (-1,-1), 1, c_border),
        ('INNERGRID', (0,0), (-1,-1), 0.5, c_border),
        ('PADDING', (0,0), (-1,-1), 4),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(sla_table)
    story.append(Spacer(1, 8))

    # ==========================================
    # SECTION 4: KEY PLATFORM INNOVATIONS
    # ==========================================
    story.append(Paragraph("4. KEY PLATFORM INNOVATIONS & USER EXPERIENCE", sec_heading))
    
    feats_data = [
        [
            Paragraph("<b>📞 P2P In-App Live Audio Calling</b>", card_title),
            Paragraph("<b>⭐ Verified Order Feedback & Star Rating</b>", card_title)
        ],
        [
            Paragraph("• Integrated in-browser calling modal powered by <b>HTML5 Web Audio API</b>.<br/>• Realistic dual-tone telephone ringing synthesizer (440Hz+480Hz).<br/>• Live active call timer (`00:15`), Mute microphone, Speaker, and End Call.<br/>• Seamless 1-click fallback to direct SIM Phone (`tel:`) and WhatsApp chat.", table_cell),
            Paragraph("• Interactive 1 to 5-star rating widget enabled immediately upon delivery.<br/>• Allows customers to review speed, handling quality, and courier behavior.<br/>• Displays permanent <b>✓ Verified Campus Delivery Feedback</b> badge.<br/>• Builds campus trust and driver reputational scoring.", table_cell)
        ],
        [
            Paragraph("<b>🛒 Multi-Store Cart & Custom Errands</b>", card_title),
            Paragraph("<b>💰 Commuter Wallet & Audit Ledger</b>", card_title)
        ],
        [
            Paragraph("• Amazon/Blinkit-style catalog across 5 campus store categories.<br/>• Live search, price sorting, real-time stock tags, and cart subtotals.<br/>• <b>Custom Errand Generator:</b> Request off-catalog items from any unlisted local shop with custom instructions and estimated budget.", table_cell),
            Paragraph("• Real-time digital balance for commuters and store merchants.<br/>• Immutable transaction ledger with unique IDs (`#TXN-xxx`).<br/>• Automated tracking of product sales, delivery rewards, and speed bonuses.<br/>• Withdrawal capability linked to registered UPI VPA (`@upi`).", table_cell)
        ]
    ]
    feats_table = Table(feats_data, colWidths=[270, 270])
    feats_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), c_card_bg),
        ('BOX', (0,0), (-1,-1), 1, c_border),
        ('INNERGRID', (0,0), (-1,-1), 0.5, c_border),
        ('PADDING', (0,0), (-1,-1), 5),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(feats_table)
    story.append(Spacer(1, 8))

    # ==========================================
    # SECTION 5: TECHNICAL STACK & SYSTEM FILES
    # ==========================================
    story.append(Paragraph("5. TECHNICAL ARCHITECTURE & COMPONENT STACK", sec_heading))
    
    tech_data = [
        [Paragraph("<b>Layer</b>", table_cell_bold), Paragraph("<b>Technology</b>", table_cell_bold), Paragraph("<b>Implementation Role</b>", table_cell_bold)],
        [Paragraph("Backend Framework", table_cell), Paragraph("Python 3.11+, Flask 3.0", table_cell_bold), Paragraph("Core MVC architecture, session handling, dynamic pricing & APIs", table_cell)],
        [Paragraph("Cloud Database", table_cell), Paragraph("PostgreSQL (Neon.tech)", table_cell_bold), Paragraph("24/7 Persistent Serverless Cloud Postgres (Zero data loss)", table_cell)],
        [Paragraph("Local DB Fallback", table_cell), Paragraph("SQLite3 (`pick4me.db`)", table_cell_bold), Paragraph("Local development engine with automatic relational schema adaptation", table_cell)],
        [Paragraph("Frontend UI/UX", table_cell), Paragraph("HTML5, Modern CSS3, JS", table_cell_bold), Paragraph("Custom responsive design system, Flexbox/Grid, zero bulky frameworks", table_cell)],
        [Paragraph("Audio Synthesizer", table_cell), Paragraph("Web Audio API", table_cell_bold), Paragraph("Client-side dual oscillator telephonic ringtone and call timer", table_cell)],
        [Paragraph("Security & Auth", table_cell), Paragraph("PBKDF2:SHA256, 4-digit OTP", table_cell_bold), Paragraph("Werkzeug cryptographic password hashing and two-factor delivery code", table_cell)],
        [Paragraph("WSGI Server", table_cell), Paragraph("Gunicorn WSGI", table_cell_bold), Paragraph("Production-grade WSGI web worker orchestration on Render Cloud", table_cell)]
    ]
    tech_table = Table(tech_data, colWidths=[110, 150, 280])
    tech_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#F1F5F9')),
        ('BOX', (0,0), (-1,-1), 1, c_border),
        ('INNERGRID', (0,0), (-1,-1), 0.5, c_border),
        ('PADDING', (0,0), (-1,-1), 3.5),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(tech_table)
    story.append(Spacer(1, 8))

    # ==========================================
    # SECTION 6: RELATIONAL DATABASE & REPOSITORY FILES
    # ==========================================
    story.append(Paragraph("6. DATABASE SCHEMA & REPOSITORY STRUCTURE", sec_heading))

    db_text = (
        "<b>6 Core Relational Tables:</b> <b>1) users</b> (id, name, email, phone, role, wallet_balance, is_verified); "
        "<b>2) shops</b> (id, owner_id, shop_name, category, address, phone, is_active); "
        "<b>3) products</b> (id, shop_id, name, category, price, in_stock); "
        "<b>4) cart_items</b> (id, user_id, product_id, quantity); "
        "<b>5) orders</b> (id, customer_id, commuter_id, shop_id, product_amount, delivery_fee, total_amount, pickup_otp, delivery_otp, status, feedback_rating, feedback_comment); "
        "<b>6) wallet_transactions</b> (id, user_id, order_id, amount, type, description)."
    )
    story.append(Paragraph(db_text, meta_style))
    story.append(Spacer(1, 4))

    files_text = (
        "<b>Key Source Files:</b> `app.py` (Core controller, APIs, calling & feedback routes); `database.py` (Dual Neon Postgres/SQLite adapter); "
        "`templates/order_details.html` (2-stage timeline, live calling modal & review form); `templates/admin_dashboard.html` (KYC control & catalog seeder); "
        "`static/css/style.css` (Bespoke styling & call animations); `Procfile` & `vercel.json` (Multi-cloud deployment descriptors)."
    )
    story.append(Paragraph(files_text, meta_style))
    story.append(Spacer(1, 8))

    # ==========================================
    # SECTION 7: REAL-WORLD IMPACT & VERIFICATION
    # ==========================================
    story.append(Paragraph("7. IMPACT METRICS & LIVE ACCESS", sec_heading))

    impact_data = [
        [
            Paragraph("<b>🌱 100% Carbon-Neutral Mobility</b><br/>Zero motorized fleet overhead. Converts natural student pedestrian and cycle foot traffic into a high-speed campus logistics network.", table_cell),
            Paragraph("<b>💼 Dignified Student Micro-Earnings</b><br/>Enables commuting hostelers to earn ₹200–₹500 daily during regular routine transit without fixed hours or shifts.", table_cell),
            Paragraph("<b>🌐 Live Verified Deployment</b><br/><b>App:</b> https://pick4me-l868.onrender.com<br/><b>Admin:</b> abhishekkanadje7@gmail.com<br/><b>Pass:</b> Abhi*2007 (KYC & Escrow oversight)", table_cell)
        ]
    ]
    impact_table = Table(impact_data, colWidths=[180, 180, 180])
    impact_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), c_card_bg),
        ('BOX', (0,0), (-1,-1), 1, c_border),
        ('INNERGRID', (0,0), (-1,-1), 0.5, c_border),
        ('PADDING', (0,0), (-1,-1), 5),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    story.append(impact_table)

    # Build document
    doc.build(story)
    print(f"✓ PDF successfully generated at: {output_path}")

if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else "/Users/abhishekkanadje7/Desktop/Pick4Me_Project_Summary.pdf"
    build_pdf(target)
