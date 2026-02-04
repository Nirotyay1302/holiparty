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

    if not email_user or not email_pass:
        print(f"Email not configured (EMAIL_USER/EMAIL_PASS missing). Would send to {to}: {subject}")
        return False

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
        server = smtplib.SMTP('smtp.gmail.com', 587, timeout=30)
        server.set_debuglevel(0)  # Set to 1 for verbose debug
        server.ehlo()
        server.starttls(context=ssl.create_default_context())
        server.ehlo()
        server.login(email_user, email_pass)
        server.sendmail(email_user, [to], msg.as_string())
        server.quit()
        print(f"Email sent successfully to {to}")
        return True
    except smtplib.SMTPAuthenticationError as e:
        error_msg = str(e)
        print(f"Email auth failed: {error_msg}")
        print(f"Check: EMAIL_USER={email_user[:3]}... EMAIL_PASS length={len(email_pass)}")
        print("Ensure you're using Gmail App Password (not regular password)")
        return False
    except smtplib.SMTPRecipientsRefused as e:
        print(f"Email recipient refused: {e}")
        return False
    except smtplib.SMTPException as e:
        print(f"SMTP error: {e}")
        return False
    except Exception as e:
        print(f"Email send failed: {e}")
        import traceback
        traceback.print_exc()
        return False