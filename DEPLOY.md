# Deploy to GitHub

## Push to https://github.com/Nirotyay1302/holiparty.git

Run these commands in your project folder (`d:\holi`):

```bash
# Initialize git (if not already)
git init

# Add all files
git add .

# Commit
git commit -m "Spectra HoliParty 2026 - Full website with booking, UPI/QR payment, ticket system"

# Add remote (if not added)
git remote add origin https://github.com/Nirotyay1302/holiparty.git

# Push to GitHub
git branch -M main
git push -u origin main
```

If the repo already has a remote:
```bash
git remote -v
git push origin main
```

## Environment Variables for Production

Set these when deploying (e.g., Render, Heroku):
- `SECRET_KEY` - Random secret for sessions
- `MONGO_URI` - MongoDB connection string
- `RAZORPAY_KEY_ID` - Razorpay key
- `RAZORPAY_KEY_SECRET` - Razorpay secret
- `EMAIL_USER` - Gmail for sending tickets
- `EMAIL_PASS` - Gmail app password
- `GOOGLE_SHEET_ID` - 13oh5EqMrsnNOqCGqKzDNzHgy4p9gRGXz6JDVK7XyKew (spectra holi sheet)
- `GOOGLE_CREDS_PATH` - Path to creds.json (or use service account JSON as env)
