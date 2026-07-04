import os
from typing import Any

from langchain_ollama import ChatOllama


def get_llm_provider() -> str:
    return os.getenv("LLM_PROVIDER", "local").strip().lower()


def get_local_chat_llm(config: Any) -> Any:
    return ChatOllama(model=config.ollama_chat_model)


def get_chat_llm(config: Any) -> Any:
    provider = get_llm_provider()

    if provider == "openagentic":
        api_key = os.getenv("OPENAGENTIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENAGENTIC_API_KEY is required when LLM_PROVIDER=openagentic"
            )

        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=os.getenv("OPENAGENTIC_MODEL", "glm-5"),
            api_key=api_key,
            base_url=os.getenv(
                "OPENAGENTIC_BASE_URL",
                "https://aimurah.my.id/api/v1",
            ),
            temperature=0,
        )

    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")

        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-5.4"),
            api_key=api_key,
            temperature=0,
        )

    return get_local_chat_llm(config)