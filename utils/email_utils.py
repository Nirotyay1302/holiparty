import base64
from io import BytesIO
from config import Config

try:
    import resend
except ImportError:
    resend = None


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
