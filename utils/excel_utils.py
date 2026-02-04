import gspread
from oauth2client.service_account import ServiceAccountCredentials
from config import Config

def _get_worksheet():
    if not Config.GOOGLE_CREDS_PATH or not Config.GOOGLE_SHEET_ID:
        return None
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(Config.GOOGLE_CREDS_PATH, scope)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(Config.GOOGLE_SHEET_ID)
    return sheet.get_worksheet(0)

def update_sheet(data):
    if not Config.GOOGLE_CREDS_PATH or not Config.GOOGLE_SHEET_ID:
        print(f"Google Sheets not configured. Would update: {data}")
        return
    
    try:
        worksheet = _get_worksheet()
        if worksheet is None:
            return
        worksheet.append_row(data)
        print(f"Sheet updated: {data}")
    except Exception as e:
        print(f"Sheet update failed: {e}")

def upsert_booking_row(booking_dict):
    """
    Upsert booking row by Ticket ID.
    This makes Google Sheet act as a persistent fallback store when Mongo is down.
    """
    worksheet = _get_worksheet()
    if worksheet is None:
        return False
    try:
        headers = ['Name', 'Email', 'Phone', 'Ticket ID', 'Passes', 'Amount', 'Payment Status', 'Entry Status', 'Booking Date', 'Pass Type']
        # Ensure header exists
        existing_headers = worksheet.row_values(1)
        if [h.strip() for h in existing_headers] != headers:
            # If sheet is empty, write headers; otherwise preserve and just ensure headers are present
            if not existing_headers:
                worksheet.append_row(headers)
            else:
                # If headers are different, keep existing sheet and do not rewrite to avoid deleting data
                pass

        ticket_id = (booking_dict.get('ticket_id') or '').strip()
        if not ticket_id:
            return False

        row = [
            booking_dict.get('name', ''),
            booking_dict.get('email', ''),
            booking_dict.get('phone', ''),
            ticket_id,
            int(booking_dict.get('passes', 0) or 0),
            int(booking_dict.get('amount', 0) or 0),
            booking_dict.get('payment_status', ''),
            booking_dict.get('entry_status', 'Not Used'),
            booking_dict.get('booking_date', ''),
            booking_dict.get('pass_type', 'entry'),
        ]

        try:
            # Find ticket id cell
            cell = worksheet.find(ticket_id)
        except Exception:
            cell = None

        if cell and cell.row > 1:
            worksheet.update(f"A{cell.row}:J{cell.row}", [row])
        else:
            worksheet.append_row(row)
        return True
    except Exception as e:
        print(f"Sheet upsert failed: {e}")
        return False

def read_bookings_from_google_sheet():
    """Read bookings as list[dict] from Google Sheet (best-effort)."""
    worksheet = _get_worksheet()
    if worksheet is None:
        return []
    try:
        records = worksheet.get_all_records()
        out = []
        for r in records:
            # Normalize keys expected by admin template
            out.append({
                'name': r.get('Name', ''),
                'email': r.get('Email', ''),
                'phone': r.get('Phone', ''),
                'ticket_id': r.get('Ticket ID', ''),
                'passes': int(r.get('Passes', 0) or 0),
                'amount': int(r.get('Amount', 0) or 0),
                'payment_status': r.get('Payment Status', ''),
                'entry_status': r.get('Entry Status', 'Not Used') or 'Not Used',
                'booking_date': r.get('Booking Date', ''),
                'pass_type': r.get('Pass Type', 'entry') or 'entry',
            })
        return out
    except Exception as e:
        print(f"Sheet read failed: {e}")
        return []

def sync_sheet_after_delete(bookings):
    """Re-export sheet with current bookings after a delete."""
    from datetime import datetime
    data = []
    for b in bookings:
        bid = b.get('_id')
        bdate = ''
        if bid and hasattr(bid, 'generation_time'):
            try:
                bdate = bid.generation_time.replace(tzinfo=None).strftime('%Y-%m-%d %H:%M:%S')
            except Exception:
                bdate = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        else:
            bdate = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        data.append([b.get('name'), b.get('email'), b.get('phone'), b.get('ticket_id'), b.get('passes'),
                    b.get('amount', b.get('passes', 0) * 200), b.get('payment_status'),
                    b.get('entry_status', 'Not Used'), bdate])
    return export_to_google_sheets(data)

def export_to_google_sheets(bookings_data):
    if not Config.GOOGLE_CREDS_PATH or not Config.GOOGLE_SHEET_ID:
        print("Google Sheets not configured.")
        return False
    
    try:
        worksheet = _get_worksheet()
        if worksheet is None:
            return False
        
        # Clear existing data
        worksheet.clear()
        
        # Add headers
        headers = ['Name', 'Email', 'Phone', 'Ticket ID', 'Passes', 'Amount', 'Payment Status', 'Entry Status', 'Booking Date']
        worksheet.append_row(headers)
        
        # Add data
        for row in bookings_data:
            worksheet.append_row(row)
        
        print("Google Sheet updated with all bookings.")
        return True
    except Exception as e:
        print(f"Google Sheet export failed: {e}")
        return False