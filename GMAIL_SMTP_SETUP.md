# 🚀 Quick Setup: Gmail SMTP (Send to Any User!)

## ✅ This is the EASIEST way to send emails to your users!

**No domain verification needed!** Works immediately with your Gmail account.

---

## Step-by-Step Setup (5 minutes)

### Step 1: Enable 2-Factor Authentication

1. Go to: https://myaccount.google.com/security
2. Sign in with `spectraholi2026@gmail.com`
3. Scroll to **"2-Step Verification"**
4. Click **"Get Started"** and follow the prompts
5. Complete the setup

### Step 2: Generate App Password

1. Go to: https://myaccount.google.com/apppasswords
2. You may need to sign in again
3. Under **"Select app"**, choose **"Mail"**
4. Under **"Select device"**, choose **"Other (Custom name)"**
5. Type: `Spectra HoliParty`
6. Click **"Generate"**
7. **Copy the 16-character password** (it looks like: `abcd efgh ijkl mnop`)
   - Remove spaces: `abcdefghijklmnop`

### Step 3: Set Environment Variables in Render

1. Go to **Render Dashboard**: https://dashboard.render.com
2. Open your web service
3. Go to **Environment** tab
4. Add/Update these variables:

```
EMAIL_PROVIDER = smtp
EMAIL_USER = spectraholi2026@gmail.com
EMAIL_PASS = abcdefghijklmnop
```

(Replace `abcdefghijklmnop` with your actual 16-character app password)

### Step 4: Deploy

- Render will automatically redeploy
- OR click **"Manual Deploy"** → **"Deploy latest commit"**

### Step 5: Test!

1. Make a test booking
2. Mark payment as "Paid" in admin
3. Check customer email - they should receive the ticket! 🎉

---

## ✅ That's It!

You can now send emails to **ANY customer email address**!

**Limits:**
- Gmail free: **500 emails/day**
- Perfect for events! 🎉

---

## 🔧 Troubleshooting

### "Invalid credentials" error?
- Make sure you're using **App Password**, not your regular Gmail password
- App Password is 16 characters (no spaces)
- Regenerate if needed: https://myaccount.google.com/apppasswords

### Emails not sending?
- Check Render logs for error messages
- Verify `EMAIL_PROVIDER = smtp` is set
- Verify `EMAIL_USER` and `EMAIL_PASS` are correct
- Make sure 2FA is enabled on your Gmail account

### Still having issues?
- Check that `EMAIL_PROVIDER` is set to `smtp` (lowercase)
- Verify the app password doesn't have spaces
- Try regenerating the app password

---

## 📊 Comparison

| Feature | Gmail SMTP | Resend (test mode) |
|---------|------------|-------------------|
| Setup Time | 5 minutes | Instant |
| Can send to customers? | ✅ Yes | ❌ No (only your email) |
| Domain needed? | ❌ No | ✅ Yes (for customers) |
| Daily limit | 500 emails | 3,000/month |
| Cost | Free | Free |

**Winner: Gmail SMTP for quick setup!** 🏆

---

## 🎯 Next Steps

Once you've set up Gmail SMTP:
1. Test with a real booking
2. Verify emails are being received
3. You're done! 🎉

If you need more than 500 emails/day later, you can:
- Upgrade to Gmail Workspace ($6/month)
- Or switch to SendGrid (100/day free, then paid)
- Or verify a domain with Resend

But for now, Gmail SMTP is perfect! ✅
