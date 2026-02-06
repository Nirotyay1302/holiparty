import gspread
import json
import os
from config import Config

_sheet_client = None
_sheet_client_error = None

def _get_credentials():
    """Load Google credentials from GOOGLE_CREDS_JSON env var or from file."""
    # 1. Try GOOGLE_CREDS_JSON env var (for Render/Heroku where file path can be tricky)
    creds_json = os.environ.get('GOOGLE_CREDS_JSON', '').strip()
    if creds_json:
        try:
            return json.loads(creds_json)
        except json.JSONDecodeError as e:
            print(f"GOOGLE_CREDS_JSON invalid JSON: {e}")
    
    # 2. Try file paths (multiple fallbacks for different deployment environments)
    paths_to_try = [
        getattr(Config, 'GOOGLE_CREDS_PATH', None) or 'creds.json',
        'creds.json',
        './creds.json',
        os.path.join(os.path.dirname(os.path.dirname(__file__)), 'creds.json'),
    ]
    for path in paths_to_try:
        if not path:
            continue
        if os.path.isfile(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Failed to read creds from {path}: {e}")
                continue
    return None

def _get_worksheet():
    """Get the first worksheet of the configured Google Sheet. Returns None on failure."""
    global _sheet_client, _sheet_client_error
    
    sheet_id = (getattr(Config, 'GOOGLE_SHEET_ID', None) or '').strip()
    if not sheet_id:
        print("GOOGLE_SHEET_ID not configured")
        return None
    
    try:
        creds_dict = _get_credentials()
        if not creds_dict:
            print("Google credentials not found. Set GOOGLE_CREDS_JSON env var or add creds.json. Ensure GOOGLE_SHEET_ID is set.")
            return None
        
        if _sheet_client is None:
            if hasattr(gspread, 'service_account_from_dict'):
                _sheet_client = gspread.service_account_from_dict(creds_dict)
            else:
                from oauth2client.service_account import ServiceAccountCredentials
                scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
                creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
                _sheet_client = gspread.authorize(creds)
            _sheet_client_error = None
        
        sheet = _sheet_client.open_by_key(sheet_id)
        return sheet.get_worksheet(0)
    except Exception as e:
        print(f"Google Sheet connection failed: {e}")
        import traceback
        traceback.print_exc()
        _sheet_client_error = str(e)
        return None

def update_sheet(data):
    if not getattr(Config, 'GOOGLE_SHEET_ID', None):
        print(f"Google Sheets not configured (GOOGLE_SHEET_ID missing). Would update: {data}")
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
        
        # Column order: Name(0), Email(1), Phone(2), Ticket ID(3), Passes(4), Amount(5), Payment Status(6), Entry Status(7), Booking Date(8), Pass Type(9)
        
        out = []
        for row_data in all_values[1:]:
            if not row_data or (len(row_data) > 0 and not str(row_data[0]).strip()):  # Skip empty rows
                continue
            row_data_padded = row_data + [''] * (10 - len(row_data))
            
            out.append({
                'name': (row_data_padded[0] or '').strip(),
                'email': (row_data_padded[1] or '').strip(),
                'phone': (row_data_padded[2] or '').strip(),
                'ticket_id': (row_data_padded[3] or '').strip(),
                'passes': int(row_data_padded[4] or 0) if row_data_padded[4] else 0,
                'amount': int(row_data_padded[5] or 0) if row_data_padded[5] else 0,
                'payment_status': (row_data_padded[6] or 'Pending').strip() or 'Pending',
                'entry_status': (row_data_padded[7] or 'Not Used').strip() or 'Not Used',
                'booking_date': (row_data_padded[8] or '').strip(),
                'pass_type': ((row_data_padded[9] if len(row_data_padded) > 9 else '') or 'entry').strip() or 'entry',
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
    if not getattr(Config, 'GOOGLE_SHEET_ID', None):
        print("Google Sheets not configured (GOOGLE_SHEET_ID missing).")
        return False
    
    try:
        worksheet = _get_worksheet()
        if worksheet is None:
            return False
        
        # Clear existing data
        worksheet.clear()
        
        # Add headers (must match upsert_booking_row / read_bookings)
        headers = ['Name', 'Email', 'Phone', 'Ticket ID', 'Passes', 'Amount', 'Payment Status', 'Entry Status', 'Booking Date', 'Pass Type']
        worksheet.append_row(headers)
        
        # Add data
        for row in bookings_data:
            worksheet.append_row(row)
        
        print("Google Sheet updated with all bookings.")
        return True
    except Exception as e:
        print(f"Google Sheet export failed: {e}")
        return False