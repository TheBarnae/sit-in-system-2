from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
import sys
from datetime import datetime


def main():
    try:
        filename = 'test_reportlab_output.pdf'
        c = canvas.Canvas(filename, pagesize=landscape(letter))
        c.setFont('Helvetica', 12)
        c.drawString(1 * inch, 6 * inch, 'ReportLab test PDF')
        c.drawString(1 * inch, 5.5 * inch, f'Generated: {datetime.now().isoformat()}')
        c.save()
        print('PDF generated:', filename)
        return 0
    except Exception as e:
        print('ERROR:', e)
        return 2


if __name__ == '__main__':
    sys.exit(main())
