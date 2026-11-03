import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

class InvoicePDFGenerator:
    @staticmethod
    def generate_pdf(invoice) -> io.BytesIO:
        """
        Generates a professional corporate PDF invoice in memory using ReportLab.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        elements = []

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'InvoiceTitle',
            parent=styles['Heading1'],
            fontSize=24,
            leading=28,
            textColor=colors.HexColor('#1E3A8A'),
            spaceAfter=10
        )
        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#64748B'),
            spaceAfter=20
        )
        bold_style = ParagraphStyle('BoldText', parent=styles['Normal'], fontSize=11, fontName='Helvetica-Bold')

        # 1. Header
        elements.append(Paragraph("FleetOps Logistics SaaS", title_style))
        elements.append(Paragraph(f"INVOICE REF: {invoice.invoice_number} &nbsp;|&nbsp; Date: {invoice.created_at.strftime('%Y-%m-%d')}", subtitle_style))
        elements.append(Spacer(1, 10))

        # 2. Shipping Details Table
        shipment = invoice.shipment
        details_data = [
            [Paragraph("<b>Sender:</b>", styles['Normal']), Paragraph(shipment.sender_name, styles['Normal']),
             Paragraph("<b>Receiver:</b>", styles['Normal']), Paragraph(shipment.receiver_name, styles['Normal'])],
            [Paragraph("<b>Origin:</b>", styles['Normal']), Paragraph(shipment.origin_address, styles['Normal']),
             Paragraph("<b>Destination:</b>", styles['Normal']), Paragraph(shipment.destination_address, styles['Normal'])],
            [Paragraph("<b>Payload Weight:</b>", styles['Normal']), Paragraph(f"{shipment.payload_weight_kg} kg", styles['Normal']),
             Paragraph("<b>Status:</b>", styles['Normal']), Paragraph(f"<b>{shipment.status}</b>", styles['Normal'])],
        ]
        details_table = Table(details_data, colWidths=[100, 160, 100, 160])
        details_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8FAFC')),
            ('PADDING', (0,0), (-1,-1), 6),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#E2E8F0')),
        ]))
        elements.append(details_table)
        elements.append(Spacer(1, 20))

        # 3. Itemized Bill of Charges
        bill_data = [
            ["Charge Description", "Calculation Metric", "Amount (INR)"],
            ["Base Dispatch Fee", "Standard Logistics Base", f"₹ {invoice.base_charge:.2f}"],
            ["Distance Freight Charge", "Road Distance Toll & Fuel", f"₹ {invoice.distance_charge:.2f}"],
            ["Payload Weight Charge", f"{shipment.payload_weight_kg} kg @ Tier 1", f"₹ {invoice.weight_charge:.2f}"],
            ["TOTAL DUE", "All Taxes Included", f"₹ {invoice.total_amount:.2f}"]
        ]
        bill_table = Table(bill_data, colWidths=[240, 160, 120])
        bill_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2563EB')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('PADDING', (0,0), (-1,-1), 8),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1')),
            ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#EFF6FF')),
            ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
        ]))
        elements.append(bill_table)
        elements.append(Spacer(1, 30))

        # 4. Footer Note
        elements.append(Paragraph("Thank you for choosing FleetOps SaaS. For billing inquiries, contact billing@fleetops.local", subtitle_style))

        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer