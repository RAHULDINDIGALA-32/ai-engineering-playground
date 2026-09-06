"""A tool-calling agent that can search the web and calculate expressions. (MANUAL)"""

import ast
import json
import os
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from dotenv import load_dotenv
from groq import Groq


load_dotenv()
my_api_key = os.getenv("GROQ_API_KEY")
tavily_api_key = os.getenv("TAVILY_API_KEY")

if not my_api_key:
    raise ValueError("GROQ_API_KEY environment variable not set. Please set it in your .env file.")


MODEL = "openai/gpt-oss-120b"
client = Groq(api_key=my_api_key)

UNSUPPORTED_RESPONSE = "I’m sorry, I don’t have an available tool to answer that request."


def web_search(query: str) -> dict[str, Any]:
    """Search the web through Tavily and return a compact list of results."""
    if not isinstance(query, str) or not query.strip():
        return {"error": "Search query must be a non-empty string."}
    if not tavily_api_key:
        return {"error": "TAVILY_API_KEY environment variable not set. Please set it in your .env file."}

    payload = json.dumps({"api_key": tavily_api_key, "query": query.strip(),
                          "search_depth": "basic", "max_results": 5}).encode("utf-8")
    request = Request("https://api.tavily.com/search", data=payload,
                      headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(request, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        return {"error": f"Tavily search failed (HTTP {error.code})."}
    except (URLError, TimeoutError, json.JSONDecodeError) as error:
        return {"error": f"Tavily search failed: {error}"}

    return {
        "query": query,
        "answer": data.get("answer"),
        "results": [
            {"title": result.get("title", ""), "url": result.get("url", ""),
             "content": result.get("content", "")}
            for result in data.get("results", [])
        ],
    }


def calculator(expression: str) -> int | float | str:
    """Safely evaluate a mathematical expression containing arithmetic only."""
    if not isinstance(expression, str) or not expression.strip():
        return "Error: Invalid expression"

    operators = {
        ast.Add: lambda left, right: left + right, ast.Sub: lambda left, right: left - right,
        ast.Mult: lambda left, right: left * right, ast.Div: lambda left, right: left / right,
        ast.FloorDiv: lambda left, right: left // right, ast.Mod: lambda left, right: left % right,
        ast.Pow: lambda left, right: left ** right,
    }

    def evaluate(node: ast.AST) -> int | float:
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return node.value
        if isinstance(node, ast.UnaryOp) and type(node.op) in (ast.UAdd, ast.USub):
            value = evaluate(node.operand)
            return value if isinstance(node.op, ast.UAdd) else -value
        if isinstance(node, ast.BinOp) and type(node.op) in operators:
            return operators[type(node.op)](evaluate(node.left), evaluate(node.right))
        raise ValueError("Only arithmetic expressions are allowed")

    try:
        return evaluate(ast.parse(expression, mode="eval").body)
    except (ArithmeticError, SyntaxError, TypeError, ValueError, OverflowError):
        return "Error: Invalid expression"


# Groq/OpenAI-compatible tool definitions supplied to the model on every turn.
tools = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the current web for facts, news, pages, or other up-to-date information.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "A focused web search query."}},
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Evaluate a valid arithmetic expression, for example 2+(3*12+(3/2)-5).",
            "parameters": {
                "type": "object",
                "properties": {"expression": {"type": "string", "description": "Arithmetic using numbers, +, -, *, /, //, %, **, and parentheses."}},
                "required": ["expression"],
                "additionalProperties": False,
            },
        },
    },
]

TOOL_FUNCTIONS = {"web_search": web_search, "calculator": calculator}

SYSTEM_PROMPT = f"""
You are a precise tool-using assistant. You have only the supplied web_search and calculator tools.
Decide whether to call a tool at each step, and may call tools multiple times if needed. Use
web_search for factual or current information and calculator for arithmetic. Never invent a tool
result or answer a factual request from memory. When tools do not cover the request, respond exactly:
{UNSUPPORTED_RESPONSE}
After receiving sufficient tool results, give a concise final answer based only on those results.
If a tool reports an error or no useful results, say that plainly instead of guessing.
""".strip()


def run_agent(user_query: str, max_steps: int = 8) -> str:
    """Run the agent until it answers or reaches its tool-call limit."""
    messages: list[Any] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_query},
    ]
    for _ in range(max_steps):
        response = client.chat.completions.create(
            model=MODEL, 
            messages=messages, 
            tools=tools, 
            tool_choice="auto", 
            temperature=0
        )
        message = response.choices[0].message
        tool_calls = message.tool_calls or []
        messages.append(message)
        if not tool_calls:
            return message.content or UNSUPPORTED_RESPONSE

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            try:
                arguments = json.loads(tool_call.function.arguments or "{}")
                result = TOOL_FUNCTIONS[function_name](**arguments)
            except (KeyError, TypeError, json.JSONDecodeError) as error:
                result = {"error": f"Tool call could not be completed: {error}"}
            messages.append({"role": "tool", "tool_call_id": tool_call.id,
                             "name": function_name, "content": json.dumps(result)})

    return "I’m sorry, I could not complete that request within the available tool steps."


if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) or input("Ask a question: ").strip()
    print(run_agent(query))
