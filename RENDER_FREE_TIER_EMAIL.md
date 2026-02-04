# 📧 Best Email Provider for Render Free Tier

## ⚠️ Important: Render Free Tier Blocks SMTP

**Render blocks outbound traffic to SMTP ports (25, 465, 587) on free tier** ([Render Changelog](https://render.com/changelog/free-web-services-will-no-longer-allow-outbound-traffic-to-smtp-ports)).

So **Gmail SMTP will NOT work** on Render free tier. You must use an **HTTPS/API-based** email provider.

---

## ✅ Best Choice for Render Free Tier: **SendGrid**

| Feature | SendGrid | Resend (test) | Mailgun |
|--------|----------|----------------|---------|
| Works on Render free tier | ✅ Yes (HTTPS API) | ✅ Yes (HTTPS API) | ✅ Yes (HTTPS API) |
| Send to any customer | ✅ Yes | ❌ No (only your email) | ✅ Yes* |
| Domain required? | ❌ No (Single Sender) | ✅ Yes (for customers) | ✅ Yes |
| Free tier | **100 emails/day** | 3,000/month (test only) | 1,000/month* |
| Setup time | ~10 min | Instant (test) / Domain (prod) | ~15 min |

\* Mailgun free tier has limits; Single Sender = verify one email and send from it.

**Recommendation: Use SendGrid** — 100 emails/day free, no domain needed (verify your Gmail), works on Render free tier.

---

## 🚀 Quick Setup: SendGrid on Render Free Tier

### Step 1: Create SendGrid Account

1. Go to **https://sendgrid.com**
2. Sign up (free)
3. Verify your email

### Step 2: Verify Single Sender (No Domain Needed)

1. In SendGrid: **Settings** → **Sender Authentication**
2. Click **Verify a Single Sender**
3. Fill in:
   - **From Name:** Spectra HoliParty
   - **From Email:** spectraholi2026@gmail.com
   - **Reply To:** spectraholi2026@gmail.com
   - Address, etc.
4. Click **Create**
5. Check your Gmail and click the verification link
6. Status should show **Verified** ✅

### Step 3: Create API Key

1. In SendGrid: **Settings** → **API Keys**
2. Click **Create API Key**
3. Name: `Spectra HoliParty`
4. Permissions: **Restricted** → enable **Mail Send** → **Full Access** (or just Mail Send)
5. Click **Create & View**
6. **Copy the API key** (you won’t see it again!)

### Step 4: Set Environment Variables on Render

1. Go to **Render Dashboard** → your web service → **Environment**
2. Add/update:

```
EMAIL_PROVIDER = sendgrid
SENDGRID_API_KEY = SG.xxxxxxxxxxxxxxxxxxxx
EMAIL_FROM = spectraholi2026@gmail.com
```

(Use your real API key and the same email you verified.)

### Step 5: Deploy

- Save env vars; Render will redeploy.
- Or trigger **Manual Deploy**.

### Step 6: Test

1. Make a test booking
2. Mark payment as **Paid** in admin
3. Check the customer’s inbox for the ticket email

---

## 📊 Summary: What Works on Render Free Tier

| Provider | Works? | Send to customers? | Notes |
|----------|--------|--------------------|--------|
| **SendGrid** | ✅ Yes | ✅ Yes | **Best:** 100/day free, Single Sender = no domain |
| **Resend** | ✅ Yes | ❌ No* | *Only with verified domain; test mode = your email only |
| **Mailgun** | ✅ Yes | ✅ Yes | Free tier; may need domain |
| **Gmail SMTP** | ❌ No | — | SMTP ports blocked on free tier |

---

## 🔗 References

- [Render: Free tier SMTP ports blocked](https://render.com/changelog/free-web-services-will-no-longer-allow-outbound-traffic-to-smtp-ports)
- [SendGrid](https://sendgrid.com) – free tier, HTTPS API
- [SendGrid Single Sender](https://docs.sendgrid.com/ui/sending-email/sender-verification) – verify one email, no domain

---

**TL;DR:** On Render free tier, use **SendGrid** with **Single Sender Verification** (e.g. spectraholi2026@gmail.com). No domain needed, 100 emails/day free, works with your current app.
