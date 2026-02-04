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
        existing_headers_stripped = [h.strip() for h in existing_headers] if existing_headers else []
        
        # Add "Pass Type" header if missing (column J)
        if len(existing_headers_stripped) < 10 or existing_headers_stripped[9] != 'Pass Type':
            if len(existing_headers_stripped) == 9:
                # Sheet has 9 headers, add "Pass Type" as 10th
                worksheet.update_cell(1, 10, 'Pass Type')
            elif not existing_headers:
                # Empty sheet, write all headers
                worksheet.append_row(headers)

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
            # Find ticket id cell (search in column D which is Ticket ID)
            all_values = worksheet.col_values(4)  # Column D = Ticket ID
            row_num = None
            for idx, val in enumerate(all_values, start=1):
                if idx > 1 and str(val).strip().upper() == ticket_id.upper():
                    row_num = idx
                    break
        except Exception:
            row_num = None

        if row_num and row_num > 1:
            worksheet.update(f"A{row_num}:J{row_num}", [row])
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
        # Get all data rows (skip header row 1)
        all_values = worksheet.get_all_values()
        if len(all_values) < 2:
            return []
        
        headers = [h.strip() for h in all_values[0]]
        # Ensure we have at least 9 columns, add Pass Type if missing
        if len(headers) < 10:
            headers.extend([''] * (10 - len(headers)))
        if headers[9] != 'Pass Type':
            headers[9] = 'Pass Type'
        
        out = []
        for row_data in all_values[1:]:
            if not row_data or not row_data[0]:  # Skip empty rows
                continue
            # Pad row to match headers
            row_data_padded = row_data + [''] * (len(headers) - len(row_data))
            
            # Build dict from headers
            r = {}
            for idx, header in enumerate(headers):
                if header:
                    r[header] = row_data_padded[idx] if idx < len(row_data_padded) else ''
            
            # Normalize keys expected by admin template
            out.append({
                'name': r.get('Name', '').strip(),
                'email': r.get('Email', '').strip(),
                'phone': r.get('Phone', '').strip(),
                'ticket_id': r.get('Ticket ID', '').strip(),
                'passes': int(r.get('Passes', 0) or 0),
                'amount': int(r.get('Amount', 0) or 0),
                'payment_status': r.get('Payment Status', '').strip() or 'Pending',
                'entry_status': r.get('Entry Status', 'Not Used').strip() or 'Not Used',
                'booking_date': r.get('Booking Date', '').strip(),
                'pass_type': r.get('Pass Type', 'entry').strip() or 'entry',
            })
        return out
    except Exception as e:
        print(f"Sheet read failed: {e}")
        import traceback
        traceback.print_exc()
        return []

def delete_booking_from_sheet(ticket_id):
    """Delete a booking row from Google Sheet by Ticket ID."""
    worksheet = _get_worksheet()
    if worksheet is None:
        return False
    try:
        # Find ticket id in column D (Ticket ID)
        all_values = worksheet.col_values(4)  # Column D = Ticket ID
        row_num = None
        for idx, val in enumerate(all_values, start=1):
            if idx > 1 and str(val).strip().upper() == str(ticket_id).strip().upper():
                row_num = idx
                break
        
        if row_num and row_num > 1:
            worksheet.delete_rows(row_num)
            print(f"Deleted booking {ticket_id} from sheet (row {row_num})")
            return True
        return False
    except Exception as e:
        print(f"Sheet delete failed: {e}")
        return False

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
            bdate = b.get('booking_date', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        data.append([b.get('name'), b.get('email'), b.get('phone'), b.get('ticket_id'), b.get('passes'),
                    b.get('amount', b.get('passes', 0) * 200), b.get('payment_status'),
                    b.get('entry_status', 'Not Used'), bdate, b.get('pass_type', 'entry')])
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