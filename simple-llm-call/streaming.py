import os
from dotenv import load_dotenv
from groq import Groq
import logging

load_dotenv()
my_api_key = os.getenv("GROQ_API_KEY")

if not my_api_key:
    raise ValueError("GROQ_API_KEY environment variable not set. Please set it in your .env file.")

client = Groq(api_key=my_api_key)
MODEL = "llama-3.3-70b-versatile"

role = "user"
prompt = "Explain the Web3 & Blockchain in detail."

message = {
    "role": role,
    "content": prompt
}

messages = [message]

## Without Streaming
complete_response = client.chat.completions.create(
    model=MODEL,
    messages=messages
)

complete_answer = complete_response.choices[0].message.content
print("\n########## WITHOUT STREAMING ############")
print(complete_answer)
print("\n#########################################")


## With Streaming
response_stream = client.chat.completions.create(
    model=MODEL,
    messages=messages,
    stream=True 
)

print("\n########## WITH STREAMING ############\n")



for chunk in response_stream:
    chunk_content = chunk.choices[0].delta.content
    if chunk_content:
        print(chunk_content, end="", flush=True)


print("\n#########################################\n")