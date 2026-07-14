import os
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq

load_dotenv()
my_api_key = os.getenv("GROQ_API_KEY")

if not my_api_key:
    raise ValueError("GROQ_API_KEY environment variable is not set. Please set it in your .env file.")

client = Groq(api_key = my_api_key)

model = "llama-3.3-70b-versatile"
role = "user"
prompt = "Write a short poem describing the beauty of nature & the power of Artificial Intelligence."
message = {
    "role": role,
    "content": prompt
}

messages = [message]

response = client.chat.completions.create(
    model = model,
    messages = messages
)


print("###########################################################")
print("Raw response from the Model:\n")
print(response)

print("\n###########################################################")
print("User Prompt: ", prompt)
print("\nExtracted Response from the Model:\n")
print(response.choices[0].message.content)

print("\n###########################################################")
print("Total Tokens Used: ", response.usage.total_tokens)