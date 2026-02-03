# Spectra HoliParty – Hosting Guide

## Option 1: Render (Recommended – Free Tier)

Render supports Python/Flask and offers a free tier.

### Steps

1. **Push code to GitHub**
   ```bash
   git add .
   git commit -m "Ready for deployment"
   git push origin main
   ```

2. **Create Render account** at [render.com](https://render.com)

3. **New Web Service**
   - Dashboard → **New** → **Web Service**
   - Connect your GitHub and select **holiparty** (or your repo)
   - Settings:
     - **Name:** spectra-holiparty
     - **Region:** Oregon (US West) or Singapore
     - **Branch:** main
     - **Runtime:** Python 3
     - **Build command:** `pip install -r requirements.txt`
     - **Start command:** `gunicorn app:app`

4. **Environment variables** (Dashboard → Environment)
   | Key | Value |
   |-----|-------|
   | `SECRET_KEY` | Random string (e.g. `openssl rand -hex 32`) |
   | `MONGO_URI` | Your MongoDB connection string |
   | `EMAIL_USER` | Your Gmail address |
   | `EMAIL_PASS` | Gmail app password |
   | `GOOGLE_SHEET_ID` | `13oh5EqMrsnNOqCGqKzDNzHgy4p9gRGXz6JDVK7XyKew` |
   | `GOOGLE_CREDS_PATH` | `creds.json` (upload creds as Secret File) |

5. **Google Sheets service account**
   - Create a Secret File on Render
   - Name: `creds.json`
   - Upload your Google service account JSON
   - Render will place it at `/etc/secrets/creds.json`
   - Set: `GOOGLE_CREDS_PATH=/etc/secrets/creds.json`

6. **Deploy**  
   Click **Create Web Service**. After the build, your site will be live at  
   `https://spectra-holiparty.onrender.com` (or similar).

---

## Option 2: Railway

1. Go to [railway.app](https://railway.app)
2. **New Project** → **Deploy from GitHub** → Select repo
3. Add variables: `SECRET_KEY`, `MONGO_URI`, `EMAIL_USER`, `EMAIL_PASS`, etc.
4. Railway auto-detects Python. Start command: `gunicorn app:app`

---

## Option 3: PythonAnywhere (Free Tier)

1. Sign up at [pythonanywhere.com](https://pythonanywhere.com)
2. **Web** tab → **Add a new web app** → Flask
3. Clone your repo or upload files
4. Configure WSGI to point to your app
5. Set environment variables in the web app config

---

## Option 4: Netlify + Backend

Netlify is for static sites. For this Flask app:

- **Option A:** Deploy only the backend on Render/Railway and use that URL.
- **Option B:** Use Netlify Functions (requires significant restructuring).

---

## Post-Deploy Checklist

- [ ] Test booking flow
- [ ] Test payment confirmation (UPI/QR)
- [ ] Test admin login and status update
- [ ] Test contact form
- [ ] Verify email sending (Gmail app password)
- [ ] Verify Google Sheet sync
- [ ] Add custom domain (if needed)

---

## Environment Variables Summary

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | Yes | Random secret for sessions |
| `MONGO_URI` | Yes | MongoDB Atlas connection string |
| `EMAIL_USER` | Yes | Gmail for ticket emails |
| `EMAIL_PASS` | Yes | Gmail app password |
| `GOOGLE_SHEET_ID` | Yes | `13oh5EqMrsnNOqCGqKzDNzHgy4p9gRGXz6JDVK7XyKew` |
| `GOOGLE_CREDS_PATH` | Yes | Path to `creds.json` (service account) |
