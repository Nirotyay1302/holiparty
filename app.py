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
    
    email_user = getattr(Config, 'EMAIL_USER', None) or ''
    email_pass = getattr(Config, 'EMAIL_PASS', None) or ''
    
    config_status = {
        'EMAIL_USER_set': bool(email_user),
        'EMAIL_USER_value': email_user[:5] + '...' if email_user else 'NOT SET',
        'EMAIL_PASS_set': bool(email_pass),
        'EMAIL_PASS_length': len(email_pass) if email_pass else 0,
        'is_gmail': '@gmail.com' in email_user.lower() if email_user else False,
    }
    
    # Try to send a test email
    test_result = None
    if email_user and email_pass:
        try:
            test_body = "<p>This is a test email from Spectra HoliParty admin panel.</p>"
            test_result = send_email(email_user, "Test Email - Spectra HoliParty", test_body)
        except Exception as e:
            test_result = f"Error: {str(e)}"
    
    return jsonify({
        'config': config_status,
        'test_email_sent': test_result,
        'instructions': {
            'step1': 'Go to https://myaccount.google.com/apppasswords',
            'step2': 'Generate App Password for "Mail"',
            'step3': 'Copy the 16-character password',
            'step4': 'Set EMAIL_USER and EMAIL_PASS in Render Environment Variables',
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
from utils.email_utils import send_email
from utils.qr_utils import generate_qr
from utils.excel_utils import update_sheet, export_to_google_sheets, sync_sheet_after_delete, upsert_booking_row, delete_booking_from_sheet
from utils.ticket_utils import generate_ticket_pdf

# Razorpay client
# razorpay_client = razorpay.Client(auth=(app.config['RAZORPAY_KEY_ID'], app.config['RAZORPAY_KEY_SECRET']))

# Admin credentials (in production, use environment variables)
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = 'holi2026'

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
        # Store or email logic could go here; for now acknowledge receipt
        return jsonify({'success': True, 'message': 'Thank you for your message! We will get back to you within 2 hours.'})
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
    total_revenue = sum(b.get('amount', b.get('passes', 0) * 200) for b in bookings if b.get('payment_status') == 'Paid')
    return render_template('admin.html', bookings=bookings, total_revenue=total_revenue)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
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
    pass_type = request.form.get('pass_type', 'entry')
    amount = int(request.form.get('amount', passes * 200))
    is_group_booking = passes >= 5

    print(f"Booking: {name}, {email}, {phone}, {address}, {passes} passes, {pass_type}, amount {amount}")

    ticket_id = str(uuid.uuid4())[:8].upper()
    booking = Booking(name=name, email=email, phone=phone, address=address, passes=passes, ticket_id=ticket_id, order_id=ticket_id, payment_status='Pending', pass_type=pass_type, amount=amount, is_group_booking=is_group_booking)
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

    booking = Booking.find_one(ticket_id=ticket_id)
    if booking:
        # Booking.update_one() now handles Google Sheet automatically (primary store)
        Booking.update_one({'ticket_id': ticket_id}, {'$set': {'payment_status': 'Awaiting Verification'}})

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
            venue = content.get('venue', 'Dighi Garden Mankundu')
            booking_with_venue = {**booking, 'venue': venue, 'payment_status': new_status}
            
            email_sent = False
            try:
                pdf_buf = generate_ticket_pdf(booking_with_venue)
                body = f"""
                <h2>Dear {booking['name']},</h2>
                <p>Your <strong>Spectra HoliParty 2026</strong> entry pass is now confirmed!</p>
                <p>Your ticket is attached. Ticket ID: <strong>{booking['ticket_id']}</strong> | Amount: <strong>₹{booking.get('amount', booking['passes'] * 200)}</strong></p>
                <p>Event: March 4, 2026 | 10:00 AM - 5:00 PM | {venue}</p>
                <p>Show the QR code at the gate for entry. We look forward to celebrating with you!</p>
                <p>— Spectra HoliParty Team</p>
                """
                email_sent = send_email(booking['email'], "🎉 Spectra HoliParty 2026 - Your Entry Pass 🎉", body, pdf_buf)
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
        
        # Check email configuration
        email_user = getattr(Config, 'EMAIL_USER', None) or ''
        email_pass = getattr(Config, 'EMAIL_PASS', None) or ''
        if not email_user or not email_pass:
            return jsonify({
                'success': False, 
                'message': 'Email not configured. Set EMAIL_USER and EMAIL_PASS in Render Environment Variables.'
            })
        
        content = EventContent.get_content()
        venue = content.get('venue', 'Dighi Garden Mankundu')
        booking_with_venue = {**booking, 'venue': venue}
        
        if mail_type == 'success':
            try:
                pdf_buf = generate_ticket_pdf(booking_with_venue)
                body = f"""
                <h2>Dear {booking['name']},</h2>
                <p>Greetings from <strong>Spectra Team</strong>!</p>
                <p>Your <strong>Spectra HoliParty 2026</strong> entry pass is confirmed.</p>
                <p>Your ticket is attached with <strong>Ticket ID: {booking['ticket_id']}</strong> and <strong>Amount: ₹{booking.get('amount', booking['passes'] * 200)}</strong>.</p>
                <p>Event: March 4, 2026 | 10:00 AM - 5:00 PM | {venue}</p>
                <p>Show the QR code at the gate for entry. We look forward to celebrating with you!</p>
                <p>— Spectra HoliParty Team</p>
                """
                sent = send_email(booking['email'], "🎉 Spectra HoliParty 2026 - Your Entry Pass 🎉", body, pdf_buf)
                if sent:
                    return jsonify({'success': True, 'message': 'Email sent successfully!'})
                else:
                    return jsonify({
                        'success': False, 
                        'message': 'Email send failed. Check Render logs for details. Ensure EMAIL_USER and EMAIL_PASS are set correctly (use Gmail App Password).'
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
        data.append({
            'Name': booking['name'],
            'Email': booking['email'],
            'Phone': booking['phone'],
            'Ticket ID': booking['ticket_id'],
            'Passes': booking['passes'],
            'Amount': booking.get('amount', booking['passes'] * 200),
            'Payment Status': booking['payment_status'],
            'Entry Status': booking.get('entry_status', 'Not Used'),
            'Booking Date': (booking.get('_id').generation_time.replace(tzinfo=None) if booking.get('_id') else datetime.now())
        })

    export_to_google_sheets([[row['Name'], row['Email'], row['Phone'], row['Ticket ID'], row['Passes'], row['Amount'], row['Payment Status'], row['Entry Status'], str(row['Booking Date'])] for row in data])

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
