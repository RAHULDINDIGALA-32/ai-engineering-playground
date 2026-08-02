import os
from dotenv import load_dotenv
from groq import Groq
from pydantic import BaseModel

load_dotenv()

my_api_key = os.getenv("GROQ_API_KEY")
if not my_api_key:
    raise ValueError("GROQ_API_KEY environment variable is not set. Please set it in your .env file.")

client = Groq(api_key=my_api_key)

model = "llama-3.3-70b-versatile"

class Ticket(BaseModel):
    name: str
    email: str
    phone: str
    location: str
    issue: str
    severity: str

severity_levels = ["low", "medium", "high", "critical"]

schema = Ticket.model_json_schema()
response_format = {
    "type" :  "json_object",
}

system_prompt = f"""You are a helpful assistant that extracts structured information from user input. 
The user will provide a description of a technical issue, and you will extract the relevant information into a structured JSON format according to the following schema:{schema}. 
For the severity field, please ensure that the value is one of the following: {severity_levels}. If the severity level is not explicitly mentioned in the user input, please infer it based on the description of the issue. If you cannot determine a severity level, please default to "medium"."""

system_message = {
    "role": "system",
    "content": system_prompt
}

user_prompt= "I am Rahul Dindigala. I am facing an issue with my laptop. The screen flickers intermittently, and sometimes it goes completely black for a few seconds. This is affecting my work, and I need it fixed urgently. My email is rahul.dindigala@example.com, and my phone number is +915551234567. I am located in Warangal, INDIA. Please help me resolve this issue as soon as possible."


user_message = {
    "role": "user",
    "content": user_prompt
}

messages = [system_message, user_message]

response = client.chat.completions.create(
    model=model,
    messages=messages,
    response_format=response_format
)

structured_ticket = response.choices[0].message.content

print("###########################################################")
print("Structured Ticket:\n")
print(structured_ticket)
print("\n###########################################################")



# Reading the structured ticket using Json library
import json

raw_json_data = structured_ticket
json_data_file = json.loads(raw_json_data)
ticket = Ticket(**json_data_file)

print("Extracted Ticket Information:\n")
print("Name: ", json_data_file.get("name"))
print("Email: ", json_data_file.get("email"))
print("Phone: ", json_data_file.get("phone"))
print("Location: ", json_data_file.get("location"))
print("Issue: ", ticket.issue)
print("Severity: ", ticket.severity)

