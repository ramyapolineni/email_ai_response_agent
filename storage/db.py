import os
from pymongo import MongoClient
from dotenv import load_dotenv
import uuid

load_dotenv()

# Load the Mongo URI from .env
MONGO_URI = os.getenv("MONGO_URI")
#client = MongoClient(MONGO_URI)
client = MongoClient(MONGO_URI, tls=True, tlsAllowInvalidCertificates=True)

# Reference the database and collection
db = client["ai_email_agent"]  # Database name
emails_collection = db["emails"]  # Collection (like a table)

def save_email(sender_name, sender_email, subject, body, category, response,
               message_id=None, in_reply_to=None, references=None):
    from datetime import datetime

    # Try to find existing thread by same sender + subject
    existing = emails_collection.find_one({
        "sender_email": sender_email,
        "subject": subject
    })

    # If found, reuse thread_id; otherwise, create a new one
    thread_id = existing["thread_id"] if existing and "thread_id" in existing else str(uuid.uuid4())

    email_doc = {
        "thread_id": thread_id,
        "sender_name": sender_name,
        "sender_email": sender_email,
        "subject": subject,
        "body": body,
        "category": category,
        "response": response,
        "timestamp": datetime.utcnow(),
        "message_id": message_id,
        "in_reply_to": in_reply_to,
        "references": references
    }

    result = emails_collection.insert_one(email_doc)
    print(f"✅ Email saved to MongoDB with ID: {result.inserted_id} and thread_id: {thread_id}")
