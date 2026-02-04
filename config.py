import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-this'
    # IMPORTANT: Never hardcode credentials in source code.
    # Set MONGO_URI in your hosting provider / environment variables.
    MONGO_URI = (os.environ.get('MONGO_URI') or '').strip()
    MONGODB_SETTINGS = {
        'db': 'holi_party',
        'host': (os.environ.get('MONGO_URI') or '').strip()
    }
    # Razorpay removed - UPI/QR payment only
    EMAIL_USER = (os.environ.get('EMAIL_USER') or '').strip()
    EMAIL_PASS = (os.environ.get('EMAIL_PASS') or '').strip()
    GOOGLE_SHEET_ID = os.environ.get('GOOGLE_SHEET_ID') or '13oh5EqMrsnNOqCGqKzDNzHgy4p9gRGXz6JDVK7XyKew'
    GOOGLE_CREDS_PATH = os.environ.get('GOOGLE_CREDS_PATH') or 'creds.json'