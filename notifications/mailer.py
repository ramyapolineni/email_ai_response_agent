import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

# Load environment variables from .env
env_loaded = load_dotenv()
print("📦 .env loaded:", env_loaded)

EMAIL_USER = os.getenv("GMAIL_USER")
EMAIL_PASS = os.getenv("GMAIL_APP_PASSWORD")

# Debug print first 4 characters of credentials
print("🔐 Loaded EMAIL_USER:", EMAIL_USER or "❌ MISSING")
print("🔐 Loaded EMAIL_PASS (first 4 chars):", EMAIL_PASS[:4] if EMAIL_PASS else "❌ MISSING")

def sanitize_header(header_value):
    """Remove any newline or carriage return characters from header values."""
    if isinstance(header_value, str):
        return header_value.replace("\n", "").replace("\r", "").strip()
    return header_value

def send_email(to_email, subject, body, in_reply_to=None, references=None):
    print("\n📨 Preparing to send email...")
    print("To:", to_email)
    print("Subject:", subject)
    print("In-Reply-To:", in_reply_to or "None")
    print("References:", references or "None")
    print("Body:\n", body)

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = EMAIL_USER
    msg["To"] = to_email

    # Clean/sanitize threading headers
    if in_reply_to:
        msg["In-Reply-To"] = sanitize_header(in_reply_to)
    if references:
        msg["References"] = sanitize_header(references)

    msg.set_content(body)

    try:
        print("📡 Connecting to Gmail SMTP...")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_USER, EMAIL_PASS)
            print(f"✅ Logged in. Sending to {to_email}")
            smtp.send_message(msg)
            print("✅ Email sent successfully!")
            return True

    except smtplib.SMTPAuthenticationError as auth_err:
        print("❌ SMTP Auth Error:", auth_err.smtp_code, auth_err.smtp_error.decode())
    except Exception as e:
        print("❌ Email sending failed:", e)

    return False
