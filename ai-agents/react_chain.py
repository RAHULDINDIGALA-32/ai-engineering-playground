# ReAct Loop Framework: Reasoning + Action Loop (Thought -> Action -> Observation)

import os
from pathlib import Path
from groq import Groq
from time import sleep
from dotenv import load_dotenv
import re
import logging

load_dotenv()
my_api_key = os.getenv("GROQ_API_KEY")

if not my_api_key:
    raise ValueError("GROQ_API_KEY environment variable not set. Please set it in your .env file.")

client = Groq(api_key=my_api_key)
MODEL = "openai/gpt-oss-120b"

# Use RTCZOF fromat to write the Prompts (mostly SYSTEM_PROMPTS)
# R - ROLE
# T - TASK
# C - CONSTRAINTS
# O - OUTPUT FORMAT
# Z - ZERO/ONE/FEW SHOT
# F - FALLBACK
SYSTEM_PROMPT = """
ROLE: You are an expert shopping assistant.

TOOLS: You have these tools:

get_product_price(product)
calculator(expression)


IMPORTANT:
- You MUST NEVER answer using your own knowledge.
- If information requires a tool, you MUST output exactly one Action.
- Call tools exactly like these examples:

Action: get_product_price("iPhone 17")
Action: calculator("5000 - 1000")

- Never write:
get_product_price(product="iPhone 17")

- Never write:
calculator(expression="5000 - 1000")

Follow these rules:

1. Decide what you need to do next.
2. Call ONLY ONE tool at a time.
3. After writing an Action, STOP immediately.
4. Never guess or invent a tool result.
5. Wait until you receive an Observation.
6. Then decide your next action.
7. When the task is complete, give the Final Answer.
8. If you answer without an Action when one is required, your response is invalid.

OUTPUT FORMAT:
Thought: what you need to do
Action: tool_name(argument)
When finished:
Final Answer: <your answer>
"""

def call_llm(messages):
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0
        )

        return response.choices[0].message.content
    except Exception as e:
        logging.exception("Failed to call LLM. Error: ", e)
        return None


## Agent Tools
def calculator(expression):
    try:
        return eval(expression)
    except:
        return "Error: Invalid expression"


def get_product_price(product):
    product_prices = {
        "iphone 15": 999.99,
        "iphone 15 pro": 1199.99,
        "iphone 17":  1799.99,
        "macbook pro": 1999.99,
        "airpods pro": 249.99,
        "ipad pro": 1099.99,
        "apple watch": 399.99
    }
    return product_prices.get(product.lower(), "Product not found")

tools = {
    "get_product_price": get_product_price,
    "calculator": calculator
}


def run_agent(user_query):

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        },
        {
            "role": "user",
            "content": user_query
        }
    ] 

    MAX_STEPS = 5

    for step in  range(MAX_STEPS):
        print("\n---------------------")
        print("STEP ", step+1)
        print("---------------------")

        llm_answer = call_llm(messages)
        print(llm_answer)

        #Agent has finished (based on output format)
        if "Final Answer:" in llm_answer:
            break

        #Find the action
        match_action  = re.search(
            r"Action:\s*(\w+)\((.*?)\)",
            llm_answer
        ) 

        if match_action:

            tool_name = match_action.group(1)
            tool_input = match_action.group(2)
            tool_input = tool_input.strip()
            tool_input = tool_input.strip('"')

            # Run the tool
            if tool_name in tools:
                tool = tools[tool_name]
                observation = tool(tool_input)
            else: 
                observation = "Tool NOT found"

            print("Observation: ", observation)


            # Add LLM response to memory
            messages.append({
                "role": "assistant",
                "content": llm_answer
            })

            # Give tool result (observation) back to LLM
            messages.append({
                "role": "user",
                "content": " Observation: " + str(observation)
            })

            sleep(3)



user_query_prompt = """
I am planning to buy iphone 17 & i have 4500 dollars. Am i able to buy it ? if so how much will i left with ?
"""

run_agent(user_query_prompt)




 






