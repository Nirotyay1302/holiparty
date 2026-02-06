# Spectra HoliParty – Render Deployment Guide

## Render Deployment (Step-by-Step)

### 1. Push to GitHub

```bash
cd d:\holi
git add .
git commit -m "Deploy to Render"
git push origin main
```

### 2. Create Render Account

Go to [render.com](https://render.com) and sign up (GitHub login recommended).

### 3. Create Web Service

1. **Dashboard** → **New** → **Web Service**
2. Connect GitHub and select **Nirotyay1302/holiparty**
3. Configure:
   - **Name:** spectra-holiparty
   - **Region:** Singapore (or Oregon for US)
   - **Branch:** main
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`

### 4. Add Environment Variables

In **Environment** tab, add:

| Key | Value |
|-----|-------|
| `SECRET_KEY` | Any random string (e.g. `spectra-holi-2026-secret-key-change-me`) |
| `MONGO_URI` | `mongodb+srv://nirotyaymukherjee563_db_user:YOUR_PASSWORD@cluster0.zyixrsi.mongodb.net/?appName=Cluster0` |
| `RESEND_API_KEY` | Your Resend API key (e.g. `re_Hf3zZg8z_84by2NfLKGNCkGFqubhShAZM`) |
| `RESEND_FROM_EMAIL` | `onboarding@resend.dev` (for testing) or your verified domain email |
| `GOOGLE_SHEET_ID` | `13oh5EqMrsnNOqCGqKzDNzHgy4p9gRGXz6JDVK7XyKew` |
| `GOOGLE_CREDS_PATH` | `creds.json` |

> **📧 Resend Email Setup (See RESEND_SETUP.md for detailed guide):** 
> - **Quick Start (Testing):** Use `onboarding@resend.dev` - works immediately, no setup needed!
> - **Production:** Get a custom domain and verify it with Resend (see RESEND_SETUP.md)
> - **Important:** Resend does NOT support Gmail addresses. You need a custom domain for production.
> - Sign up at [resend.com](https://resend.com) (free tier: 3,000 emails/month)
> - Get API key from [resend.com/api-keys](https://resend.com/api-keys)

### 5. Google Sheets Credentials (Secret File)

1. In your Web Service → **Environment** tab
2. Scroll to **Secret Files**
3. Click **Add Secret File**
4. **Filename:** `creds.json`
5. **Contents:** Paste your full Google service account JSON
6. Set env var: `GOOGLE_CREDS_PATH` = `creds.json` (Render mounts it in the app root)

> **Resend Email Setup:** 
> - Sign up at [resend.com](https://resend.com) (free tier: 3,000 emails/month)
> - Get API key from [resend.com/api-keys](https://resend.com/api-keys)
> - Set `RESEND_API_KEY` and `RESEND_FROM_EMAIL` in Render environment variables
> - For testing, use `onboarding@resend.dev` as RESEND_FROM_EMAIL
> - For production, verify your domain at [resend.com/domains](https://resend.com/domains)
> - **If ticket emails fail:** Check Render logs for Resend errors. Ensure RESEND_API_KEY and RESEND_FROM_EMAIL are set correctly.

### 6. Deploy

Click **Create Web Service**. Wait 2–3 minutes. Your site will be at:

**https://spectra-holiparty.onrender.com**

### 7. Free Tier Notes

- Service sleeps after 15 min of no traffic (first load may take 30–60 sec)
- 750 free hours/month

### 8. Prevent Cold Starts (Keep Site Awake)

Use [UptimeRobot](https://uptimerobot.com) (free):

1. Create account at uptimerobot.com
2. **Add New Monitor**
3. **Monitor Type:** HTTP(s)
4. **URL:** `https://YOUR-APP.onrender.com/ping`
5. **Monitoring Interval:** 5 minutes
6. Save

This pings your site every 5 min so it never sleeps. Response is instant.

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
- [ ] Verify email sending (Resend API - check RESEND_SETUP.md for details)
- [ ] Verify Google Sheet sync
- [ ] Add custom domain (if needed)

---

## Environment Variables Summary

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | Yes | Random secret for sessions |
| `MONGO_URI` | Yes | MongoDB Atlas connection string |
| `RESEND_API_KEY` | Yes | Resend API key from [resend.com/api-keys](https://resend.com/api-keys) |
| `RESEND_FROM_EMAIL` | Yes | Verified sender email (use `onboarding@resend.dev` for testing) |
| `GOOGLE_SHEET_ID` | Yes | `13oh5EqMrsnNOqCGqKzDNzHgy4p9gRGXz6JDVK7XyKew` |
| `GOOGLE_CREDS_PATH` | Yes | Path to `creds.json` (service account) |
| `CONTACT_EMAIL` | No | Inbox for contact form (default: spectraholi2026@gmail.com) |
