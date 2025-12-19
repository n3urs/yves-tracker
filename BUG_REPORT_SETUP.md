# Bug Report Email Setup

I've added a bug report feature to your app! Users can now report bugs directly from the sidebar, and you'll receive an email at oscar@sullivanltd.co.uk.

## Setup Instructions

To enable email sending, you need to configure email credentials in `.streamlit/secrets.toml`:

### Option 1: Using Gmail (Recommended)

1. **Create a Gmail App Password** (if using 2FA):
   - Go to your Google Account: https://myaccount.google.com/
   - Navigate to: Security > 2-Step Verification > App passwords
   - Generate a new app password for "Mail"
   - Copy the 16-character password

2. **Update `.streamlit/secrets.toml`**:
   ```toml
   EMAIL_SENDER = "your-email@gmail.com"
   EMAIL_PASSWORD = "your-16-char-app-password"
   EMAIL_SMTP_SERVER = "smtp.gmail.com"
   EMAIL_SMTP_PORT = 587
   ```

### Option 2: Using Other Email Providers

For other providers (Outlook, custom domain, etc.), use their SMTP settings:

**Outlook/Hotmail:**
```toml
EMAIL_SENDER = "your-email@outlook.com"
EMAIL_PASSWORD = "your-password"
EMAIL_SMTP_SERVER = "smtp-mail.outlook.com"
EMAIL_SMTP_PORT = 587
```

**Custom SMTP:**
```toml
EMAIL_SENDER = "your-email@yourdomain.com"
EMAIL_PASSWORD = "your-password"
EMAIL_SMTP_SERVER = "smtp.yourdomain.com"
EMAIL_SMTP_PORT = 587
```

## How It Works

1. Users click "🐛 Report Bug" in the sidebar (visible on all pages)
2. They type a description of the issue
3. Click "Send Bug Report"
4. You receive an email with:
   - The username
   - Timestamp
   - The bug description

## Testing

To test it:
1. Add your email credentials to secrets.toml
2. Restart Streamlit
3. Open the sidebar
4. Expand "🐛 Report Bug"
5. Type a test message
6. Click "Send Bug Report"
7. Check oscar@sullivanltd.co.uk for the email

## Security Notes

- **Never commit secrets.toml to git** (it's already in .gitignore)
- Use app-specific passwords, not your main email password
- The bug report form is available to all users (logged in or not)
- User context is included in the email automatically
