import gspread
from oauth2client.service_account import ServiceAccountCredentials
from config import Config

def update_sheet(data):
    if not Config.GOOGLE_CREDS_PATH or not Config.GOOGLE_SHEET_ID:
        print(f"Google Sheets not configured. Would update: {data}")
        return
    
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(Config.GOOGLE_CREDS_PATH, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(Config.GOOGLE_SHEET_ID)
        worksheet = sheet.get_worksheet(0)  # Use the first worksheet instead of hardcoded ID
        worksheet.append_row(data)
        print(f"Sheet updated: {data}")
    except Exception as e:
        print(f"Sheet update failed: {e}")

def export_to_google_sheets(bookings_data):
    if not Config.GOOGLE_CREDS_PATH or not Config.GOOGLE_SHEET_ID:
        print("Google Sheets not configured.")
        return False
    
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(Config.GOOGLE_CREDS_PATH, scope)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(Config.GOOGLE_SHEET_ID)
        worksheet = sheet.get_worksheet(0)
        
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