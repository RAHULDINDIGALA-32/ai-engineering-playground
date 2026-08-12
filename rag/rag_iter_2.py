import os
import sys
from dotenv import load_dotenv
from groq import Groq
import numpy as np
from sentence_transformers import SentenceTransformer
import logging

load_dotenv()
my_api_key = os.getenv("GROQ_API_KEY")

if not my_api_key:
    raise ValueError("GROQ_API_KEY environment variable is not set. Please set it in your .env file.")

client = Groq(api_key=my_api_key)
LLM_MODEL = "llama-3.3-70b-versatile"

TRANSFORMER_MODEL = SentenceTransformer("all-MiniLM-L6-v2") #374 features


## RAG 

# 1. Knowledge Base
documents = [
    "Employees receive 24 days of paid leave per year. Unused paid leave can be carried forward for up to 10 days into the following year.",

    "Employees work from the office on Tuesday, Wednesday and Thursday. Monday and Friday are optional work-from-home days. Employees must inform their manager before working remotely.",

    "Employees receive Rs 3000 per month for gym reimbursement. The reimbursement requires a valid monthly receipt and must be submitted through the employee benefits portal.",

    "Employees can claim Rs 2000 per month for home internet expenses. The internet reimbursement is available only to employees who work remotely at least four days per month.",

    "Employees have a 90 day notice period. Employees who are still in their probation period have a 30 day notice period.",

    "The company provides Rs 1500 per month for mobile phone expenses. Employees must submit a copy of their mobile bill to receive the reimbursement.",

    "Employees receive health insurance coverage for themselves and their spouse. Children can also be included under the family health insurance plan.",

    "The standard working hours are 9:30 AM to 6:30 PM from Monday to Friday. Employees are expected to complete eight working hours per day excluding lunch breaks.",

    "Employees receive a meal allowance of Rs 250 for each day they work from the office. The meal allowance does not apply to work-from-home days.",

    "Employees are eligible for a performance bonus once per year. The bonus amount depends on individual performance and overall company performance.",

    "New employees have a six month probation period. During probation, employees are evaluated on performance, attendance and adherence to company policies.",

    "Employees can request up to 10 days of sick leave per year. A medical certificate may be required when sick leave exceeds three consecutive working days.",

    "Employees must notify their manager at least two weeks before taking more than five consecutive days of planned leave.",

    "The company provides Rs 5000 per year for professional development. Employees can use this allowance for approved courses, certifications, conferences and technical books.",

    "Employees are expected to maintain confidentiality of company information, customer information and internal business documents even after leaving the company.",

    "Employees must use company-issued laptops for accessing confidential company systems. Personal computers should not be used to access production databases.",

    "The company provides a one-time relocation allowance of up to Rs 25000 for employees who are required to move to another city for business purposes.",

    "Employees working overtime must obtain approval from their manager before performing the additional work. Overtime without prior approval may not qualify for compensation.",

    "Salary is paid on the last working day of each month. If the last working day falls on a public holiday, salary will normally be processed on the preceding working day.",

    "Employees are eligible for a Rs 10000 annual learning bonus after completing at least one approved professional certification during the financial year."
]

document_embeddings = TRANSFORMER_MODEL.encode(documents)
print("Knowledge Base embedding size (in Bytes): ", sys.getsizeof(document_embeddings))


# 2. Retrieval System (Single-document retrieval)
def cosine_similarity(vector1, vector2):
    return np.dot(vector1, vector2) / (np.linalg.norm(vector1) * np.linalg.norm(vector2))


def retrieve_info(query):
    query_embedding = TRANSFORMER_MODEL.encode(query)
    scores = []

    for i, document in enumerate(document_embeddings):
        score = cosine_similarity(query_embedding, document)
        scores.append((score, documents[i]))

    scores.sort(reverse=True)

    return scores[0]
    

# 3. Augmented Generation
def ask_llm(query):
    _, context = retrieve_info(query)

    system_prompt = f"""Answer ONLY in single sentence. Answer ONLY based on the context provided, do NOT hallucinate. Context: {context}"""
    system_message = {
        "role": "system",
        "content": system_prompt
    }

    user_message = {
        "role": "user",
        "content": query
    }

    messages = [system_message, user_message]

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages
        )
        answer = response.choices[0].message.content
        return answer
    except Exception as e:
        logging.exception("Failed to call LLM. Error: ", e)
        return None

    
question = "What is the notice period?"
answer = ask_llm(question)

print("#############################")
print(answer)
print("#############################")
    