import os
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_community.chat_models import ChatOpenAI

# Load environment variables
load_dotenv()

llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)

prompt = PromptTemplate(
    input_variables=["email"],
    template="""You are a helpful HR assistant that classifies emails. Use one of the following categories:

1. Leave Application
2. Job Inquiry
3. Onboarding Question
4. Complaint or Dispute
5. Training Request
6. General HR Query
7. Other

ONLY choose "Other" if the email clearly fits HR but does not belong to the first six categories.

If you are not absolutely sure about the correct category or if the email is unclear or vague, respond with "Escalate".

Email:
{email}

Respond with only one of the following exact words:
- Leave Application
- Job Inquiry
- Onboarding Question
- Complaint or Dispute
- Training Request
- General HR Query
- Other
- Escalate
"""
)

classification_chain = LLMChain(llm=llm, prompt=prompt)

def classify_email(email_body: str) -> str:
    result = classification_chain.run(email=email_body).strip()

    # Additional fallback based on vague/short content
    vague_phrases = ["please confirm", "can you help", "is it approved", "thanks", "okay", "thank you"]
    if len(email_body.strip()) < 20 or any(p.lower() in email_body.lower() for p in vague_phrases):
        if result not in ["Escalate", "Other"]:
            print("⚠️ Switching vague result to 'Other'")
            return "Other"

    return result
