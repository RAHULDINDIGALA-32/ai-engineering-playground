import os
from dotenv import load_dotenv
from groq import Groq
import logging

load_dotenv()
my_api_key = os.getenv("GROQ_API_KEY")

if not my_api_key:
    raise ValueError("GROQ_API_KEY environment variable is not set. Please set it in your .env file.")

client = Groq(api_key=my_api_key)
MODEL = "llama-3.3-70b-versatile"

## RAG 

# 1. Knowledge Base
knowledge_base_dict = {
    "name": "RAHUL DINDIGALA",
    "age": "The age of Rahul is 22 years.",
    "qualification": "Rahul has completed his btech. in CSE major in Artificial Intelligence from IIITDM Kancheepuram in the year 2026.",
    "role": "Web3 Engineer"
}

# 2. Retrieval System
def retrieve_info(question):
    question = question.lower()
    if "age"in question:
        return knowledge_base_dict["age"]
    elif "qualification" in question:
        return knowledge_base_dict["qualification"]
    else:
        return None

    
# 3. Augmented Generation
def ask_llm(question):
    context = retrieve_info(question)

    system_prompt = f"""Answer ONLY in single sentence. Answer ONLY basedon the context provided, do NOT hallucinate. Context: {context}"""
    system_message = {
        "role": "system",
        "content": system_prompt
    }

    user_message = {
        "role": "user",
        "content": question
    }

    messages = [system_message, user_message]

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages
        )
        answer = response.choices[0].message.content
        return answer
    except Exception as e:
        logging.exception("Failed to call LLM. Error: ", e)
        return None

    
question = "What is Rahul's qualification ?"
answer = ask_llm(question)

print("#############################")
print(answer)
print("#############################")
    