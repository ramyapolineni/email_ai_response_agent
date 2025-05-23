import imaplib
import os
from dotenv import load_dotenv

load_dotenv()

EMAIL_USER = os.getenv("GMAIL_USER")
EMAIL_PASS = os.getenv("GMAIL_APP_PASSWORD")

def fetch_unread_emails():
    imap = imaplib.IMAP4_SSL("imap.gmail.com")
    imap.login(EMAIL_USER, EMAIL_PASS)
    imap.select("inbox")

    # Search for unread emails
    status, messages = imap.search(None, 'UNSEEN')
    email_ids = messages[0].split()

    fetched_emails = []

    for mail_id in email_ids:
        status, msg_data = imap.fetch(mail_id, "(RFC822)")
        if status != "OK":
            continue
        raw_email_bytes = msg_data[0][1]
        raw_email_str = raw_email_bytes.decode("utf-8", errors="replace")
        fetched_emails.append(raw_email_str)

    imap.logout()
    return fetched_emails
