from dotenv import load_dotenv
from importlib.metadata import version

# from langchain_openai import ChatOpenAI
# from langchain_anthropic import ChatAnthropic
from langchain_openrouter import ChatOpenRouter

load_dotenv()

core_version = version("langchain-core")
lg_version = version("langgraph")


def main():
    print("Hello from Langgraph!")
    print(f"Langgraph version: {lg_version}")
    print(f"Langchain Core version: {core_version}")

    """
    llm_openai = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)
    response = llm_openai.invoke("Say Hello uniquely in a concise way.")
    print(f"OpenAI Response: {response}")

    llm_anthropic = ChatAnthropic(model_name="claude-haiku-4-5-20251001", temperature=0)
    response = llm_anthropic.invoke("Say Hello uniquely in a concise way.")
    print(f"Anthropic Response: {response}")
    """

    llm_openrouter = ChatOpenRouter(
        model_name="openrouter/free", temperature=0, max_tokens=1024
    )
    response = llm_openrouter.invoke("Say Hello uniquely in a concise way.")
    print(f"OpenRouter Response: {response.content}")


if __name__ == "__main__":
    main()
