"""Generate Spectra HoliParty PDF tickets with name, ticket ID, and amount highlighted."""
import io
import os
import tempfile
from fpdf import FPDF
from PIL import Image


def generate_ticket_pdf(booking):
    """Generate a PDF ticket for the booking. Returns BytesIO buffer."""
    qr_path = None
    try:
        from utils.qr_utils import generate_qr
        qr_buf = generate_qr(booking.get('ticket_id', 'N/A'))
        qr_img = Image.open(qr_buf)
        fd, qr_path = tempfile.mkstemp(suffix='.png')
        os.close(fd)
        qr_img.save(qr_path, format='PNG')
    except Exception:
        if qr_path and os.path.exists(qr_path):
            try:
                os.unlink(qr_path)
            except Exception:
                pass
        qr_path = None

    pass_type_labels = {
        'entry': 'Entry Only',
        'entry_starter': 'Entry + Starter',
        'entry_starter_lunch': 'Entry + Starter + Lunch'
    }
    pass_label = pass_type_labels.get(booking.get('pass_type', 'entry'), 'Entry Only')
    amount = booking.get('amount')
    if amount is None:
        # Fallback logic if amount is missing
        pricing = booking.get('pricing', {})
        pass_type = booking.get('pass_type', 'entry')
        price_per_pass = 200  # Absolute default
        if pass_type == 'entry':
            price_per_pass = pricing.get('entry_pass', 200)
        elif pass_type == 'entry_starter':
            price_per_pass = pricing.get('entry_plus_starter', 349)
        elif pass_type == 'entry_starter_lunch':
            price_per_pass = pricing.get('entry_plus_starter_lunch', 499)
        amount = booking.get('passes', 1) * price_per_pass
    venue = booking.get('venue', 'Kunjachaya, Bhadreswar')

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Header - Spectra HoliParty
    pdf.set_font("Arial", 'B', 18)
    pdf.set_text_color(255, 47, 146)
    pdf.cell(0, 12, txt="SPECTRA HOLIPARTY 2026", ln=1, align='C')
    pdf.set_font("Arial", '', 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 8, txt="Entry Ticket", ln=1, align='C')
    pdf.ln(5)

    # Ticket border effect (thick line)
    pdf.set_draw_color(255, 47, 146)
    pdf.set_line_width(1)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(8)

    # Name - prominent
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 8, txt=f"Name: {booking['name']}", ln=1)
    pdf.set_font("Arial", '', 11)

    # Ticket ID - prominent
    pdf.set_font("Arial", 'B', 13)
    pdf.set_text_color(0, 100, 0)
    pdf.cell(0, 8, txt=f"Ticket ID: {booking['ticket_id']}", ln=1)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", '', 11)

    # Amount - HIGHLIGHTED
    pdf.set_fill_color(255, 212, 0)  # Yellow highlight
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, txt=f"Amount Paid: Rs. {amount}", ln=1, fill=True)
    pdf.set_font("Arial", '', 11)

    # Other details
    pdf.cell(0, 6, txt=f"Passes: {booking['passes']} | Type: {pass_label}", ln=1)
    event_date = booking.get('event_date', 'March 3, 2026')
    pdf.cell(0, 6, txt=f"Date: {event_date} | Time: 10:00 AM - 5:00 PM", ln=1)
    pdf.cell(0, 6, txt=f"Venue: {venue}", ln=1)
    pdf.cell(0, 6, txt="Complimentary: Abir & Special Lassi", ln=1)
    pdf.ln(5)

    # QR Code
    if qr_path:
        try:
            y_pos = pdf.get_y()
            pdf.image(qr_path, x=75, y=y_pos, w=60)
            pdf.set_y(y_pos + 65)
        except Exception:
            pass
        finally:
            if qr_path and os.path.exists(qr_path):
                try:
                    os.unlink(qr_path)
                except Exception:
                    pass

    pdf.set_font("Arial", 'I', 8)
    pdf.set_text_color(128, 128, 128)
    pdf.cell(0, 5, txt="Show this ticket at the gate. Organized by Spectra Group - 2nd Year of HoliParty!", ln=1, align='C')

    out = pdf.output(dest='S')
    if isinstance(out, str):
        out = out.encode('latin-1')
    pdf_buf = io.BytesIO(out)
    pdf_buf.seek(0)
    return pdf_buf
