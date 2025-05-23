from utils.email_parser import parse_email, strip_signature, strip_quoted_text
from utils.email_classifier import classify_email
from utils.email_responder import generate_response
from admin.escalation_handler import handle_escalation
from storage.db import save_email
from inbox.email_fetcher import fetch_unread_emails
from notifications.mailer import send_email
from utils.scenario_templates import load_scenarios, get_response_template
from utils.date_extractor import extract_leave_date
from email.utils import getaddresses
from pymongo import MongoClient
import os

# Load scenario templates
scenarios = load_scenarios("Downloads/ai_email_agent/config/responses.json")

# MongoDB setup
client = MongoClient(os.getenv("MONGO_URI"))
db = client["ai_email_agent"]
emails_collection = db["emails"]

# Fetch unread emails
emails = fetch_unread_emails()

for raw_email in emails:
    parsed = parse_email(raw_email)
    if not parsed:
        print("⚠️ Skipping email due to parse failure.")
        continue

    # Log full parsed email
    print("\n📥 Incoming Email")
    print(f"From   : {parsed.get('from_name')} <{parsed.get('from_email')}>")
    print(f"Subject: {parsed.get('subject')}")
    print("Body:")
    print(parsed.get("body"))
    print("=" * 60)

    # Get cleaned body (no quoted text, no signature)
    raw_body = parsed["body"]
    print("\n📜 Raw Body:\n" + raw_body)
    cleaned_body = strip_signature(strip_quoted_text(raw_body))
    if not cleaned_body.strip():
        print("⚠️ Cleaned body is empty after stripping. Falling back to raw body.")
        cleaned_body = raw_body
    print("\n🧹 Cleaned Body for classification:\n" + cleaned_body)

    # Use cleaned body for classification
    classification_input = f"Subject: {parsed.get('subject')}\n{cleaned_body}"
    print("🔍 Classification input:\n" + classification_input)
    category = classify_email(classification_input)
    print(f"🤖 Predicted Category: {category}")

    # Retrieve prior message for thread (for follow-up logic)
    thread_id = parsed.get("in_reply_to") or parsed.get("references") or parsed.get("message_id")
    prior = emails_collection.find_one({
        "$or": [
            {"message_id": thread_id},
            {"references": thread_id},
            {"in_reply_to": thread_id}
        ]
    })

    # 🔁 Follow-up logic: combine header + keyword based intent
    followup_keywords = [
        "any update", "just checking", "still waiting", "is it approved", "can you confirm",
        "follow up", "wanted to ask", "did you see", "pending", "not heard back", "status"
    ]
    same_sender = prior and prior.get("from_email") == parsed.get("from_email")
    same_subject = prior and prior.get("subject", "").strip().lower() == parsed.get("subject", "").strip().lower()
    has_thread_headers = parsed.get("in_reply_to") or parsed.get("references")
    has_followup_intent = any(kw in cleaned_body.lower() for kw in followup_keywords)
    is_followup = (same_sender and same_subject and has_thread_headers) or has_followup_intent
    print(f"\n🔁 is_followup: {is_followup}")

    # Manual override if escalated earlier
    if category == "Escalate" and prior and "manual_category" in prior:
        print(f"🔁 Overriding 'Escalate' with prior manual_category: {prior['manual_category']}")
        category = prior["manual_category"]

    # Handle escalation
    if category == "Escalate":
        response = handle_escalation(parsed)
        email_sent = False
    else:
        # Fetch template based on category and follow-up flag
        template_obj = get_response_template(category, cleaned_body, scenarios, is_followup=is_followup)

        name = parsed["from_name"] or "there"
        if isinstance(template_obj, dict):
            response = template_obj.get("followupTemplate" if is_followup else "responseTemplate", "")
        else:
            response = template_obj or ""

        response = response.replace("{{name}}", name)
        if "{{leave_date}}" in response:
            leave_date = extract_leave_date(cleaned_body) or "your requested date"
            response = response.replace("{{leave_date}}", leave_date)

        if not response.strip():
            response = generate_response(cleaned_body, category)

        print("\n📝 Final Response:\n" + response)

        # Build recipient list
        to_addrs = [addr for _, addr in getaddresses(parsed.get("to", []))]
        cc_addrs = [addr for _, addr in getaddresses(parsed.get("cc", []))]
        all_recipients = list(set(to_addrs + cc_addrs + [parsed["from_email"]]))

        my_email = os.getenv("GMAIL_USER")
        if my_email:
            all_recipients = [addr for addr in all_recipients if addr.lower() != my_email.lower()]
        if not all_recipients:
            all_recipients = [parsed["from_email"]]

        # Threading setup
        subject = parsed["subject"]
        if not subject.lower().startswith("re:"):
            subject = "Re: " + subject

        in_reply_to = parsed.get("message_id")
        prior_refs = parsed.get("references") or parsed.get("in_reply_to")
        references = f"{prior_refs} {in_reply_to}".strip() if prior_refs else in_reply_to

        print("📌 In-Reply-To:", in_reply_to)
        print("📌 References :", references)

        email_sent = send_email(
            to_email=all_recipients,
            subject=subject,
            body=response,
            in_reply_to=in_reply_to,
            references=references
        )

    # Save email to DB
    save_email(
        sender_name=parsed["from_name"],
        sender_email=parsed["from_email"],
        subject=parsed["subject"],
        body=parsed["body"],
        category=category,
        response=response,
        message_id=parsed.get("message_id"),
        in_reply_to=parsed.get("in_reply_to"),
        references=parsed.get("references")
    )
