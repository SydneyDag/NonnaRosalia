from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from datetime import datetime

def generate_invoice_pdf(order, customer, filename):
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Header
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30
    )
    story.append(Paragraph("Invoice", header_style))
    
    # Customer and Order Information
    info_style = ParagraphStyle(
        'CustomerInfo',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=12
    )
    
    story.append(Paragraph(f"Customer: {customer.name}", info_style))
    story.append(Paragraph(f"Address: {customer.address}", info_style))
    story.append(Paragraph(f"Order Date: {order.order_date.strftime('%Y-%m-%d')}", info_style))
    story.append(Paragraph(f"Delivery Date: {order.delivery_date.strftime('%Y-%m-%d')}", info_style))
    story.append(Spacer(1, 20))

    # Order Details Table
    data = [
        ['Description', 'Amount'],
        ['Total Cases', str(order.total_cases)],
        ['Total Cost', f"${float(order.total_cost):.2f}"],
        ['Payment Received', f"${float(order.payment_received):.2f}"],
        ['Balance Due', f"${float(order.total_cost - order.payment_received):.2f}"]
    ]

    table = Table(data, colWidths=[4*inch, 2*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(table)

    # Payment Details
    story.append(Spacer(1, 20))
    story.append(Paragraph("Payment Details:", styles['Heading3']))
    payment_data = [
        ['Payment Type', 'Amount'],
        ['Cash', f"${float(order.payment_cash):.2f}"],
        ['Check', f"${float(order.payment_check):.2f}"],
        ['Credit', f"${float(order.payment_credit):.2f}"]
    ]
    payment_table = Table(payment_data, colWidths=[4*inch, 2*inch])
    payment_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(payment_table)

    doc.build(story)

def generate_report_pdf(daily_data, summary, start_date, end_date, territory, filename):
    doc = SimpleDocTemplate(filename, pagesize=letter, leftMargin=36, rightMargin=36)
    styles = getSampleStyleSheet()
    story = []

    # Header
    header_style = ParagraphStyle(
        'CustomHeader',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30
    )
    title = "Sales Report"
    if territory:
        title += f" - {territory}"
    story.append(Paragraph(title, header_style))
    
    # Date Range
    date_style = ParagraphStyle(
        'DateRange',
        parent=styles['Normal'],
        fontSize=12,
        spaceAfter=20
    )
    story.append(Paragraph(
        f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}", 
        date_style
    ))

    # Summary Table
    summary_data = [
        ['Metric', 'Value'],
        ['Total Orders', str(summary['total_orders'])],
        ['Total Cases', str(summary['total_cases'])],
        ['Total Revenue', f"${summary['total_revenue']:.2f}"],
        ['Total Payments', f"${summary['total_payments']:.2f}"],
        ['Outstanding Balance', f"${summary['outstanding_balance']:.2f}"]
    ]

    summary_table = Table(summary_data, colWidths=[4*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 20))

    # Daily Totals Table
    if daily_data:
        story.append(Paragraph("Daily Totals:", styles['Heading3']))
        order_data = [[
            'Date', 'Cases', 'Cost', 'Cash', 'Check', 'Credit', 'Total Paid'
        ]]
        
        for day in daily_data:
            order_data.append([
                day['order_date'].split('T')[0],
                str(day['total_cases']),
                f"${float(day['total_cost']):.2f}",
                f"${float(day['payment_cash']):.2f}",
                f"${float(day['payment_check']):.2f}",
                f"${float(day['payment_credit']):.2f}",
                f"${float(day['payment_received']):.2f}"
            ])

        col_widths = [1*inch, 0.8*inch, 1*inch, 1*inch, 1*inch, 1*inch, 1*inch]
        order_table = Table(order_data, colWidths=col_widths)
        order_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(order_table)

    doc.build(story)
