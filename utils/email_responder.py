import os
from langchain_community.chat_models import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0.7)

prompt = PromptTemplate(
    input_variables=["email", "category"],
    template="""
You are an HR assistant. Given the email below and its classified category, write a professional and friendly response.

Category: {category}

Email:
{email}

Respond as if you are replying on behalf of the HR team. Keep it concise and polite.
"""
)

responder_chain = LLMChain(llm=llm, prompt=prompt)

def generate_response(email_body: str, category: str) -> str:
    result = responder_chain.run(email=email_body, category=category)
    return result.strip()
