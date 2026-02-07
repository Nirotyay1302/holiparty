# Spectra HoliParty 2026

A complete web application for promoting and managing bookings for Spectra HoliParty – **our 2nd year** of organizing! Event at **Kunjachaya, Bhadreswar** | Schedule: **10:00 AM – 5:00 PM**

## Features

- Event promotion page with Previous Year Photos
- Online booking with **3 pass types**: Entry (₹200), Entry+Starter (₹349), Entry+Starter+Lunch (₹499)
- **Group booking**: 10% discount for 5+ members
- Razorpay + **UPI/QR payment** (7278737263@jio)
- Automatic email tickets with name, Ticket ID, amount highlighted
- Auto-updating [Google Sheets](https://docs.google.com/spreadsheets/d/13oh5EqMrsnNOqCGqKzDNzHgy4p9gRGXz6JDVK7XyKew) for bookings
- MongoDB database for records

## Setup Instructions

### Prerequisites
- Python 3.8+
- MongoDB Atlas account
- Resend account (for emails) - [resend.com](https://resend.com)
- Google Cloud account for Sheets API

### Local Development

1. Clone or download the project files.

2. Create a virtual environment:
   ```
   python -m venv venv
   venv\Scripts\activate  # On Windows
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file or set environment variables:
   ```
   SECRET_KEY=your-secret-key
   MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/holi_party
   RESEND_API_KEY=your-resend-api-key
   RESEND_FROM_EMAIL=onboarding@resend.dev
   GOOGLE_SHEET_ID=your-google-sheet-id
   GOOGLE_CREDS_PATH=path/to/creds.json
   ```

5. For Google Sheets:
   - Create a Google Sheet and copy its ID from the URL.
   - Create a service account in Google Cloud Console.
   - Download the JSON credentials file and place it in the project root as `creds.json`.
   - Share the Google Sheet with the service account email.

6. For Resend Email:
   - Sign up at [resend.com](https://resend.com) (free tier: 3,000 emails/month)
   - Get API key from [resend.com/api-keys](https://resend.com/api-keys)
   - For testing: Use `onboarding@resend.dev` (works immediately)
   - For production: Verify your domain (see RESEND_SETUP.md for details)

7. Run the application:
   ```
   python app.py
   ```

8. Open http://localhost:5000 in your browser.

### Hosting

#### Frontend (Netlify)
- Upload the `static` and `templates` folders to Netlify.
- For a full-stack deployment, consider using a platform that supports Python.

#### Backend (Render)
- Create a Render account.
- Connect your GitHub repository.
- Set environment variables in Render dashboard.
- Deploy the Flask app.

#### Database (MongoDB Atlas)
- Create a free cluster.
- Get the connection string and set as MONGO_URI.

#### Payment (Razorpay)
- Sign up for Razorpay.
- Get API keys and set in environment.

#### Email (Resend API)
- Sign up at [resend.com](https://resend.com)
- Get API key and set RESEND_API_KEY
- Set RESEND_FROM_EMAIL (use `onboarding@resend.dev` for testing)
- See RESEND_SETUP.md for detailed setup guide

#### Excel Update (Google Sheets)
- As described in setup.

## Usage

1. Visit the home page for event details.
2. View the gallery for previous year photos.
3. Click "Book Now" to fill the form and pay via Razorpay.
4. After payment, receive an email with the PDF ticket containing QR code.
5. The booking is automatically added to your Google Sheet.

## Security Notes

- Change the SECRET_KEY in production.
- Use HTTPS in production.
- Validate all inputs on the server side.
- Store credentials securely.

## Troubleshooting

- If emails don't send, check Resend API key and RESEND_FROM_EMAIL settings. See RESEND_SETUP.md for troubleshooting.
- If payments fail, verify Razorpay keys.
- If database connection fails, check MongoDB URI.
- If Google Sheets update fails, check credentials and sheet sharing.

## License

This project is for educational purposes. Modify as needed.