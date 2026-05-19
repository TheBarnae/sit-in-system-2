from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import os
from datetime import datetime

output = 'test_header_layout.pdf'
pagesize = landscape(letter)
width, height = pagesize
margin = 0.7 * inch

c = canvas.Canvas(output, pagesize=pagesize)

left_logo = os.path.join('static', 'images', 'CCS_UC.png')
right_logo = os.path.join('static', 'images', 'uclogo.png')
logo_w = 0.7 * inch
logo_h = 0.7 * inch
top_y = height - margin

# Draw left logo
if os.path.exists(left_logo):
    try:
        c.drawImage(left_logo, margin, top_y - logo_h, width=logo_w, height=logo_h, preserveAspectRatio=True, mask='auto')
    except Exception as e:
        print('left logo draw error', e)

# Draw right logo
if os.path.exists(right_logo):
    try:
        c.drawImage(right_logo, width - margin - logo_w, top_y - logo_h, width=logo_w, height=logo_h, preserveAspectRatio=True, mask='auto')
    except Exception as e:
        print('right logo draw error', e)

# University text
text_x = margin + logo_w + (0.12 * inch)
c.setFont('Helvetica-Bold', 14)
c.drawString(text_x, top_y - 6, 'University of Cebu')
c.setFont('Helvetica', 12)
c.drawString(text_x, top_y - 22, 'College of Computer Studies')

# Title
title = 'CCS Sit-in History Report'
c.setFont('Helvetica-Bold', 16)
center_x = margin + (width - 2 * margin) / 2
title_y = top_y - logo_h - (0.2 * inch)
c.drawCentredString(center_x, title_y, title)

# Filters and timestamp
c.setFont('Helvetica', 10)
filter_text = 'All records'
c.drawString(margin, title_y - (0.28 * inch), filter_text)
c.drawString(margin, title_y - (0.28 * inch) - 12, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# Draw table header to mimic layout
c.setFont('Helvetica-Bold', 10)
col_widths = [0.4, 2.0, 0.9, 1.0, 1.6, 0.8, 1.2, 1.2]
col_positions = [margin]
for w in col_widths[:-1]:
    col_positions.append(col_positions[-1] + w * inch)

# Start table below
start_y = title_y - (0.28 * inch) - 0.45 * inch
for idx, hdr in enumerate(['ID','Student','Course','Lab','Purpose','Status','Started','Ended']):
    c.drawString(col_positions[idx], start_y, hdr)

c.line(margin, start_y - 2, width - margin, start_y - 2)

# Draw a couple sample rows
c.setFont('Helvetica', 9)
rows = [
    ['1', 'Garcia, Nichole Anne Maraguinot', 'BSIT', 'Laboratory 524', 'Python', 'Completed', '2026-05-19 03:04', '2026-05-19 03:12'],
    ['2', 'Garcia, Sean Maraguinot', 'BSIT', 'LAB101', 'Java', 'Completed', '2026-03-25 19:25', '2026-03-25 19:26']
]

y = start_y - 14
for r in rows:
    for idx, val in enumerate(r):
        if idx in (6,7):
            c.drawRightString(col_positions[idx] + (col_widths[idx] * inch) - 6, y, val)
        else:
            text = val
            limit = [6,40,12,16,30,12,20,20][idx]
            if len(text) > limit:
                text = text[:limit-3] + '...'
            c.drawString(col_positions[idx], y, text)
    y -= 14

c.save()
print('Wrote', output)
