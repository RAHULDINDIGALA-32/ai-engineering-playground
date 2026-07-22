import os
from pathlib import Path
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

my_api_key = os.getenv("GROQ_API_KEY")
if not my_api_key:
    raise ValueError("GROQ_API_KEY environment variable is not set. Please set it in your .env file.")

client = Groq(api_key=my_api_key)

model = "llama-3.3-70b-versatile"

system_message = {
    "role": "system",
    "content": "you are a creative brand marketer and copywriter. You are a helpful assistant that can answer questions and provide information about the brand, products, and services. You are also able to generate creative content such as titles, slogans, taglines, and marketing copy."
}

user_message_1 = {
    "role": "user",
    "content": "Suggest a single creative and catchy slogans for a new eco-friendly water bottle brand called 'AquaPure'."
}

messages = [system_message, user_message_1]

response = client.chat.completions.create(
    model = model,
    messages = messages,
    temperature = 1.5,
)


print("\n###########################################################\n")
print("User Prompt: ", user_message_1["content"])
print("\nExtracted Response from the Model:\n")
print(response.choices[0].message.content)
print("\n###########################################################\n")