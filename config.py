import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-this'
    MONGO_URI = os.environ.get('MONGO_URI') or 'mongodb+srv://nirotyaymukherjee563_db_user:U9dbgw3jvJTUUJnw@cluster0.zyixrsi.mongodb.net/'
    MONGODB_SETTINGS = {
        'db': 'holi_party',
        'host': os.environ.get('MONGO_URI') or 'mongodb+srv://nirotyaymukherjee563_db_user:U9dbgw3jvJTUUJnw@cluster0.zyixrsi.mongodb.net/'
    }
    RAZORPAY_KEY_ID = 'rzp_test_SBY1cIA6tBEKpN'
    RAZORPAY_KEY_SECRET = 'JEsj6m763sTNgiALdpOeZxpq'
    EMAIL_USER = os.environ.get('EMAIL_USER')
    EMAIL_PASS = os.environ.get('EMAIL_PASS')
    GOOGLE_SHEET_ID = os.environ.get('GOOGLE_SHEET_ID') or '13oh5EqMrsnNOqCGqKzDNzHgy4p9gRGXz6JDVK7XyKew'
    GOOGLE_CREDS_PATH = os.environ.get('GOOGLE_CREDS_PATH') or 'creds.json'