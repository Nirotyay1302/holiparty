from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from config import Config
from models import Booking, EventContent
from utils.email_utils import send_email
from utils.qr_utils import generate_qr
from utils.excel_utils import update_sheet, export_to_google_sheets
from utils.ticket_utils import generate_ticket_pdf
import uuid
import io
import pandas as pd
from datetime import datetime
import razorpay

app = Flask(__name__)
app.config.from_object(Config)

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
    booking.save()

    print(f"Booking saved with ticket_id: {ticket_id}")

    # Create Razorpay order
    try:
        razorpay_client = razorpay.Client(auth=(app.config['RAZORPAY_KEY_ID'], app.config['RAZORPAY_KEY_SECRET']))
        razorpay_order = razorpay_client.order.create({
            'amount': amount * 100,  # Amount in paisa
            'currency': 'INR',
            'payment_capture': '1'  # Auto capture
        })
        print(f"Razorpay order created: {razorpay_order['id']}")
    except Exception as e:
        print(f"Razorpay error: {e}")
        # Fallback to test order
        razorpay_order = {'id': 'test_order_' + ticket_id}

    # Update booking with razorpay order id
    Booking.update_one({'ticket_id': ticket_id}, {'$set': {'razorpay_order_id': razorpay_order['id']}})

    print("Redirecting to payment")

    # Redirect to payment page with data
    return redirect(url_for('payment', ticket_id=ticket_id, amount=amount, name=name, passes=passes, order_id=razorpay_order['id'], pass_type=pass_type))

@app.route('/payment')
def payment():
    ticket_id = request.args.get('ticket_id')
    amount = int(request.args.get('amount', 0))
    name = request.args.get('name')
    passes = int(request.args.get('passes', 0))
    order_id = request.args.get('order_id')
    pass_type = request.args.get('pass_type', 'entry')

    return render_template('payment.html', ticket_id=ticket_id, amount=amount, name=name, passes=passes, order_id=order_id, pass_type=pass_type, razorpay_key=app.config['RAZORPAY_KEY_ID'])

@app.route('/payment_success', methods=['POST'])
def payment_success():
    data = request.get_json()
    ticket_id = data.get('ticket_id')
    payment_id = data.get('razorpay_payment_id')
    order_id = data.get('razorpay_order_id')
    signature = data.get('razorpay_signature')

    # Verify payment signature
    # params_dict = {
    #     'razorpay_order_id': order_id,
    #     'razorpay_payment_id': payment_id,
    #     'razorpay_signature': signature
    # }

    # Verify payment signature
    if not order_id.startswith('test_'):
        razorpay_client = razorpay.Client(auth=(app.config['RAZORPAY_KEY_ID'], app.config['RAZORPAY_KEY_SECRET']))
        params_dict = {
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        }

        try:
            razorpay_client.utility.verify_payment_signature(params_dict)
        except:
            return jsonify({'success': False})
    
    # Payment verified, update status and send ticket
    booking = Booking.find_one(ticket_id=ticket_id)
    if booking:
        content = EventContent.get_content()
        venue = content.get('venue', 'Mankundu Amrakunja Park')
        booking_with_venue = {**booking, 'venue': venue}
        Booking.update_one({'ticket_id': ticket_id}, {'$set': {'payment_status': 'Paid', 'razorpay_payment_id': payment_id}})

        try:
            pdf_buf = generate_ticket_pdf(booking_with_venue)
            body = f"""
            <h2>Dear {booking['name']},</h2>
            <p>Thank you for your payment! Your <strong>Spectra HoliParty 2026</strong> entry pass is confirmed.</p>
            <p>Your ticket is attached with your <strong>Ticket ID: {booking['ticket_id']}</strong> and <strong>Amount: ₹{booking.get('amount', booking['passes'] * 200)}</strong>.</p>
            <p>Show the QR code at the gate for entry. Event: March 4, 2026 | 10:00 AM - 5:00 PM | {venue}</p>
            """
            send_email(booking['email'], "🎉 Spectra HoliParty 2026 - Your Entry Pass 🎉", body, pdf_buf)
        except Exception as e:
            print(f"Ticket/email send error: {e}")

        booking_amount = booking.get('amount', booking['passes'] * 200)
        from datetime import datetime
        update_sheet([booking['name'], booking['email'], booking['phone'], booking['ticket_id'], booking['passes'], booking_amount, 'Paid', 'Not Used', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])

    return jsonify({'success': True})

@app.route('/confirm_payment', methods=['POST'])
def confirm_payment():
    ticket_id = request.form['ticket_id']

    booking = Booking.find_one(ticket_id=ticket_id)
    if booking:
        Booking.update_one({'ticket_id': ticket_id}, {'$set': {'payment_status': 'Awaiting Verification'}})

    # Do not send ticket yet - wait for admin verification
    return render_template('success.html', awaiting_verification=True)

@app.route('/success')
def success():
    return render_template('success.html', awaiting_verification=False)

@app.route('/update_booking_status', methods=['POST'])
def update_booking_status():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False})
        ticket_id = data.get('ticket_id')
        new_status = data.get('status')

        if not ticket_id or not new_status:
            return jsonify({'success': False})

        booking = Booking.find_one(ticket_id=ticket_id)
        if not booking:
            return jsonify({'success': False})
        old_status = booking.get('payment_status')

        result = Booking.update_one({'ticket_id': ticket_id}, {'$set': {'payment_status': new_status}})
        modified = getattr(result, 'modified_count', 1)
        if True:  # Proceed - update attempted
            # If status changed to Paid and wasn't before, send ticket
            if new_status == 'Paid' and old_status != 'Paid':
                content = EventContent.get_content()
                venue = content.get('venue', 'Mankundu Amrakunja Park')
                booking_with_venue = {**booking, 'venue': venue}
                try:
                    pdf_buf = generate_ticket_pdf(booking_with_venue)
                    body = f"""
                    <h2>Dear {booking['name']},</h2>
                    <p>Your <strong>Spectra HoliParty 2026</strong> entry pass is now confirmed!</p>
                    <p>Your ticket is attached. Ticket ID: <strong>{booking['ticket_id']}</strong> | Amount: <strong>₹{booking.get('amount', booking['passes'] * 200)}</strong></p>
                    <p>Event: March 4, 2026 | 10:00 AM - 5:00 PM | {venue}</p>
                    """
                    send_email(booking['email'], "🎉 Spectra HoliParty 2026 - Your Entry Pass 🎉", body, pdf_buf)
                    booking_amount = booking.get('amount', booking['passes'] * 200)
                    update_sheet([booking['name'], booking['email'], booking['phone'], booking['ticket_id'], booking['passes'], booking_amount, 'Paid', 'Not Used', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
                except Exception as e:
                    print(f"Admin ticket send error: {e}")

            return jsonify({'success': True})
    except Exception as e:
        print(f"update_booking_status error: {e}")
    return jsonify({'success': False})

@app.route('/admin/content', methods=['GET', 'POST'])
def admin_content():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin_login'))
    
    if request.method == 'POST':
        # Update event content
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
            'gallery_images': request.form.getlist('gallery_images[]')
        }
        EventContent.save_content(content)
        flash('Content updated successfully!', 'success')
        return redirect(url_for('admin_content'))
    
    content = EventContent.get_content()
    return render_template('admin_content.html', content=content)

@app.route('/export_bookings')
def export_bookings():
    bookings = Booking.find_all()

    # Convert to DataFrame
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

    # Sync to Google Sheets
    bookings_list = [[row['Name'], row['Email'], row['Phone'], row['Ticket ID'], row['Passes'], row['Amount'], row['Payment Status'], row['Entry Status'], str(row['Booking Date'])] for row in data]
    export_to_google_sheets(bookings_list)

    df = pd.DataFrame(data)

    # Create Excel file
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
