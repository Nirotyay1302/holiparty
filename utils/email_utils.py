import base64
from io import BytesIO
from config import Config

try:
    import resend
except ImportError:
    resend = None


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
    entry_starter_price = pricing.get('entry_plus_starter', 350)
    entry_lunch_price = pricing.get('entry_plus_starter_lunch', 499)
    
    # Calculate plan details
    passes = booking.get('passes', 1)
    pass_type = booking.get('pass_type', 'entry')
    amount = booking.get('amount', passes * entry_pass_price)
    
    # Get event details
    event_date = event_content.get('event_date', 'March 4, 2026')
    event_time = event_content.get('event_time', '10:00 AM – 5:00 PM')
    venue = event_content.get('venue', 'Dighi Garden Mankundu')
    organizer = event_content.get('organizer', 'Spectra Group')
    complimentary = event_content.get('complimentary', 'Abir & Special Lassi')
    food_available = pricing.get('food_available', 'Veg and Non-Veg options available at counters')
    
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


def send_email(to, subject, body, attachment=None):
    """Send email with optional PDF attachment using Resend API. Returns True on success, False otherwise."""
    api_key = getattr(Config, 'RESEND_API_KEY', None) or ''
    from_email = getattr(Config, 'RESEND_FROM_EMAIL', None) or ''
    
    api_key = api_key.strip() if api_key else ''
    from_email = from_email.strip() if from_email else ''
    
    # Check if resend package is installed
    if resend is None:
        print("ERROR: resend package is not installed. Run: pip install resend")
        return False
    
    # Validate configuration
    if not api_key:
        print("ERROR: RESEND_API_KEY is empty or not set in environment variables")
        print("Get your API key from: https://resend.com/api-keys")
        return False
    
    if not from_email:
        print("ERROR: RESEND_FROM_EMAIL is empty or not set in environment variables")
        print("Set it to your verified domain email (e.g., tickets@yourdomain.com) or use resend.com domain")
        return False
    
    if not to or not str(to).strip():
        print("No recipient email address provided")
        return False
    
    to = str(to).strip()
    
    print(f"Attempting to send email via Resend from {from_email} to {to}")
    
    try:
        # Initialize Resend client
        resend.api_key = api_key
        
        # Prepare attachment if provided
        attachments = []
        if attachment:
            try:
                if hasattr(attachment, 'seek'):
                    attachment.seek(0)
                pdf_data = attachment.read() if hasattr(attachment, 'read') else attachment
                
                if pdf_data:
                    # Convert to base64 for Resend
                    if isinstance(pdf_data, bytes):
                        pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')
                    else:
                        pdf_base64 = base64.b64encode(bytes(pdf_data)).decode('utf-8')
                    
                    attachments.append({
                        "filename": "Spectra_HoliParty_Ticket.pdf",
                        "content": pdf_base64  # Resend expects base64-encoded content
                    })
            except Exception as e:
                print(f"Attachment processing error: {e}")
        
        # Send email via Resend
        params = {
            "from": from_email,
            "to": [to],
            "subject": subject,
            "html": body,
        }
        
        if attachments:
            params["attachments"] = attachments
        
        response = resend.Emails.send(params)
        
        # Check response
        if response and hasattr(response, 'id'):
            print(f"✓ Email sent successfully to {to} (Resend ID: {response.id})")
            return True
        else:
            print(f"Email send failed: Unexpected response from Resend: {response}")
            return False
            
    except Exception as e:
        error_msg = str(e)
        print(f"Email send failed: {error_msg}")
        
        # Provide helpful error messages
        if "Unauthorized" in error_msg or "401" in error_msg:
            print("SOLUTION: Check your RESEND_API_KEY in Render environment variables")
            print("Get your API key from: https://resend.com/api-keys")
        elif "Forbidden" in error_msg or "403" in error_msg:
            print("SOLUTION: Verify your sender domain or use a Resend test domain")
            print("Check: https://resend.com/domains")
        elif "validation" in error_msg.lower() or "invalid" in error_msg.lower():
            print("SOLUTION: Check that RESEND_FROM_EMAIL is a valid verified email address")
            print("For testing, you can use: onboarding@resend.dev")
        
        import traceback
        traceback.print_exc()
        return False
