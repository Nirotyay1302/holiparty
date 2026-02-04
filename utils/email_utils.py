import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formataddr
from config import Config


def send_email(to, subject, body, attachment=None):
    """Send email with optional PDF attachment. Returns True on success, False otherwise."""
    email_user = getattr(Config, 'EMAIL_USER', None) or ''
    email_pass = getattr(Config, 'EMAIL_PASS', None) or ''
    email_user = email_user.strip() if email_user else ''
    email_pass = email_pass.strip() if email_pass else ''
    
    # Remove spaces from app password (Gmail app passwords sometimes have spaces)
    email_pass = email_pass.replace(' ', '')

    # Detailed diagnostics
    if not email_user:
        print("ERROR: EMAIL_USER is empty or not set in environment variables")
        return False
    
    if not email_pass:
        print("ERROR: EMAIL_PASS is empty or not set in environment variables")
        return False
    
    if '@gmail.com' not in email_user.lower() and '@googlemail.com' not in email_user.lower():
        print(f"WARNING: EMAIL_USER ({email_user[:5]}...) doesn't look like a Gmail address")
    
    if len(email_pass) < 16:
        print(f"WARNING: EMAIL_PASS length is {len(email_pass)} (Gmail App Passwords are usually 16 characters)")
    
    print(f"Attempting to send email from {email_user[:5]}... to {to}")

    if not to or not str(to).strip():
        print("No recipient email address provided")
        return False

    to = str(to).strip()
    msg = MIMEMultipart('alternative')
    msg['From'] = formataddr(('Spectra HoliParty', email_user))
    msg['To'] = to
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html', 'utf-8'))

    if attachment:
        try:
            if hasattr(attachment, 'seek'):
                attachment.seek(0)
            payload = attachment.read() if hasattr(attachment, 'read') else attachment
            if payload:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(payload)
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', 'attachment', filename='Spectra_HoliParty_Ticket.pdf')
                msg.attach(part)
        except Exception as e:
            print(f"Attachment error: {e}")

    try:
        # Create SSL context with proper settings
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        server = smtplib.SMTP('smtp.gmail.com', 587, timeout=30)
        server.set_debuglevel(0)
        
        # EHLO
        code, message = server.ehlo()
        if code != 250:
            print(f"EHLO failed: {code} {message}")
            server.quit()
            return False
        
        # STARTTLS
        code, message = server.starttls(context=context)
        if code != 220:
            print(f"STARTTLS failed: {code} {message}")
            server.quit()
            return False
        
        # EHLO again after STARTTLS
        code, message = server.ehlo()
        if code != 250:
            print(f"EHLO after STARTTLS failed: {code} {message}")
            server.quit()
            return False
        
        # Login
        try:
            code, message = server.login(email_user, email_pass)
            if code != 235:
                print(f"LOGIN failed: {code} {message}")
                server.quit()
                return False
        except smtplib.SMTPAuthenticationError as auth_err:
            error_code = getattr(auth_err, 'smtp_code', 'Unknown')
            error_msg = str(auth_err)
            print(f"SMTP Authentication Error [{error_code}]: {error_msg}")
            print(f"EMAIL_USER: {email_user}")
            print(f"EMAIL_PASS length: {len(email_pass)} characters")
            print("SOLUTION: Go to Gmail → Account → Security → 2-Step Verification → App passwords")
            print("Generate a new App Password and set it as EMAIL_PASS in Render")
            server.quit()
            return False
        
        # Send email
        try:
            failed = server.sendmail(email_user, [to], msg.as_string())
            if failed:
                print(f"Some recipients failed: {failed}")
                server.quit()
                return False
        except smtplib.SMTPRecipientsRefused as e:
            print(f"Recipients refused: {e}")
            server.quit()
            return False
        
        server.quit()
        print(f"✓ Email sent successfully to {to}")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        error_code = getattr(e, 'smtp_code', 'Unknown')
        error_msg = str(e)
        print(f"SMTP Authentication Error [{error_code}]: {error_msg}")
        print(f"EMAIL_USER: {email_user}")
        print(f"EMAIL_PASS: {'*' * len(email_pass)} (length: {len(email_pass)})")
        print("SOLUTION:")
        print("1. Go to https://myaccount.google.com/apppasswords")
        print("2. Generate App Password for 'Mail'")
        print("3. Copy the 16-character password")
        print("4. Set EMAIL_PASS in Render Environment Variables")
        return False
    except smtplib.SMTPRecipientsRefused as e:
        print(f"Email recipient refused: {e}")
        return False
    except smtplib.SMTPException as e:
        print(f"SMTP error: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"Email send failed: {e}")
        import traceback
        traceback.print_exc()
        return False