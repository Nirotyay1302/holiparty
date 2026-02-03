# Deploy to GitHub & Netlify

## Push to https://github.com/Nirotyay1302/holiparty.git

```bash
git add .
git commit -m "Spectra HoliParty 2026 - UPI/QR payment, no Razorpay"
git push origin main
```

## Netlify Hosting

1. Go to [netlify.com](https://netlify.com) → Add new site → Import from Git
2. Connect your GitHub repo: **Nirotyay1302/holiparty**
3. Build settings: Leave default (netlify.toml is in repo)
4. **Important:** Netlify hosts static sites. This is a **Flask app** – for booking, payment, admin, and emails you need a Python backend.

### Recommended: Deploy backend to Render (free)

1. Go to [render.com](https://render.com) → New Web Service
2. Connect GitHub repo
3. Build: `pip install -r requirements.txt`
4. Start: `python app.py` (or use gunicorn: `gunicorn app:app`)
5. Add environment variables (SECRET_KEY, MONGO_URI, EMAIL_USER, EMAIL_PASS, GOOGLE_SHEET_ID, GOOGLE_CREDS_PATH)
6. Deploy – you get a URL like `https://holiparty.onrender.com`

Then either:
- Use the Render URL directly (full site), OR
- Host static pages on Netlify and point forms to your Render backend URL

## Environment Variables

- `SECRET_KEY` - Random secret for sessions
- `MONGO_URI` - MongoDB connection string
- `EMAIL_USER` - Gmail for sending tickets
- `EMAIL_PASS` - Gmail app password
- `GOOGLE_SHEET_ID` - 13oh5EqMrsnNOqCGqKzDNzHgy4p9gRGXz6JDVK7XyKew
- `GOOGLE_CREDS_PATH` - creds.json path
