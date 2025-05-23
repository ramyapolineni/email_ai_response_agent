import streamlit as st
from pymongo import MongoClient
from dotenv import load_dotenv
import os
from bson import ObjectId
from notifications.mailer import send_email
import uuid  # for fallback threading IDs

# Load environment variables
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client["ai_email_agent"]
emails_collection = db["emails"]

st.set_page_config(page_title="HR Email Agent Dashboard", layout="wide")
st.title("📬 HR Email Agent - Conversation View")

# Dropdown to filter threads by category
category_filter = st.selectbox(
    "Filter by Category",
    options=["All", "Leave Application", "Job Inquiry", "Onboarding Question", "Other", "Escalate"]
)

# Group messages by thread_id
match_stage = {} if category_filter == "All" else {"category": category_filter}
threads = emails_collection.aggregate([
    {"$match": match_stage},
    {"$sort": {"timestamp": 1}},
    {"$group": {
        "_id": "$thread_id",
        "messages": {"$push": "$$ROOT"},
        "last_updated": {"$max": "$timestamp"},
        "sender_email": {"$first": "$sender_email"},
        "subject": {"$first": "$subject"}
    }},
    {"$sort": {"last_updated": -1}}
])

# Display each thread
for thread in threads:
    messages = thread["messages"]
    st.subheader(f"📎 Thread: {thread['subject']} ({thread['sender_email']})")

    for msg in messages:
        st.markdown("----")
        st.markdown(f"**🕒 Timestamp:** {msg.get('timestamp', '')}")
        st.markdown(f"**✉️ From:** {msg['sender_name']} ({msg['sender_email']})")
        st.markdown("**📨 Message:**")
        st.code(msg["body"])

        if msg.get("response"):
            st.markdown("**🤖 Response:**")
            st.success(msg["response"])

        # Escalation response form
        # Escalation response form with manual classification
        if msg["category"] == "Escalate" and msg.get("response", "").startswith("_Pending"):
            with st.form(key=f"form_{str(msg['_id'])}"):
                st.markdown("**📝 Classify this email for future automation:**")
                manual_category = st.selectbox("Select category", [
                    "Leave Application", "Job Inquiry", "Onboarding Question", 
                    "Complaint or Dispute", "Training Request", 
                    "General HR Query", "Other"
                ])
                response_text = st.text_area("Type your response", height=150)
                submit = st.form_submit_button("Send Response")

                if submit and response_text.strip():
                    in_reply_to = msg.get("in_reply_to")
                    references = msg.get("references")

                    # Fallback threading logic
                    if not in_reply_to:
                        previous_msgs = [m for m in messages if m["_id"] != msg["_id"]]
                        if previous_msgs:
                            latest = previous_msgs[-1]
                            in_reply_to = latest.get("message_id") or f"<{uuid.uuid4()}@fallback>"
                            references = latest.get("references") or in_reply_to
                        else:
                            in_reply_to = f"<{uuid.uuid4()}@fallback>"
                            references = in_reply_to

                    # Display threading headers
                    st.markdown(f"📬 **Threading headers:**")
                    st.markdown(f"**In-Reply-To:** `{in_reply_to}`")
                    st.markdown(f"**References:** `{references}`")

                    # Update database with response and manual classification
                    emails_collection.update_one(
                        {"_id": ObjectId(msg["_id"])},
                        {"$set": {
                            "response": response_text.strip(),
                            "in_reply_to": in_reply_to,
                            "references": references,
                            "manual_category": manual_category
                        }}
                    )

                    # Send email
                    email_sent = send_email(
                        to_email=msg["sender_email"],
                        subject=f"Re: {msg['subject']}",
                        body=response_text.strip(),
                        in_reply_to=in_reply_to,
                        references=references
                    )

                    if email_sent:
                        st.success("✅ Response saved and email sent!")
                    else:
                        st.error("⚠️ Response saved but email failed to send.")
