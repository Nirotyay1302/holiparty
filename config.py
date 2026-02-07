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
    # Email via Resend API (HTTPS-based, works on Render free tier)
    # Default API key provided, but should be set via environment variable in production
    RESEND_API_KEY = (os.environ.get('RESEND_API_KEY') or 're_Hf3zZg8z_84by2NfLKGNCkGFqubhShAZM').strip()
    RESEND_FROM_EMAIL = (os.environ.get('RESEND_FROM_EMAIL') or 'onboarding@resend.dev').strip()
    # Email Provider Selection: 'smtp', 'sendgrid', 'mailgun', 'resend' (default)
    # On Render FREE tier: use 'sendgrid' or 'resend' (SMTP ports 25/465/587 are blocked on free tier)
    EMAIL_PROVIDER = (os.environ.get('EMAIL_PROVIDER') or 'resend').strip()
    
    # Gmail SMTP (works on paid hosting only; Render free tier blocks SMTP ports)
    EMAIL_USER = (os.environ.get('EMAIL_USER') or '').strip()
    EMAIL_PASS = (os.environ.get('EMAIL_PASS') or '').strip()
    SMTP_HOST = (os.environ.get('SMTP_HOST') or 'smtp.gmail.com').strip()
    SMTP_PORT = int(os.environ.get('SMTP_PORT') or 587)
    
    # SendGrid Configuration (for EMAIL_PROVIDER='sendgrid')
    SENDGRID_API_KEY = (os.environ.get('SENDGRID_API_KEY') or '').strip()
    
    # Mailgun Configuration (for EMAIL_PROVIDER='mailgun')
    MAILGUN_API_KEY = (os.environ.get('MAILGUN_API_KEY') or '').strip()
    MAILGUN_DOMAIN = (os.environ.get('MAILGUN_DOMAIN') or '').strip()
    
    # Common email from address (used by sendgrid, mailgun)
    EMAIL_FROM = (os.environ.get('EMAIL_FROM') or '').strip()
    # Contact form submissions are sent to this inbox
    CONTACT_EMAIL = (os.environ.get('CONTACT_EMAIL') or 'spectraholi2026@gmail.com').strip()
    GOOGLE_SHEET_ID = os.environ.get('GOOGLE_SHEET_ID') or '13oh5EqMrsnNOqCGqKzDNzHgy4p9gRGXz6JDVK7XyKew'
    GOOGLE_CREDS_PATH = os.environ.get('GOOGLE_CREDS_PATH') or 'creds.json'

    # Where to store JSON fallback files (bookings.json, event_content.json).
    # On Render free tier this remains ephemeral. If you attach a disk, set:
    # DATA_DIR=/var/data (and mount a disk there).
    DATA_DIR = (os.environ.get('DATA_DIR') or '').strip()

    # Admin Login Credentials
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME') or 'admin'
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD') or 'holi2026'