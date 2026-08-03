import os
from dotenv import load_dotenv
from groq import Groq
#import json


load_dotenv()

my_api_key = os.getenv("GROQ_API_KEY")

if not my_api_key:
    raise ValueError("GROQ_API_KEY environment variable is not set.")

client = Groq(api_key=my_api_key)
DEFAULT_MODEL = "openai/gpt-oss-120b"

def parse_query(system_prompt:str, query_prompt: str, response_format={"type": "json_object"}):

   messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": query_prompt}
    ]

   response = client.chat.completions.create(
        model = DEFAULT_MODEL,
         messages = messages,
         response_format = response_format
   )

  
   #raw_content = response.choices[0].message.content
   #json_content = json.loads(raw_content)
   #return json_content

   return response.choices[0].message.content
