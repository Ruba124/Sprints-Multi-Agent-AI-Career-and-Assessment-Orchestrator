import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()


def get_llm(temperature: float = 0) -> ChatOpenAI:
    """Return a configured ChatOpenAI client using Groq or OpenRouter based on LLM_PROVIDER."""
    provider = os.getenv("LLM_PROVIDER", "groq").lower()

    if provider == "groq":
        return ChatOpenAI(
            api_key=os.getenv("GROQ_API_KEY"),
            base_url="https://api.groq.com/openai/v1",
            model="qwen/qwen3.8-27b",
            temperature=temperature,
        )

    # Default / fallback: OpenRouter
    return  ChatOpenAI(model="openrouter/free",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
    temperature=temperature)