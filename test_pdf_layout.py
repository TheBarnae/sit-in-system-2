from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import os
from datetime import datetime

width, height = landscape(letter)
margin = 0.7 * inch

buffer_file = 'test_sit_in_report.pdf'
pdf = canvas.Canvas(buffer_file, pagesize=landscape(letter))

# header
logo_path = os.path.join('static', 'images', 'CCS_UC.png')
logo_w = 0.6 * inch
logo_h = 0.6 * inch
top_y = height - margin
try:
    if os.path.exists(logo_path):
        pdf.drawImage(logo_path, margin, top_y - logo_h, width=logo_w, height=logo_h, preserveAspectRatio=True, mask='auto')
except Exception:
    pass

text_x = margin + logo_w + (0.15 * inch)
pdf.setFont('Helvetica-Bold', 14)
pdf.drawString(text_x, top_y - 6, 'University of Cebu')
pdf.setFont('Helvetica', 12)
pdf.drawString(text_x, top_y - 22, 'College of Computer Studies')

# title
pdf.setFont('Helvetica-Bold', 16)
center_x = margin + (width - 2 * margin) / 2
title_y = top_y - logo_h - (0.25 * inch)
pdf.drawCentredString(center_x, title_y, 'CCS Sit-in History Report')

# filters
pdf.setFont('Helvetica', 10)
filter_y = title_y - (0.25 * inch)
pdf.drawString(margin, filter_y, 'All records')
pdf.drawString(margin, filter_y - 12, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# columns
pdf.setFont('Helvetica-Bold', 10)
headers = ['ID', 'Student', 'Course', 'Lab', 'Purpose', 'Status', 'Started', 'Ended']
col_widths = [0.4, 2.0, 0.9, 1.0, 1.6, 0.8, 1.2, 1.2]
col_positions = [margin]
for w in col_widths[:-1]:
    col_positions.append(col_positions[-1] + w * inch)
col_rights = [col_positions[i] + col_widths[i] * inch - 6 for i in range(len(col_widths))]

# start table
y = filter_y - (0.45 * inch)
for idx, header in enumerate(headers):
    pdf.drawString(col_positions[idx], y, header)
pdf.line(margin, y - 2, width - margin, y - 2)
y -= 16

pdf.setFont('Helvetica', 8)
# sample rows
rows = [
    {'session_no': 4, 'full_name': 'Garcia, Nichole Anne Maraguinot', 'course':'BSIT', 'lab_label':'Laboratory 530', 'purpose':'ASP.Net', 'status':'Completed', 'started_at':'2026-05-19 03:26', 'ended_at':'2026-05-19 03:27'},
    {'session_no': 3, 'full_name': 'Garcia, Nichole Maraguinot', 'course':'BSIT', 'lab_label':'Laboratory 524', 'purpose':'General use', 'status':'Completed', 'started_at':'2026-05-19 03:14', 'ended_at':'2026-05-19 03:16'},
]

max_chars = [6, 40, 12, 16, 30, 12, 20, 20]
for record in rows:
    values = [str(record.get('session_no') or ''), record.get('full_name'), record.get('course'), record.get('lab_label'), record.get('purpose'), record.get('status'), record.get('started_at'), record.get('ended_at')]
    for idx, value in enumerate(values):
        text = str(value or '')
        limit = max_chars[idx] if idx < len(max_chars) else 40
        if len(text) > limit:
            text = text[: max(0, limit - 3)] + '...'
        if idx in (6,7):
            pdf.drawRightString(col_rights[idx], y, text)
        else:
            pdf.drawString(col_positions[idx], y, text)
    y -= 12

pdf.setFont('Helvetica-Bold', 10)
pdf.drawString(margin, y - 10, f"Total records: {len(rows)} | Completed: {len(rows)} | Active: 0")

pdf.save()
print('Wrote', buffer_file)
