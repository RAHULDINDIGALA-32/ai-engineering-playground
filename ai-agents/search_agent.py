from __future__ import annotations

import ast
import json
import logging
import math
import operator
import os
import random
import sys
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import groq
from dotenv import load_dotenv
from groq import Groq

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

MODEL = "openai/gpt-oss-120b"
MAX_STEPS = 8
REQUEST_TIMEOUT = 20
TAVILY_MAX_RESULTS = 5

# How many messages (after the system prompt) we proactively keep around.
MAX_HISTORY_MESSAGES = 30

# Groq "too many requests" (429) handling.
RATE_LIMIT_MAX_RETRIES = 5
RATE_LIMIT_BASE_DELAY = 1.0

# Other Groq API/network hiccups (5xx, connection errors).
API_ERROR_MAX_RETRIES = 3

# Tavily web search transient-failure retries.
SEARCH_MAX_RETRIES = 3

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY environment variable not set. Please set it in your .env file.")

if not TAVILY_API_KEY:
    raise ValueError("TAVILY_API_KEY environment variable not set. Please set it in your .env file.")

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("tool_agent")

client = Groq(api_key=GROQ_API_KEY)

UNSUPPORTED_RESPONSE = "I'm sorry, I don't have an available tool to answer that request."


def _sleep_with_backoff(attempt: int, base: float = 1.0, cap: float = 30.0) -> None:
    """Exponential backoff with a little jitter so concurrent callers don't sync up."""
    delay = min(cap, base * (2 ** (attempt - 1))) + random.uniform(0, 0.5)
    time.sleep(delay)


# --------------------------------------------------------------------------
# Tool: web_search (Tavily)
# --------------------------------------------------------------------------

def web_search(query: str) -> dict[str, Any]:
    """Search the web through Tavily and return a compact list of results.
    
    """
    if not isinstance(query, str) or not query.strip():
        return {"error": "Search query must be a non-empty string."}
    if not TAVILY_API_KEY:
        return {"error": "TAVILY_API_KEY environment variable not set. Please set it in your .env file."}

    query = query.strip()
    payload = json.dumps({
        "api_key": TAVILY_API_KEY,
        "query": query,
        "search_depth": "basic",
        "max_results": TAVILY_MAX_RESULTS,
    }).encode("utf-8")

    for attempt in range(1, SEARCH_MAX_RETRIES + 1):
        request = Request(
            "https://api.tavily.com/search",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=REQUEST_TIMEOUT) as response:
                data = json.loads(response.read().decode("utf-8"))
            return {
                "query": query,
                "answer": data.get("answer"),
                "results": [
                    {"title": result.get("title", ""), "url": result.get("url", ""),
                     "content": result.get("content", "")}
                    for result in data.get("results", [])[:TAVILY_MAX_RESULTS]
                ],
            }
        except HTTPError as error:
            if error.code == 429 or error.code >= 500:
                logger.warning(
                    "Tavily transient error (attempt %d/%d): HTTP %d",
                    attempt, SEARCH_MAX_RETRIES, error.code,
                )
                if attempt < SEARCH_MAX_RETRIES:
                    _sleep_with_backoff(attempt)
                    continue
                return {"error": "Web search is temporarily unavailable (rate limited or server error). Please try again shortly."}
            # 4xx other than 429 (bad key, bad request) won't succeed on retry.
            return {"error": f"Tavily search failed (HTTP {error.code})."}
        except (URLError, TimeoutError, json.JSONDecodeError) as error:
            logger.warning(
                "Tavily connection error (attempt %d/%d): %s", attempt, SEARCH_MAX_RETRIES, error,
            )
            if attempt < SEARCH_MAX_RETRIES:
                _sleep_with_backoff(attempt)
                continue
            return {"error": f"Could not reach the web search service: {error}"}

    return {"error": "Web search failed after retries."}  # defensive fallback, not normally reached


# --------------------------------------------------------------------------
# Tool: calculator (safe AST-whitelist evaluation)
# --------------------------------------------------------------------------

_BIN_OPS: dict[type, Any] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY_OPS: dict[type, Any] = {ast.UAdd: operator.pos, ast.USub: operator.neg}
_ALLOWED_FUNCS: dict[str, Any] = {
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sqrt": math.sqrt,
    "pow": math.pow,
}
_MAX_ABS_EXPONENT = 1000  # guards against expressions like 9**9**9 hanging the process
_MAX_EXPRESSION_LENGTH = 500


class _CalculatorError(ValueError):
    """Raised internally for any expression the evaluator refuses to run."""


def _evaluate(node: ast.AST) -> float:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
            raise _CalculatorError("Only numeric constants are allowed.")
        return node.value

    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
        return _UNARY_OPS[type(node.op)](_evaluate(node.operand))

    if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
        left = _evaluate(node.left)
        right = _evaluate(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > _MAX_ABS_EXPONENT:
            raise _CalculatorError("Exponent is too large.")
        try:
            return _BIN_OPS[type(node.op)](left, right)
        except ZeroDivisionError as exc:
            raise _CalculatorError("Division by zero.") from exc

    if isinstance(node, ast.Call):
        func_name = node.func.id if isinstance(node.func, ast.Name) else None
        if func_name not in _ALLOWED_FUNCS:
            raise _CalculatorError(f"Function '{func_name or '?'}' is not allowed.")
        if node.keywords:
            raise _CalculatorError("Keyword arguments are not supported.")
        args = [_evaluate(arg) for arg in node.args]
        try:
            return _ALLOWED_FUNCS[func_name](*args)
        except (TypeError, ValueError) as exc:
            raise _CalculatorError(str(exc)) from exc

    raise _CalculatorError("Expression contains unsupported syntax.")


def calculator(expression: str) -> dict[str, Any]:
    """Safely evaluate a mathematical expression.

    Supports +, -, *, /, //, %, **, unary +/-, and abs/round/min/max/sqrt/pow.
    No name lookups, attribute access, or comprehensions are permitted.
    """
    if not isinstance(expression, str) or not expression.strip():
        return {"error": "Expression must be a non-empty string."}
    if len(expression) > _MAX_EXPRESSION_LENGTH:
        return {"error": "Expression is too long."}

    try:
        parsed = ast.parse(expression, mode="eval")
        result = _evaluate(parsed.body)
    except SyntaxError:
        return {"error": "Invalid syntax in expression."}
    except _CalculatorError as exc:
        return {"error": str(exc)}
    except (ArithmeticError, TypeError, OverflowError, RecursionError) as exc:
        return {"error": f"Could not evaluate expression: {exc}"}

    return {"expression": expression, "result": result}


# --------------------------------------------------------------------------
# Groq/OpenAI-compatible tool definitions supplied to the model on every turn.
# --------------------------------------------------------------------------

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
            "description": (
                "Evaluate an arithmetic expression. Supports +, -, *, /, //, %, ** and the "
                "functions abs, round, min, max, sqrt, pow. Example: sqrt(16) + 2**3."
            ),
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


# --------------------------------------------------------------------------
# Resilient LLM call: rate limits, oversized requests, and network errors
# --------------------------------------------------------------------------

class AgentRuntimeError(Exception):
    """Raised when the model call ultimately cannot be completed. Message is user-facing."""


class ContextLengthExceeded(Exception):
    """Raised when the LLM reports the request is too large for the model's context window."""


def _looks_like_context_length_error(message: str) -> bool:
    message = message.lower()
    keywords = (
        "too large", "context length", "context_length", "reduce the length",
        "maximum context", "request too large", "token limit", "tokens exceed",
    )
    return any(keyword in message for keyword in keywords)


def _retry_after_seconds(error: Exception, default: float) -> float:
    """Honor a Retry-After header from the LLM's (Groq) rate-limit response if present."""
    response = getattr(error, "response", None)
    header = None
    if response is not None:
        headers = getattr(response, "headers", None)
        if headers is not None:
            header = headers.get("retry-after") or headers.get("Retry-After")
    if header:
        try:
            return float(header)
        except ValueError:
            pass
    return default


def _role_of(item: Any) -> str | None:
    if isinstance(item, dict):
        return item.get("role")
    return getattr(item, "role", None)


def call_model(messages: list[Any]):
    """Call Groq with resilience for rate limits, oversized requests, and network errors.

    Raises:
        ContextLengthExceeded: the request was too large (token/context limit).
        AgentRuntimeError: the call could not be completed after retries; the
            exception message is safe to show directly to the user.
    """
    rate_limit_attempts = 0
    api_error_attempts = 0

    while True:
        try:
            return client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=0,
            )
        except groq.RateLimitError as error:
            # "Too many requests" — back off and retry, honoring Retry-After if given.
            rate_limit_attempts += 1
            if rate_limit_attempts > RATE_LIMIT_MAX_RETRIES:
                logger.error("Exhausted rate-limit retries: %s", error)
                raise AgentRuntimeError(
                    "the model is receiving too many requests right now. Please wait a moment and try again"
                ) from error
            delay = _retry_after_seconds(
                error, RATE_LIMIT_BASE_DELAY * (2 ** (rate_limit_attempts - 1))
            )
            logger.warning(
                "Rate limited by Groq (attempt %d/%d). Retrying in %.1fs.",
                rate_limit_attempts, RATE_LIMIT_MAX_RETRIES, delay,
            )
            time.sleep(delay + random.uniform(0, 0.5))
        except groq.APIStatusError as error:
            status_code = getattr(error, "status_code", None)
            message = str(error)

            if status_code == 413 or _looks_like_context_length_error(message):
                logger.warning("Context/token limit hit: %s", message)
                raise ContextLengthExceeded(message) from error

            if status_code in (401, 403):
                # Bad/expired API key or no access — retrying can't fix this.
                logger.error("Groq authentication/permission error: %s", error)
                raise AgentRuntimeError(
                    f"authentication with the language model API failed ({error})"
                ) from error

            # Other API errors (validation, 5xx) — a few quick retries, then give up.
            api_error_attempts += 1
            if api_error_attempts > API_ERROR_MAX_RETRIES:
                logger.error("Exhausted retries after repeated API errors: %s", error)
                raise AgentRuntimeError(
                    f"the language model API returned an error and retries were exhausted ({error})"
                ) from error
            logger.warning(
                "Groq API error (attempt %d/%d): %s", api_error_attempts, API_ERROR_MAX_RETRIES, error,
            )
            _sleep_with_backoff(api_error_attempts)
        except groq.APIConnectionError as error:
            api_error_attempts += 1
            if api_error_attempts > API_ERROR_MAX_RETRIES:
                logger.error("Exhausted retries after connection errors: %s", error)
                raise AgentRuntimeError("could not reach the language model service") from error
            logger.warning(
                "Connection error talking to Groq (attempt %d/%d): %s",
                api_error_attempts, API_ERROR_MAX_RETRIES, error,
            )
            _sleep_with_backoff(api_error_attempts)


def _trim_history(messages: list[Any]) -> list[Any]:
    """Proactively bound history length so we're less likely to hit a token limit.

    Keeps the system prompt plus the most recent messages, making sure the
    kept slice doesn't start on an orphaned "tool" response (which requires
    its parent assistant tool_call message to be valid).
    """
    if len(messages) <= MAX_HISTORY_MESSAGES:
        return messages

    system_message = messages[0]
    tail = messages[-(MAX_HISTORY_MESSAGES - 1):]
    while tail and _role_of(tail[0]) == "tool":
        tail = tail[1:]

    return [system_message, *tail]


def _shrink_messages_for_retry(messages: list[Any]) -> list[Any] | None:
    """keep just the system prompt + the most recent user message. 
    Returns None if the conversation is already at that minimal size (nothing left to shrink).
    """
    system_message = messages[0]
    last_user_message = next(
        (m for m in reversed(messages) if isinstance(m, dict) and m.get("role") == "user"), None
    )
    if last_user_message is None:
        return None
    minimal = [system_message, last_user_message]
    if messages == minimal:
        return None
    return minimal


# --------------------------------------------------------------------------
# Agent loop
# --------------------------------------------------------------------------

def run_agent(user_query: str, max_steps: int = MAX_STEPS) -> str:
    """Run the agent until it answers or reaches its tool-call/error limits."""
    if not isinstance(user_query, str) or not user_query.strip():
        return "Please provide a non-empty question."

    messages: list[Any] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_query.strip()},
    ]
    already_shrunk = False

    for step in range(1, max_steps + 1):
        messages = _trim_history(messages)

        try:
            response = call_model(messages)
        except ContextLengthExceeded:
            shrunk = _shrink_messages_for_retry(messages)
            if shrunk is None or already_shrunk:
                return (
                    "Sorry, this conversation grew too large for the model to process, even "
                    "after trimming the history. Please start a new question or ask something "
                    "more specific."
                )
            logger.warning("Shrinking conversation history after a context/token-limit error.")
            messages = shrunk
            already_shrunk = True
            continue
        except AgentRuntimeError as error:
            return f"Sorry, I ran into a problem talking to the model: {error}."

        message = response.choices[0].message
        tool_calls = message.tool_calls or []
        messages.append(message)
        if not tool_calls:
            return message.content or UNSUPPORTED_RESPONSE

        logger.debug("Step %d/%d: executing %d tool call(s)", step, max_steps, len(tool_calls))
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            try:
                arguments = json.loads(tool_call.function.arguments or "{}")
                function = TOOL_FUNCTIONS.get(function_name)
                if function is None:
                    result: Any = {"error": f"Unknown tool '{function_name}'."}
                else:
                    result = function(**arguments)
            except (TypeError, json.JSONDecodeError) as error:
                result = {"error": f"Tool call could not be completed: {error}"}
            except Exception as error:  # noqa: BLE001 - a tool must never crash the agent loop
                logger.exception("Unhandled error in tool %s", function_name)
                result = {"error": f"Tool '{function_name}' failed unexpectedly: {error}"}
            messages.append({"role": "tool", "tool_call_id": tool_call.id,
                             "name": function_name, "content": json.dumps(result)})

    return "I'm sorry, I could not complete that request within the available tool steps."


if __name__ == "__main__":
    try:
        query = " ".join(sys.argv[1:]) or input("Ask a question: ").strip()
        answer = run_agent(query)
        print("-" * 80)
        print(answer)
        print("-" * 80)
    except (EOFError, KeyboardInterrupt):
        print()
        sys.exit(0)