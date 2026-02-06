import base64
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from io import BytesIO
from config import Config

try:
    import resend
    from resend.exceptions import ResendError
except ImportError:
    resend = None
    ResendError = Exception

try:
    import sendgrid
    from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
except ImportError:
    sendgrid = None

try:
    import requests
except ImportError:
    requests = None


def create_success_email_template(booking, event_content):
    """Create a comprehensive success email template with all booking and plan details."""
    # Get pass type label
    pass_type_labels = {
        'entry': 'Entry Only',
        'entry_starter': 'Entry + Starter',
        'entry_starter_lunch': 'Entry + Starter + Lunch'
    }
    pass_label = pass_type_labels.get(booking.get('pass_type', 'entry'), 'Entry Only')
    
    # Get pricing details
    pricing = event_content.get('pricing', {})
    entry_pass_price = pricing.get('entry_pass', 200)
    entry_starter_price = pricing.get('entry_plus_starter', 349)
    entry_lunch_price = pricing.get('entry_plus_starter_lunch', 499)
    
    # Calculate plan details
    passes = booking.get('passes', 1)
    pass_type = booking.get('pass_type', 'entry')
    amount = booking.get('amount', passes * entry_pass_price)
    
    # Get event details
    event_date = event_content.get('event_date', 'March 3, 2026')
    event_time = event_content.get('event_time', '10:00 AM – 5:00 PM')
    venue = event_content.get('venue', 'Dighi Garden Mankundu')
    organizer = event_content.get('organizer', 'Spectra Group')
    complimentary = event_content.get('complimentary', 'Abir & Special Lassi')
    food_available = pricing.get('food_available', 'Food & drink available at counter')
    
    # Get contact persons
    contact_persons = event_content.get('contact_persons', [])
    contact_info = ""
    if contact_persons:
        contact_info = "<ul>"
        for person in contact_persons:
            contact_info += f"<li><strong>{person.get('name', '')}</strong>: {person.get('phone', '')}</li>"
        contact_info += "</ul>"
    
    # Booking date
    booking_date = booking.get('booking_date', '')
    
    # Create comprehensive email HTML
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f4f4f4;
            }}
            .container {{
                background-color: #ffffff;
                border-radius: 10px;
                padding: 30px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .header {{
                text-align: center;
                background: linear-gradient(135deg, #ff2f92 0%, #ff6b35 100%);
                color: white;
                padding: 25px;
                border-radius: 10px 10px 0 0;
                margin: -30px -30px 30px -30px;
            }}
            .header h1 {{
                margin: 0;
                font-size: 28px;
                font-weight: bold;
            }}
            .success-badge {{
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                border-radius: 25px;
                display: inline-block;
                margin: 15px 0;
                font-weight: bold;
            }}
            .ticket-info {{
                background-color: #f8f9fa;
                border-left: 4px solid #ff2f92;
                padding: 20px;
                margin: 20px 0;
                border-radius: 5px;
            }}
            .ticket-info h2 {{
                color: #ff2f92;
                margin-top: 0;
                font-size: 20px;
            }}
            .info-row {{
                display: flex;
                justify-content: space-between;
                padding: 10px 0;
                border-bottom: 1px solid #e0e0e0;
            }}
            .info-row:last-child {{
                border-bottom: none;
            }}
            .info-label {{
                font-weight: bold;
                color: #555;
                flex: 1;
            }}
            .info-value {{
                color: #333;
                flex: 1;
                text-align: right;
            }}
            .highlight {{
                background-color: #fff3cd;
                padding: 15px;
                border-radius: 5px;
                margin: 20px 0;
                border-left: 4px solid #ffc107;
            }}
            .plan-details {{
                background-color: #e8f5e9;
                padding: 20px;
                border-radius: 5px;
                margin: 20px 0;
            }}
            .plan-details h3 {{
                color: #2e7d32;
                margin-top: 0;
            }}
            .amount-box {{
                background-color: #ff2f92;
                color: white;
                padding: 20px;
                border-radius: 5px;
                text-align: center;
                margin: 20px 0;
                font-size: 24px;
                font-weight: bold;
            }}
            .footer {{
                margin-top: 30px;
                padding-top: 20px;
                border-top: 2px solid #e0e0e0;
                text-align: center;
                color: #666;
                font-size: 14px;
            }}
            .contact-box {{
                background-color: #e3f2fd;
                padding: 15px;
                border-radius: 5px;
                margin: 20px 0;
            }}
            .contact-box h3 {{
                color: #1976d2;
                margin-top: 0;
            }}
            ul {{
                margin: 10px 0;
                padding-left: 20px;
            }}
            li {{
                margin: 5px 0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎉 Spectra HoliParty 2026 🎉</h1>
            </div>
            
            <div style="text-align: center;">
                <div class="success-badge">✓ Booking Confirmed!</div>
            </div>
            
            <p>Dear <strong>{booking.get('name', 'Guest')}</strong>,</p>
            
            <p>We are thrilled to confirm your booking for <strong>Spectra HoliParty 2026</strong>! Your entry pass has been successfully processed and confirmed.</p>
            
            <div class="ticket-info">
                <h2>🎫 Your Ticket Details</h2>
                <div class="info-row">
                    <span class="info-label">Ticket ID:</span>
                    <span class="info-value"><strong>{booking.get('ticket_id', 'N/A')}</strong></span>
                </div>
                <div class="info-row">
                    <span class="info-label">Order ID:</span>
                    <span class="info-value">{booking.get('order_id', booking.get('ticket_id', 'N/A'))}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Booking Date:</span>
                    <span class="info-value">{booking_date}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Payment Status:</span>
                    <span class="info-value" style="color: #4CAF50;"><strong>✓ Paid</strong></span>
                </div>
            </div>
            
            <div class="plan-details">
                <h3>📋 Your Booking Plan</h3>
                <div class="info-row">
                    <span class="info-label">Pass Type:</span>
                    <span class="info-value"><strong>{pass_label}</strong></span>
                </div>
                <div class="info-row">
                    <span class="info-label">Number of Passes:</span>
                    <span class="info-value"><strong>{passes} {'Pass' if passes == 1 else 'Passes'}</strong></span>
                </div>
                <div class="info-row">
                    <span class="info-label">Booking Type:</span>
                    <span class="info-value">{'Group Booking (5+ passes)' if booking.get('is_group_booking', False) else 'Individual Booking'}</span>
                </div>
            </div>
            
            <div class="amount-box">
                Total Amount Paid: ₹{amount}
            </div>
            
            <div class="highlight">
                <h3 style="margin-top: 0; color: #856404;">📅 Event Information</h3>
                <div class="info-row">
                    <span class="info-label">Date:</span>
                    <span class="info-value"><strong>{event_date}</strong></span>
                </div>
                <div class="info-row">
                    <span class="info-label">Time:</span>
                    <span class="info-value"><strong>{event_time}</strong></span>
                </div>
                <div class="info-row">
                    <span class="info-label">Venue:</span>
                    <span class="info-value"><strong>{venue}</strong></span>
                </div>
            </div>
            
            <div class="plan-details">
                <h3>🎁 What's Included</h3>
                <ul>
                    <li><strong>Entry Pass:</strong> Access to the event venue</li>
                    {f"<li><strong>Starter:</strong> Delicious starter included</li>" if pass_type in ['entry_starter', 'entry_starter_lunch'] else ""}
                    {f"<li><strong>Lunch:</strong> Full meal included</li>" if pass_type == 'entry_starter_lunch' else ""}
                    <li><strong>Complimentary:</strong> {complimentary}</li>
                </ul>
                <p><strong>Food Options:</strong> {food_available}</p>
            </div>
            
            <div class="highlight">
                <h3 style="margin-top: 0; color: #856404;">📱 Important Instructions</h3>
                <ul>
                    <li>Your ticket PDF is attached to this email. Please download and save it.</li>
                    <li>Show the QR code on your ticket at the gate for entry.</li>
                    <li>Please arrive on time to avoid any delays.</li>
                    <li>Carry a valid ID proof along with your ticket.</li>
                    <li>Keep your ticket safe - you'll need it for entry.</li>
                </ul>
            </div>
            
            <div class="contact-box">
                <h3>📞 Need Help?</h3>
                <p>If you have any questions or need assistance, feel free to contact us:</p>
                {contact_info if contact_info else "<p><strong>Contact:</strong> Check our website for contact details</p>"}
            </div>
            
            <div class="ticket-info">
                <h2>👤 Your Contact Information</h2>
                <div class="info-row">
                    <span class="info-label">Name:</span>
                    <span class="info-value">{booking.get('name', 'N/A')}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Email:</span>
                    <span class="info-value">{booking.get('email', 'N/A')}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Phone:</span>
                    <span class="info-value">{booking.get('phone', 'N/A')}</span>
                </div>
                <div class="info-row">
                    <span class="info-label">Address:</span>
                    <span class="info-value">{booking.get('address', 'N/A')}</span>
                </div>
            </div>
            
            <p style="margin-top: 30px;">We look forward to celebrating Holi with you! Get ready for an amazing day filled with colors, music, and joy! 🎨🎵🎉</p>
            
            <div class="footer">
                <p><strong>Organized by {organizer}</strong></p>
                <p>Thank you for choosing Spectra HoliParty 2026!</p>
                <p style="font-size: 12px; color: #999;">This is an automated confirmation email. Please do not reply to this email.</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html_body


def _send_via_smtp(to, subject, body, attachment=None, from_email=None):
    """Send email via SMTP (Gmail, etc.)"""
    email_user = getattr(Config, 'EMAIL_USER', None) or ''
    email_pass = getattr(Config, 'EMAIL_PASS', None) or ''
    smtp_host = getattr(Config, 'SMTP_HOST', None) or 'smtp.gmail.com'
    smtp_port = int(getattr(Config, 'SMTP_PORT', None) or 587)
    
    if not from_email:
        from_email = email_user
    
    if not email_user or not email_pass:
        print("ERROR: EMAIL_USER and EMAIL_PASS must be set for SMTP")
        return False
    
    try:
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))
        
        if attachment:
            try:
                if hasattr(attachment, 'seek'):
                    attachment.seek(0)
                pdf_data = attachment.read() if hasattr(attachment, 'read') else attachment
                if pdf_data:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(pdf_data)
                    encoders.encode_base64(part)
                    part.add_header('Content-Disposition', 'attachment; filename= "Spectra_HoliParty_Ticket.pdf"')
                    msg.attach(part)
            except Exception as e:
                print(f"Attachment processing error: {e}")
        
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(email_user, email_pass)
        text = msg.as_string()
        server.sendmail(from_email, to, text)
        server.quit()
        
        print(f"✓ Email sent successfully via SMTP to {to}")
        return True
    except Exception as e:
        print(f"SMTP email send failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def _send_via_sendgrid(to, subject, body, attachment=None, from_email=None):
    """Send email via SendGrid API"""
    if sendgrid is None:
        print("ERROR: sendgrid package not installed. Run: pip install sendgrid")
        return False
    
    api_key = getattr(Config, 'SENDGRID_API_KEY', None) or ''
    if not from_email:
        from_email = getattr(Config, 'EMAIL_FROM', None) or getattr(Config, 'EMAIL_USER', None) or ''
    
    if not api_key:
        print("ERROR: SENDGRID_API_KEY must be set")
        return False
    
    try:
        sg = sendgrid.SendGridAPIClient(api_key=api_key)
        message = Mail(
            from_email=from_email,
            to_emails=to,
            subject=subject,
            html_content=body
        )
        
        if attachment:
            try:
                if hasattr(attachment, 'seek'):
                    attachment.seek(0)
                pdf_data = attachment.read() if hasattr(attachment, 'read') else attachment
                if pdf_data:
                    encoded = base64.b64encode(pdf_data).decode()
                    message.attachment = Attachment(
                        FileContent(encoded),
                        FileName('Spectra_HoliParty_Ticket.pdf'),
                        FileType('application/pdf'),
                        Disposition('attachment')
                    )
            except Exception as e:
                print(f"Attachment processing error: {e}")
        
        response = sg.send(message)
        print(f"✓ Email sent successfully via SendGrid to {to} (Status: {response.status_code})")
        return True
    except Exception as e:
        print(f"SendGrid email send failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def _send_via_mailgun(to, subject, body, attachment=None, from_email=None):
    """Send email via Mailgun API"""
    if requests is None:
        print("ERROR: requests package not installed. Run: pip install requests")
        return False
    
    api_key = getattr(Config, 'MAILGUN_API_KEY', None) or ''
    domain = getattr(Config, 'MAILGUN_DOMAIN', None) or ''
    if not from_email:
        from_email = getattr(Config, 'EMAIL_FROM', None) or f'tickets@{domain}' if domain else ''
    
    if not api_key or not domain:
        print("ERROR: MAILGUN_API_KEY and MAILGUN_DOMAIN must be set")
        return False
    
    try:
        url = f"https://api.mailgun.net/v3/{domain}/messages"
        files = []
        
        if attachment:
            try:
                if hasattr(attachment, 'seek'):
                    attachment.seek(0)
                pdf_data = attachment.read() if hasattr(attachment, 'read') else attachment
                if pdf_data:
                    files.append(('attachment', ('Spectra_HoliParty_Ticket.pdf', pdf_data, 'application/pdf')))
            except Exception as e:
                print(f"Attachment processing error: {e}")
        
        data = {
            'from': from_email,
            'to': to,
            'subject': subject,
            'html': body
        }
        
        response = requests.post(url, auth=('api', api_key), data=data, files=files)
        
        if response.status_code == 200:
            print(f"✓ Email sent successfully via Mailgun to {to}")
            return True
        else:
            print(f"Mailgun email send failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"Mailgun email send failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def _send_via_resend(to, subject, body, attachment=None, from_email=None):
    """Send email via Resend API"""
    if resend is None:
        print("ERROR: resend package not installed. Run: pip install resend")
        return False
    
    api_key = getattr(Config, 'RESEND_API_KEY', None) or ''
    if not from_email:
        from_email = getattr(Config, 'RESEND_FROM_EMAIL', None) or ''
    
    api_key = api_key.strip() if api_key else ''
    from_email = from_email.strip() if from_email else ''
    
    if not api_key:
        print("ERROR: RESEND_API_KEY is empty or not set")
        return False
    
    if not from_email:
        print("ERROR: RESEND_FROM_EMAIL is empty or not set")
        return False
    
    try:
        resend.api_key = api_key
        
        attachments = []
        if attachment:
            try:
                if hasattr(attachment, 'seek'):
                    attachment.seek(0)
                pdf_data = attachment.read() if hasattr(attachment, 'read') else attachment
                if pdf_data:
                    if isinstance(pdf_data, bytes):
                        pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')
                    else:
                        pdf_base64 = base64.b64encode(bytes(pdf_data)).decode('utf-8')
                    attachments.append({
                        "filename": "Spectra_HoliParty_Ticket.pdf",
                        "content": pdf_base64
                    })
            except Exception as e:
                print(f"Attachment processing error: {e}")
        
        params = {
            "from": from_email,
            "to": [to],
            "subject": subject,
            "html": body,
        }
        
        if attachments:
            params["attachments"] = attachments
        
        response = resend.Emails.send(params)
        
        if response and hasattr(response, 'id'):
            print(f"✓ Email sent successfully via Resend to {to} (Resend ID: {response.id})")
            return True
        else:
            print(f"Email send failed: Unexpected response from Resend: {response}")
            return False

    except ResendError as e:
        error_msg = str(e)
        print(f"Email send failed: {error_msg}")
        if "only send testing emails to your own email" in error_msg.lower() or "verify a domain" in error_msg.lower():
            print("SOLUTION: With onboarding@resend.dev you can only send TO the email linked to your Resend account.")
            print("To send to customers, verify a domain at https://resend.com/domains and set RESEND_FROM_EMAIL to an email on that domain.")
        return False
            
    except Exception as e:
        print(f"Resend email send failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def send_contact_form_email(name, email, phone, subject, message):
    """
    Send contact form submission to the configured CONTACT_EMAIL inbox.
    Returns True on success, False otherwise.
    """
    to_email = getattr(Config, 'CONTACT_EMAIL', None) or 'spectraholi2026@gmail.com'
    to_email = str(to_email).strip()
    if not to_email:
        print("CONTACT_EMAIL not set, cannot send contact form")
        return False

    subject_line = f"Spectra HoliParty Contact: {subject}" if subject else "Spectra HoliParty - New Contact Form Message"
    body = f"""
    <h2>New Contact Form Message</h2>
    <p><strong>From:</strong> {name}</p>
    <p><strong>Email:</strong> {email}</p>
    <p><strong>Phone:</strong> {phone or 'Not provided'}</p>
    <p><strong>Subject:</strong> {subject or 'Not specified'}</p>
    <hr>
    <p><strong>Message:</strong></p>
    <p>{message}</p>
    """
    return send_email(to_email, subject_line, body)


def send_email(to, subject, body, attachment=None):
    """
    Send email with optional PDF attachment using configured provider.
    Supports: smtp, sendgrid, mailgun, resend
    Set EMAIL_PROVIDER environment variable to choose provider.
    Returns True on success, False otherwise.
    """
    if not to or not str(to).strip():
        print("No recipient email address provided")
        return False
    
    to = str(to).strip()
    
    # Determine which provider to use (default: resend for backward compatibility)
    provider = (getattr(Config, 'EMAIL_PROVIDER', None) or 'resend').lower().strip()
    
    # Get from_email based on provider
    from_email = None
    if provider == 'smtp':
        from_email = getattr(Config, 'EMAIL_USER', None) or ''
    elif provider == 'sendgrid':
        from_email = getattr(Config, 'EMAIL_FROM', None) or getattr(Config, 'EMAIL_USER', None) or ''
    elif provider == 'mailgun':
        domain = getattr(Config, 'MAILGUN_DOMAIN', None) or ''
        from_email = getattr(Config, 'EMAIL_FROM', None) or (f'tickets@{domain}' if domain else '')
    elif provider == 'resend':
        from_email = getattr(Config, 'RESEND_FROM_EMAIL', None) or ''
    else:
        from_email = getattr(Config, 'RESEND_FROM_EMAIL', None) or getattr(Config, 'EMAIL_USER', None) or ''
    
    print(f"Attempting to send email via {provider.upper()} from {from_email} to {to}")
    
    # Route to appropriate provider
    if provider == 'smtp':
        return _send_via_smtp(to, subject, body, attachment, from_email)
    elif provider == 'sendgrid':
        return _send_via_sendgrid(to, subject, body, attachment, from_email)
    elif provider == 'mailgun':
        return _send_via_mailgun(to, subject, body, attachment, from_email)
    elif provider == 'resend':
        return _send_via_resend(to, subject, body, attachment, from_email)
    else:
        # Default to Resend for backward compatibility
        print(f"Unknown provider '{provider}', defaulting to Resend")
        return _send_via_resend(to, subject, body, attachment, from_email)
