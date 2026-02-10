from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from config import Config
import uuid
import io
from datetime import datetime

app = Flask(__name__)
app.config.from_object(Config)

# Lightweight ping - no heavy imports, for keep-alive (prevents Render sleep)
@app.route('/ping')
def ping():
    return 'ok', 200

@app.route('/test_email_config')
def test_email_config():
    """Test endpoint to check email configuration (admin only)."""
    if 'admin_logged_in' not in session:
        return jsonify({'error': 'Not authenticated'})
    
    resend_api_key = getattr(Config, 'RESEND_API_KEY', None) or ''
    resend_from = getattr(Config, 'RESEND_FROM_EMAIL', None) or ''
    
    config_status = {
        'RESEND_API_KEY_set': bool(resend_api_key),
        'RESEND_API_KEY_value': resend_api_key[:8] + '...' if resend_api_key else 'NOT SET',
        'RESEND_FROM_EMAIL_set': bool(resend_from),
        'RESEND_FROM_EMAIL_value': resend_from if resend_from else 'NOT SET',
    }
    
    # Try to send a test email via Resend
    test_result = None
    if resend_api_key and resend_from:
        try:
            test_body = "<p>This is a test email from Spectra HoliParty admin panel.</p>"
            test_result = send_email(resend_from, "Test Email - Spectra HoliParty", test_body)
        except Exception as e:
            test_result = f"Error: {str(e)}"
    elif not resend_api_key:
        test_result = "RESEND_API_KEY not configured"
    elif not resend_from:
        test_result = "RESEND_FROM_EMAIL not configured"
    
    return jsonify({
        'config': config_status,
        'test_email_sent': test_result,
        'instructions': {
            'step1': 'Sign up at https://resend.com (free tier: 3,000 emails/month)',
            'step2': 'Go to https://resend.com/api-keys and create an API key',
            'step3': 'Copy the API key and set RESEND_API_KEY in Render Environment Variables',
            'step4': 'Set RESEND_FROM_EMAIL to your verified domain email (or use onboarding@resend.dev for testing)',
            'step5': 'Verify your domain at https://resend.com/domains (optional, for production)',
        }
    })

@app.after_request
def add_cache_headers(response):
    if request.path.startswith('/static/'):
        response.cache_control.max_age = 3600
        response.cache_control.public = True
    return response

# Lazy imports for heavy modules (speeds up cold start)
from models import Booking, EventContent
from utils.email_utils import send_email, send_contact_form_email, create_success_email_template
from utils.qr_utils import generate_qr
from utils.excel_utils import update_sheet, export_to_google_sheets, sync_sheet_after_delete, upsert_booking_row, delete_booking_from_sheet
from utils.ticket_utils import generate_ticket_pdf

# Razorpay client
# razorpay_client = razorpay.Client(auth=(app.config['RAZORPAY_KEY_ID'], app.config['RAZORPAY_KEY_SECRET']))

# Admin credentials
# ADMIN_USERNAME = app.config['ADMIN_USERNAME']
# ADMIN_PASSWORD = app.config['ADMIN_PASSWORD']

@app.route('/')
def home():
    content = EventContent.get_content()
    return render_template('index.html', content=content)

@app.route('/about')
def about():
    content = EventContent.get_content()
    return render_template('about.html', content=content)

@app.route('/contact')
def contact():
    content = EventContent.get_content()
    return render_template('contact.html', content=content)

@app.route('/contact_submit', methods=['POST'])
def contact_submit():
    try:
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        subject = request.form.get('subject', '')
        message = request.form.get('message', '').strip()
        if not name or not email or not message:
            return jsonify({'success': False, 'message': 'Please fill in all required fields.'})
        # Send message to spectraholi2026@gmail.com (or CONTACT_EMAIL)
        sent = send_contact_form_email(name, email, phone, subject, message)
        if sent:
            return jsonify({'success': True, 'message': 'Thank you for your message! We will get back to you within 2 hours.'})
        return jsonify({'success': False, 'message': 'Could not send email. Please try again or call us.'})
    except Exception as e:
        print(f"Contact submit error: {e}")
        return jsonify({'success': False, 'message': 'Could not send. Please try again.'})

@app.route('/booking')
def booking():
    return redirect(url_for('home') + '#booking')

@app.route('/admin')
def admin():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))
    bookings = Booking.find_all()
    
    # Calculate revenue with better fallback
    content = EventContent.get_content()
    pricing = content.get('pricing', {})
    
    total_revenue = 0
    for b in bookings:
        if b.get('payment_status') == 'Paid':
            amount = b.get('amount')
            if amount is not None:
                total_revenue += amount
            else:
                # Fallback
                p_type = b.get('pass_type', 'entry')
                price = 200
                if p_type == 'entry': price = pricing.get('entry_pass', 200)
                elif p_type == 'entry_starter': price = pricing.get('entry_plus_starter', 349)
                elif p_type == 'entry_starter_lunch': price = pricing.get('entry_plus_starter_lunch', 499)
                total_revenue += b.get('passes', 1) * price

    return render_template('admin.html', bookings=bookings, total_revenue=total_revenue, content=content)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == app.config['ADMIN_USERNAME'] and password == app.config['ADMIN_PASSWORD']:
            session['admin_logged_in'] = True
            return redirect(url_for('admin'))
        else:
            flash('Invalid credentials', 'error')
    return render_template('admin_login.html')

@app.route('/create_order', methods=['POST'])
def create_order():
    print("Create order called")
    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']
    address = request.form['address']
    passes = int(request.form['passes'])
    # Prefer radio button value (directly from user selection) over hidden field (JS updated)
    pass_type = request.form.get('pass_type_radio') or request.form.get('pass_type', 'entry')
    is_couple_booking = request.form.get('is_couple_booking') == 'true'
    
    # Calculate amount server-side (do not trust client)
    content = EventContent.get_content()
    pricing = content.get('pricing', {})
    
    price_per_pass = 200 # Absolute fallback
    if pass_type == 'entry':
        price_per_pass = pricing.get('entry_pass', 200)
    elif pass_type == 'entry_starter':
        price_per_pass = pricing.get('entry_plus_starter', 349)
    elif pass_type == 'entry_starter_lunch':
        price_per_pass = pricing.get('entry_plus_starter_lunch', 499)
        
    base_amount = passes * price_per_pass
    is_group_booking = passes >= 5
    
    # discount logic
    discount = 0
    discount_description = ""
    
    if passes >= 8:
        discount = int(base_amount * 0.15) # 15% off for 8+ passes
        is_group_booking = True
        discount_description = "15% Group Discount (8+ people)"
    elif passes >= 5:
        discount = int(base_amount * 0.10) # 10% off for 5-7 passes
        is_group_booking = True
        discount_description = "10% Group Discount (5+ people)"
    elif passes == 2 and is_couple_booking:
        discount = int(base_amount * 0.10) # 10% off for couples
        discount_description = "10% Couple Discount"
        
    amount = base_amount - discount

    print(f"Booking: {name}, {email}, {phone}, {address}, {passes} passes, {pass_type}, amount {amount}")

    ticket_id = str(uuid.uuid4())[:8].upper()
    booking = Booking(
        name=name, 
        email=email, 
        phone=phone, 
        address=address, 
        passes=passes, 
        ticket_id=ticket_id, 
        order_id=ticket_id, 
        payment_status='Pending', 
        pass_type=pass_type, 
        amount=amount, 
        is_group_booking=is_group_booking, 
        is_couple_booking=(passes == 2 and is_couple_booking),
        pricing=pricing,
        discount_description=discount_description
    )
    # Save to Google Sheet (primary), MongoDB (optional), and JSON (cache)
    booking.save()

    print(f"Booking saved with ticket_id: {ticket_id}")

    print("Redirecting to payment")
    return redirect(url_for('payment', ticket_id=ticket_id, amount=amount, name=name, passes=passes, pass_type=pass_type))

@app.route('/payment')
def payment():
    ticket_id = request.args.get('ticket_id')
    amount = int(request.args.get('amount', 0))
    name = request.args.get('name')
    passes = int(request.args.get('passes', 0))
    pass_type = request.args.get('pass_type', 'entry')
    return render_template('payment.html', ticket_id=ticket_id, amount=amount, name=name, passes=passes, pass_type=pass_type)

@app.route('/confirm_payment', methods=['POST'])
def confirm_payment():
    ticket_id = request.form['ticket_id']
    transaction_id = request.form.get('transaction_id', '').strip()

    booking = Booking.find_one(ticket_id=ticket_id)
    if booking:
        # Booking.update_one() now handles Google Sheet automatically (primary store)
        update_data = {'payment_status': 'Awaiting Verification'}
        if transaction_id:
            update_data['transaction_id'] = transaction_id
            
        Booking.update_one({'ticket_id': ticket_id}, {'$set': update_data})

    # Do not send ticket yet - wait for admin verification
    return render_template('success.html', awaiting_verification=True)

@app.route('/success')
def success():
    return render_template('success.html', awaiting_verification=False)

@app.route('/update_booking_status', methods=['POST'])
def update_booking_status():
    if 'admin_logged_in' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data provided'})
        
        ticket_id = data.get('ticket_id')
        new_status = data.get('status')

        if not ticket_id or not new_status:
            return jsonify({'success': False, 'message': 'Missing ticket_id or status'})

        booking = Booking.find_one(ticket_id=ticket_id)
        if not booking:
            return jsonify({'success': False, 'message': f'Booking with ticket ID {ticket_id} not found'})
        
        old_status = booking.get('payment_status', 'Pending')
        
        # Update booking (Google Sheet is PRIMARY, Mongo/JSON are optional fallbacks)
        result = Booking.update_one({'ticket_id': ticket_id}, {'$set': {'payment_status': new_status}})
        modified = getattr(result, 'modified_count', 0)
        
        # Google Sheet is primary, so update always succeeds if booking exists
        # If status changed to Paid and wasn't before, send ticket email
        if new_status == 'Paid' and old_status != 'Paid':
            content = EventContent.get_content()
            venue = content.get('venue', 'Kunjachaya, Bhadreswar')
            event_date = content.get('event_date', 'March 3, 2026')
            booking_with_venue = {**booking, 'venue': venue, 'event_date': event_date, 'payment_status': new_status, 'pricing': content.get('pricing', {})}
            
            email_sent = False
            try:
                # Generate PDF ticket
                pdf_buf = generate_ticket_pdf(booking_with_venue)
                
                # Create comprehensive email template with all booking and plan details
                email_body = create_success_email_template(booking_with_venue, content)
                
                # Send email with ticket attachment
                email_sent = send_email(
                    booking['email'], 
                    "🎉 Spectra HoliParty 2026 - Your Entry Pass Confirmed! 🎉", 
                    email_body, 
                    pdf_buf
                )
                if email_sent:
                    print(f"Ticket email sent successfully to {booking['email']} for {booking['ticket_id']}")
                else:
                    print(f"Failed to send ticket email to {booking['email']} for {booking['ticket_id']}")
            except Exception as e:
                print(f"Error sending ticket email: {e}")
                import traceback
                traceback.print_exc()
            
            # Return success (status updated in Google Sheet)
            return jsonify({
                'success': True, 
                'message': 'Status updated successfully' + (' and email sent' if email_sent else ' (email failed - check logs)')
            })
        
        # Status updated successfully (Google Sheet is primary)
        return jsonify({'success': True, 'message': 'Status updated successfully'})
            
    except Exception as e:
        print(f"update_booking_status error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/admin/content', methods=['GET', 'POST'])
def admin_content():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        # Update event content (do NOT delete existing fields; models.EventContent merges safely)
        gallery_images = [x.strip() for x in request.form.getlist('gallery_images[]') if str(x).strip()]
        content = {
            'event_date': request.form['event_date'],
            'registration_deadline': request.form.get('registration_deadline', 'February 28, 2026'),
            'event_time': request.form['event_time'],
            'venue': request.form['venue'],
            'organizer': request.form['organizer'],
            'complimentary': request.form['complimentary'],
            'pricing': {
                'entry_pass': int(request.form['entry_pass']),
                'entry_plus_starter': int(request.form['entry_plus_starter']),
                'entry_plus_starter_lunch': int(request.form.get('entry_plus_starter_lunch', 499)),
                'food_available': request.form['food_available']
            },
            'offers': request.form['offers'],
            'hero_image': request.form['hero_image'],
            # Only overwrite gallery if non-empty list was provided
            'gallery_images': gallery_images
        }
        EventContent.save_content(content)
        flash('Content updated successfully!', 'success')
        return redirect(url_for('admin_content'))
    
    content = EventContent.get_content()
    return render_template('admin_content.html', content=content)

@app.route('/delete_booking', methods=['POST'])
def delete_booking():
    if 'admin_logged_in' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    try:
        data = request.get_json()
        ticket_id = data.get('ticket_id')
        if not ticket_id:
            return jsonify({'success': False, 'message': 'No ticket ID provided'})
        
        # Delete from Mongo/JSON
        result = Booking.delete_one({'ticket_id': ticket_id})
        deleted_count = getattr(result, 'deleted_count', 0)
        
        # Also delete from Google Sheet (persistent store)
        sheet_deleted = False
        try:
            sheet_deleted = delete_booking_from_sheet(ticket_id)
        except Exception as e:
            print(f"Sheet delete failed (non-fatal): {e}")
        
        # Return success if deleted from either store
        if deleted_count > 0 or sheet_deleted:
            return jsonify({'success': True, 'message': 'Booking deleted successfully'})
        
        # Check if booking exists at all
        booking_exists = Booking.find_one(ticket_id=ticket_id)
        if not booking_exists:
            # Booking doesn't exist, consider it already deleted
            return jsonify({'success': True, 'message': 'Booking not found (may already be deleted)'})
        
        return jsonify({'success': False, 'message': 'Failed to delete booking'})
    except Exception as e:
        print(f"Delete booking error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/admin_send_mail', methods=['POST'])
def admin_send_mail():
    if 'admin_logged_in' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    try:
        data = request.get_json()
        ticket_id = data.get('ticket_id')
        mail_type = data.get('mail_type')  # 'success' or 'failure'
        if not ticket_id or mail_type not in ('success', 'failure'):
            return jsonify({'success': False, 'message': 'Invalid request data'})
        
        booking = Booking.find_one(ticket_id=ticket_id)
        if not booking:
            return jsonify({'success': False, 'message': f'Booking with ticket ID {ticket_id} not found'})
        
        # Check email configuration based on provider
        email_provider = getattr(Config, 'EMAIL_PROVIDER', None) or 'resend'
        if email_provider == 'smtp':
            email_user = getattr(Config, 'EMAIL_USER', None) or ''
            email_pass = getattr(Config, 'EMAIL_PASS', None) or ''
            if not email_user or not email_pass:
                return jsonify({
                    'success': False, 
                    'message': 'Email not configured. Set EMAIL_USER and EMAIL_PASS for SMTP, or change EMAIL_PROVIDER.'
                })
        elif email_provider == 'sendgrid':
            api_key = getattr(Config, 'SENDGRID_API_KEY', None) or ''
            if not api_key:
                return jsonify({
                    'success': False, 
                    'message': 'Email not configured. Set SENDGRID_API_KEY, or change EMAIL_PROVIDER.'
                })
        elif email_provider == 'mailgun':
            api_key = getattr(Config, 'MAILGUN_API_KEY', None) or ''
            domain = getattr(Config, 'MAILGUN_DOMAIN', None) or ''
            if not api_key or not domain:
                return jsonify({
                    'success': False, 
                    'message': 'Email not configured. Set MAILGUN_API_KEY and MAILGUN_DOMAIN, or change EMAIL_PROVIDER.'
                })
        else:  # resend (default)
            resend_api_key = getattr(Config, 'RESEND_API_KEY', None) or ''
            resend_from = getattr(Config, 'RESEND_FROM_EMAIL', None) or ''
            if not resend_api_key or not resend_from:
                return jsonify({
                    'success': False, 
                    'message': 'Email not configured. Set RESEND_API_KEY and RESEND_FROM_EMAIL, or set EMAIL_PROVIDER=smtp to use Gmail.'
                })
        
        content = EventContent.get_content()
        venue = content.get('venue', 'Kunjachaya, Bhadreswar')
        event_date = content.get('event_date', 'March 3, 2026')
        booking_with_venue = {**booking, 'venue': venue, 'event_date': event_date, 'pricing': content.get('pricing', {})}
        
        if mail_type == 'success':
            try:
                # Generate PDF ticket
                pdf_buf = generate_ticket_pdf(booking_with_venue)
                
                # Create comprehensive email template with all booking and plan details
                email_body = create_success_email_template(booking_with_venue, content)
                
                # Send email with ticket attachment via Resend
                sent = send_email(
                    booking['email'], 
                    "🎉 Spectra HoliParty 2026 - Your Entry Pass Confirmed! 🎉", 
                    email_body, 
                    pdf_buf
                )
                if sent:
                    provider = getattr(Config, 'EMAIL_PROVIDER', None) or 'resend'
                    return jsonify({'success': True, 'message': f'Email sent successfully via {provider.upper()}!'})
                else:
                    provider = getattr(Config, 'EMAIL_PROVIDER', None) or 'resend'
                    if provider == 'resend':
                        return jsonify({
                            'success': False, 
                            'message': (
                                'Email not sent. With onboarding@resend.dev you can only send to your Resend account email. '
                                'To send to customers, verify a domain at resend.com/domains OR set EMAIL_PROVIDER=smtp to use Gmail.'
                            )
                        })
                    else:
                        return jsonify({
                            'success': False, 
                            'message': f'Email send failed. Check Render logs for details. Provider: {provider.upper()}'
                        })
            except Exception as e:
                print(f"Error generating PDF or sending email: {e}")
                import traceback
                traceback.print_exc()
                return jsonify({'success': False, 'message': f'Error: {str(e)}'})
        else:
            body = f"""
            <h2>Dear {booking['name']},</h2>
            <p>Greetings from <strong>Spectra Team</strong>!</p>
            <p>We noticed your booking for <strong>Spectra HoliParty 2026</strong> (Ticket ID: {booking['ticket_id']}) could not be confirmed due to payment verification issues.</p>
            {f"<p>Transaction ID submitted: {booking.get('transaction_id', 'Not provided')}</p>" if booking.get('transaction_id') else ""}
            <p>If you have already made the payment, please contact us with your Ticket ID for manual verification.</p>
            <p>For any queries, reach us at the numbers on our website.</p>
            <p>— Spectra HoliParty Team</p>
            """
            sent = send_email(booking['email'], "Spectra HoliParty 2026 - Payment Verification Required", body)
            if sent:
                return jsonify({'success': True, 'message': 'Email sent successfully!'})
            else:
                return jsonify({
                    'success': False, 
                    'message': 'Email send failed. Check Render logs for details.'
                })
    except Exception as e:
        print(f"Admin send mail error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@app.route('/export_bookings')
def export_bookings():
    import pandas as pd
    bookings = Booking.find_all()

    data = []
    for booking in bookings:
        bdate = booking.get('booking_date', '')
        if not bdate and booking.get('_id') and hasattr(booking['_id'], 'generation_time'):
            try:
                bdate = booking['_id'].generation_time.replace(tzinfo=None).strftime('%Y-%m-%d %H:%M:%S')
            except Exception:
                bdate = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if not bdate:
            bdate = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        data.append({
            'Name': booking.get('name', ''),
            'Email': booking.get('email', ''),
            'Phone': booking.get('phone', ''),
            'Ticket ID': booking.get('ticket_id', ''),
            'Passes': booking.get('passes', 0),
            'Amount': booking.get('amount', booking.get('passes', 0) * 200),
            'Payment Status': booking.get('payment_status', 'Pending'),
            'Entry Status': booking.get('entry_status', 'Not Used'),
            'Booking Date': bdate,
            'Pass Type': booking.get('pass_type', 'entry'),
            'Transaction ID': booking.get('transaction_id', ''),
            'Discount Info': booking.get('discount_description', ''),
        })

    rows = [[r['Name'], r['Email'], r['Phone'], r['Ticket ID'], r['Passes'], r['Amount'], r['Payment Status'], r['Entry Status'], str(r['Booking Date']), r['Pass Type'], r['Transaction ID'], r['Discount Info']] for r in data]
    export_to_google_sheets(rows)

    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Bookings', index=False)

    output.seek(0)

    # Return file for download
    from flask import send_file
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='holi_party_bookings.xlsx'
    )

if __name__ == '__main__':
    app.run(debug=True)
