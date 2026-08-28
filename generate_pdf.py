import os
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_pdf():
    pdf_path = "/Users/abhishekkanadje7/Desktop/Pick4Me_EnergyTech_Presentation.pdf"
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=landscape(letter),
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Colors
    c_slate = colors.HexColor('#0F172A')
    c_teal = colors.HexColor('#0D9488')
    c_teal_dark = colors.HexColor('#115E59')
    c_amber = colors.HexColor('#D97706')
    c_card_bg = colors.HexColor('#F8FAFC')
    c_border = colors.HexColor('#E2E8F0')

    style_cat = ParagraphStyle('Cat', fontName='Helvetica-Bold', fontSize=10, textColor=c_teal, leading=12)
    style_title = ParagraphStyle('Title', fontName='Helvetica-Bold', fontSize=22, textColor=c_slate, leading=26)
    style_h2 = ParagraphStyle('H2', fontName='Helvetica-Bold', fontSize=14, textColor=c_teal_dark, leading=18)
    style_body = ParagraphStyle('Body', fontName='Helvetica', fontSize=10.5, textColor=c_slate, leading=14)
    style_muted = ParagraphStyle('Muted', fontName='Helvetica', fontSize=9.5, textColor=colors.HexColor('#64748B'), leading=13)

    story = []

    def make_slide(cat, title, content_table):
        s = []
        s.append(Paragraph(cat.upper(), style_cat))
        s.append(Paragraph(title, style_title))
        s.append(Spacer(1, 12))
        s.append(content_table)
        s.append(PageBreak())
        return s

    # SLIDE 1: Title
    s1_data = [
        [Paragraph("<font size=28 color='#0F172A'><b>Pick4Me</b></font><br/><font size=16 color='#0D9488'><b>Zero-Emission Hyperlocal Logistics & Smart Campus Supply Network</b></font><br/><br/><font color='#64748B'>Decarbonizing Last-Mile Campus Mobility through Crowdsourced Foot Traffic & 2-Stage Escrow Protocols</font>", style_body)],
        [Paragraph("<b>⚡ Challenge Track:</b> Smart Buildings & Clean Campus Mobility<br/><b>👥 Project Lead:</b> Abhishek Kanadje & Team (abhishekkanadje7@gmail.com)<br/><b>🌐 Live Application:</b> https://pick4me-l868.onrender.com", style_body)]
    ]
    t1 = Table(s1_data, colWidths=[720])
    t1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), c_card_bg),
        ('BOX', (0,0), (-1,-1), 1.5, c_teal),
        ('PADDING', (0,0), (-1,-1), 24),
        ('ROUNDEDCORNERS', [10, 10, 10, 10])
    ]))
    story.extend(make_slide("YUVA YODHA ENERGY TECH HACKATHON 2026", "Project Presentation", t1))

    # SLIDE 2: Problem
    s2_data = [
        [
            Paragraph("<b>🚗 High Fuel Consumption</b><br/><br/>Commercial quick-commerce fleets burn petrol for single low-value deliveries (stationery, snacks, medicines), creating excessive carbon emissions.", style_body),
            Paragraph("<b>🏭 Campus Congestion & Noise</b><br/><br/>Motorized delivery two-wheelers cause noise pollution and traffic inside academic zones and residential hostel premises.", style_body),
            Paragraph("<b>💸 Invisibility & High Surge</b><br/><br/>High delivery fees penalize students, while local campus shops remain invisible without an affordable digital catalog.", style_body)
        ]
    ]
    t2 = Table(s2_data, colWidths=[235, 235, 235])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), c_card_bg),
        ('BOX', (0,0), (-1,-1), 1, c_border),
        ('PADDING', (0,0), (-1,-1), 16),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ROUNDEDCORNERS', [8, 8, 8, 8])
    ]))
    story.extend(make_slide("PROBLEM STATEMENT", "Inefficient Last-Mile Logistics in Campus & Building Complexes", t2))

    # SLIDE 3: Vision
    s3_data = [
        [
            Paragraph("<b>🌱 The Green Crowdsourcing Hypothesis</b><br/><br/>Thousands of students walk daily between gates, libraries, and hostels with empty bags.<br/><br/>Pick4Me monetizes these existing walking routes to achieve <b>100% Zero-Emission Deliveries</b> without adding a single motorized vehicle.", style_body),
            Paragraph("<b>⚡ Alignment with Energy Tech & Smart Buildings</b><br/><br/>• Zero Capital Expenditure on delivery fleets.<br/>• Eliminates localized CO2 emissions in campus air.<br/>• Energy efficient intra-building micro-supply chain.<br/>• Circular campus economy benefiting local stores and student commuters.", style_body)
        ]
    ]
    t3 = Table(s3_data, colWidths=[355, 355])
    t3.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), c_card_bg),
        ('BOX', (0,0), (-1,-1), 1, c_teal),
        ('PADDING', (0,0), (-1,-1), 18),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ROUNDEDCORNERS', [8, 8, 8, 8])
    ]))
    story.extend(make_slide("VISION & ALIGNMENT", "Decarbonizing Campus Mobility Through Human Routine Transit", t3))

    # SLIDE 4: Solution Ecosystem
    s4_data = [
        [
            Paragraph("<b>🛍️ Customer A (Buyer)</b><br/><br/>Orders from registered campus shops or posts custom errands with advance escrow safety.", style_body),
            Paragraph("<b>🏪 Store Merchant</b><br/><br/>Catalogs items and automatically receives 100% item payment upon shop counter pickup.", style_body),
            Paragraph("<b>🚴 Customer B (Commuter)</b><br/><br/>Claims delivery along routine walking route and receives reward into personal wallet.", style_body),
            Paragraph("<b>🛡️ Admin Escrow</b><br/><br/>Holds 100% funds securely and executes 2-stage automated payouts upon OTP verification.", style_body)
        ]
    ]
    t4 = Table(s4_data, colWidths=[175, 175, 175, 175])
    t4.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), c_card_bg),
        ('BOX', (0,0), (-1,-1), 1, c_border),
        ('PADDING', (0,0), (-1,-1), 14),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ROUNDEDCORNERS', [8, 8, 8, 8])
    ]))
    story.extend(make_slide("SOLUTION OVERVIEW", "The Pick4Me 3-Party Peer Commerce Ecosystem", t4))

    # SLIDE 5: Workflow
    s5_data = [
        [Paragraph("<b>Step 1: Order & Advance Payment</b>", style_h2), Paragraph("Customer A orders lab manual and pays ₹120 item + ₹35 reward = ₹155 to Admin Escrow.", style_body)],
        [Paragraph("<b>Step 2: Commuter Claim</b>", style_h2), Paragraph("Customer B (student walking near shop) claims task on 'Deliver & Earn' board.", style_body)],
        [Paragraph("<b>Step 3: Stage 1 Shop Handover</b>", style_h2), Paragraph("Customer B picks up at shop. Shopkeeper confirms & ₹120 item cost is instantly credited to Shopkeeper's Wallet!", style_body)],
        [Paragraph("<b>Step 4: Stage 2 Customer Handover</b>", style_h2), Paragraph("Customer B delivers to room. Customer A shares 4-digit OTP. Customer B enters OTP & ₹35 (+Speed Bonus) is credited to Customer B's Wallet!", style_body)]
    ]
    t5 = Table(s5_data, colWidths=[240, 470])
    t5.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), c_card_bg),
        ('BOX', (0,0), (-1,-1), 1, c_teal),
        ('PADDING', (0,0), (-1,-1), 12),
        ('GRID', (0,0), (-1,-1), 0.5, c_border),
        ('ROUNDEDCORNERS', [8, 8, 8, 8])
    ]))
    story.extend(make_slide("WORKFLOW", "2-Stage Autonomous Escrow Settlement Architecture", t5))

    # SLIDE 6: Environmental Impact
    s6_data = [
        [
            Paragraph("<font size=20 color='#0D9488'><b>0.15 kg</b></font><br/><b>CO2 Saved Per Delivery</b><br/><br/>Compared to fossil fuel two-wheelers.", style_body),
            Paragraph("<font size=20 color='#D97706'><b>54.75 Tons</b></font><br/><b>Annual CO2 Avoided</b><br/><br/>Per average campus with 1,000 daily deliveries.", style_body),
            Paragraph("<font size=20 color='#0D9488'><b>18,000+ L</b></font><br/><b>Petrol Conserved</b><br/><br/>Zero fossil fuel consumed on daily errands.", style_body),
            Paragraph("<font size=20 color='#0F172A'><b>100%</b></font><br/><b>Zero Extra Vehicles</b><br/><br/>Zero fleet noise or traffic congestion.", style_body)
        ]
    ]
    t6 = Table(s6_data, colWidths=[175, 175, 175, 175])
    t6.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), c_card_bg),
        ('BOX', (0,0), (-1,-1), 1, c_border),
        ('PADDING', (0,0), (-1,-1), 16),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ROUNDEDCORNERS', [8, 8, 8, 8])
    ]))
    story.extend(make_slide("ENERGY & ENVIRONMENTAL IMPACT", "Measurable Decarbonization & Carbon Savings Metrics", t6))

    # SLIDE 7: Conclusion
    s7_data = [
        [Paragraph("<font size=16 color='#0F172A'><b>Pick4Me — Transforming Routine Commutes into Zero-Emission Deliveries</b></font><br/><br/><b>👥 Project Lead:</b> Abhishek Kanadje & Team<br/><b>📧 Contact:</b> abhishekkanadje7@gmail.com<br/><b>🌐 Live Application Demo:</b> https://pick4me-l868.onrender.com<br/><b>📂 Source Code:</b> https://github.com/abhishekkanadje7/Pick4Me<br/><br/>✓ 100% Automated Tests Passed (`test_workflow.py`)<br/>✓ Ready for University & Smart Township Deployments", style_body)]
    ]
    t7 = Table(s7_data, colWidths=[720])
    t7.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), c_card_bg),
        ('BOX', (0,0), (-1,-1), 1.5, c_teal),
        ('PADDING', (0,0), (-1,-1), 20),
        ('ROUNDEDCORNERS', [8, 8, 8, 8])
    ]))
    story.extend(make_slide("CONCLUSION & LINKS", "Project Summary & Live Verification", t7))

    doc.build(story)
    print(f"PDF Presentation saved to: {pdf_path}")

if __name__ == '__main__':
    generate_pdf()
