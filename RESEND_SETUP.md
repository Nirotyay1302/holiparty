# Resend Email Setup Guide

## Option 1: Using onboarding@resend.dev (Quick Start - Testing Only)

**Yes, you can use `onboarding@resend.dev` for testing!**

### Setup Steps:
1. Go to Render Dashboard → Your Web Service → Environment
2. Add environment variable:
   - `RESEND_FROM_EMAIL` = `onboarding@resend.dev`
3. That's it! You can start sending emails immediately.

**Limitations:**
- ✅ Works for testing and development
- ❌ Not recommended for production
- ❌ May have lower deliverability
- ❌ Can't customize sender name much

---

## Option 2: Using Your Own Domain (Production - Recommended)

**Important:** Resend does NOT support sending from Gmail addresses (`@gmail.com`). 
You need a **custom domain** (e.g., `spectraholi2026.com`).

### Step-by-Step Guide:

### Step 1: Get a Domain
If you don't have one, purchase from:
- Namecheap (cheap, ~$10/year)
- Google Domains
- GoDaddy
- Any domain registrar

**Example:** Purchase `spectraholi2026.com` or `spectraholiparty.com`

### Step 2: Sign Up for Resend
1. Go to [resend.com](https://resend.com)
2. Sign up/login with your account
3. Navigate to **Domains** section

### Step 3: Add Your Domain to Resend
1. In Resend dashboard, click **"Add Domain"**
2. Enter your domain: `spectraholi2026.com` (or your domain)
3. Resend will show you DNS records to add

### Step 4: Configure DNS Records
You need to add these DNS records to your domain:

#### A. SPF Record (TXT)
- **Type:** TXT
- **Name:** `@` (or your subdomain like `send`)
- **Value:** `v=spf1 include:resend.com ~all`
- **TTL:** 3600 (or default)

#### B. DKIM Record (TXT)
- **Type:** TXT
- **Name:** `resend._domainkey` (or what Resend provides)
- **Value:** (Resend will provide this - looks like a long string)
- **TTL:** 3600 (or default)

#### C. DMARC Record (Optional but Recommended)
- **Type:** TXT
- **Name:** `_dmarc`
- **Value:** `v=DMARC1; p=none; rua=mailto:spectraholi2026@gmail.com`
- **TTL:** 3600

### Step 5: Verify Domain in Resend
1. After adding DNS records, wait 5-10 minutes
2. Go back to Resend dashboard → Domains
3. Click **"Verify"** button
4. Resend will check DNS records
5. Once verified ✅, you can send from any email on that domain

### Step 6: Create Email Address
Once domain is verified, you can use:
- `tickets@spectraholi2026.com`
- `noreply@spectraholi2026.com`
- `info@spectraholi2026.com`
- Or any email address on your domain!

### Step 7: Update Render Environment Variables
1. Go to Render Dashboard → Your Web Service → Environment
2. Update:
   - `RESEND_FROM_EMAIL` = `tickets@spectraholi2026.com` (or your chosen email)

### Step 8: Test Email
1. Make a test booking
2. Mark payment as "Paid" in admin
3. Check if email arrives from your custom domain

---

## Quick Comparison

| Feature | onboarding@resend.dev | Custom Domain |
|---------|----------------------|---------------|
| Setup Time | Instant | 15-30 minutes |
| Cost | Free | Domain cost (~$10/year) |
| Deliverability | Good | Excellent |
| Professional | No | Yes |
| Production Ready | No | Yes |
| Custom Email | No | Yes (any@yourdomain.com) |

---

## Recommended Approach

**For Now (Testing):**
- Use `onboarding@resend.dev` ✅
- Set in Render: `RESEND_FROM_EMAIL = onboarding@resend.dev`

**For Production:**
- Get a domain (e.g., `spectraholi2026.com`)
- Verify it with Resend
- Use `tickets@spectraholi2026.com` or `info@spectraholi2026.com`
- Update Render: `RESEND_FROM_EMAIL = tickets@spectraholi2026.com`

---

## Troubleshooting

### Domain Verification Failing?
- Wait 10-15 minutes after adding DNS records
- Check DNS propagation: [whatsmydns.net](https://www.whatsmydns.net)
- Ensure TXT records are exactly as Resend provided
- Remove any extra spaces in DNS records

### Emails Not Sending?
- Check Render logs for errors
- Verify `RESEND_API_KEY` is set correctly
- Ensure `RESEND_FROM_EMAIL` matches verified domain
- Check Resend dashboard → Logs for delivery status

---

## Need Help?

- Resend Docs: https://resend.com/docs
- Domain Setup: https://resend.com/docs/dashboard/domains/introduction
- Support: support@resend.com
