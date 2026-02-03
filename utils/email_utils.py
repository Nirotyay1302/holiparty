import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from config import Config

def send_email(to, subject, body, attachment=None):
    if not Config.EMAIL_USER or not Config.EMAIL_PASS:
        print(f"Email not configured. Would send to {to}: {subject}")
        return
    
    msg = MIMEMultipart()
    msg['From'] = Config.EMAIL_USER
    msg['To'] = to
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))
    
    if attachment:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f"attachment; filename=ticket.pdf")
        msg.attach(part)
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(Config.EMAIL_USER, Config.EMAIL_PASS)
        text = msg.as_string()
        server.sendmail(Config.EMAIL_USER, to, text)
        server.quit()
        print(f"Email sent to {to}")
    except Exception as e:
        print(f"Email send failed: {e}")