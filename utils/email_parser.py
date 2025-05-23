from email import message_from_string
from email.utils import parseaddr
from email.header import decode_header
import re

def parse_email(raw_email):
    msg = message_from_string(raw_email)

    from_name, from_email = parseaddr(msg.get("From", ""))
    subject_raw, encoding = decode_header(msg.get("Subject", ""))[0]
    subject = subject_raw.decode(encoding or "utf-8") if isinstance(subject_raw, bytes) else subject_raw

    # Extract plain text body
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/plain":
                charset = part.get_content_charset() or "utf-8"
                try:
                    body = part.get_payload(decode=True).decode(charset)
                except:
                    body = part.get_payload(decode=True).decode("utf-8", errors="replace")
                break
    else:
        charset = msg.get_content_charset() or "utf-8"
        try:
            body = msg.get_payload(decode=True).decode(charset)
        except:
            body = msg.get_payload().decode("utf-8", errors="replace")

    return {
        "from_name": from_name,
        "from_email": from_email,
        "subject": subject,
        "body": body.strip(),
        "message_id": msg.get("Message-ID"),
        "references": msg.get("References"),
        "in_reply_to": msg.get("In-Reply-To"),
        "to": msg.get_all("To", []),
        "cc": msg.get_all("Cc", [])
    }

def strip_quoted_text(body):
    """
    Removes quoted reply chains like:
    "On [date], [person] wrote:"
    or
    "From: [email] ..."
    """
    # Common email reply separators
    patterns = [
        r"\nOn .*wrote:\n",                      # Gmail
        r"\nFrom: .*",                           # Outlook
        r"-----Original Message-----",           # Outlook classic
        r"\n>.*",                                # Quoted lines
    ]

    for pattern in patterns:
        match = re.search(pattern, body, flags=re.IGNORECASE | re.DOTALL)
        if match:
            body = body[:match.start()].strip()
            break
    return body

def strip_signature(body):
    """
    Removes common email signature lines starting with 'Thanks', 'Regards', etc.
    """
    signature_markers = ["thanks", "regards", "best", "sincerely", "--", "__"]
    lines = body.strip().splitlines()
    clean_lines = []

    for line in lines:
        lower_line = line.strip().lower()
        if any(lower_line.startswith(marker) for marker in signature_markers):
            break
        clean_lines.append(line)

    return "\n".join(clean_lines).strip()
