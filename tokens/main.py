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
MAX_TOKENS = 1000

prompt1 = "Hello!!" 
prompt2 = "What is the capital of India?"
prompt3 = "Write a short poem describing the beauty of nature & the power of Artificial Intelligence."

prompts = [prompt1, prompt2, prompt3]

for prompt in prompts:
    message = {
        "role": role,
        "content": prompt
    } 
    messages = [message]
    response = client.chat.completions.create(
    model = model,
    messages = messages,
    max_tokens = MAX_TOKENS,
    )
    usage = response.usage

    print("\n###########################################################\n")
    print("User Prompt: ", prompt)
    print("\nExtracted Response from the Model:\n")
    print(response.choices[0].message.content)
    print("\nPrompt_tokens: ", usage.prompt_tokens)
    print("Completion_tokens: ", usage.completion_tokens)
    print("Total_tokens: ", usage.total_tokens)
    print("Finish Response: ", response.choices[0].finish_reason)
    print("\n###########################################################\n")




