import json
import os
import re
from typing import Any

from langchain.agents import create_agent
from src.llm import get_chat_llm

from src.config import load_config
from src.logger import setup_logger
from src.rag.tools import create_agent_tools

AGENT_SYSTEM_PROMPT = """You are an AI Article Research Agent.

Use the available tools when needed to answer questions about collected AI articles.

Rules:
- Prefer search_ai_articles for questions about AI trends, topics, companies, models, or article content.
- Use list_recent_articles when the user asks what articles were collected.
- Use get_article_sources when the user asks for sources or references.
- Use tavily_web_search only when the user explicitly asks for latest web info or local data is insufficient.
- Do not invent facts.
- If the local knowledge base does not contain enough information and Tavily is unavailable, say so.
- Always mention relevant source URLs when available.
- Keep answers concise and practical.
"""


def extract_agent_output(result: dict[str, Any]) -> str:
    """Extract plain text content from a LangChain agent invocation result."""
    messages = result.get("messages", [])
    if not messages:
        return str(result)

    last_message = messages[-1]
    content = getattr(last_message, "content", "")

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(str(item.get("text", "")))
            else:
                parts.append(str(item))
        return "\n".join(part for part in parts if part).strip()

    return str(content)


def get_tool_map(tools: list[Any]) -> dict[str, Any]:
    """Build a lookup table that maps tool names to tool instances."""
    return {tool.name: tool for tool in tools}


def parse_limit(question: str, default: int = 5) -> int:
    """Parse a small numeric limit from a user question."""
    match = re.search(r"\b(\d{1,2})\b", question)
    if not match:
        return default

    limit = int(match.group(1))
    return max(1, min(limit, 20))


def invoke_tool(tool: Any, value: Any) -> str:
    """Invoke a LangChain tool with several supported payload shapes."""
    payloads = [
        value,
        str(value),
        {"query": value},
        {"question": value},
        {"input": value},
        {"limit": value},
        {"__arg1": value},
    ]

    last_error: Exception | None = None

    for payload in payloads:
        try:
            result = tool.invoke(payload)
            return str(result)
        except Exception as error:
            last_error = error

    raise RuntimeError(f"Tool invocation failed: {last_error}")


def answer_with_local_router(question: str, tools: list[Any]) -> str:
    """Route a question to the most suitable local tool without an LLM agent."""
    tool_map = get_tool_map(tools)
    normalized = question.lower()

    if any(
        keyword in normalized
        for keyword in [
            "list",
            "artikel terakhir",
            "artikel terbaru",
            "recent articles",
            "collected articles",
            "dikumpulkan",
        ]
    ):
        tool = tool_map.get("list_recent_articles")
        if not tool:
            return "Tool list_recent_articles is unavailable."

        limit = parse_limit(question)
        return invoke_tool(tool, limit)

    if any(
        keyword in normalized
        for keyword in [
            "source",
            "sources",
            "sumber",
            "url",
            "referensi",
            "reference",
        ]
    ):
        tool = tool_map.get("get_article_sources")
        if not tool:
            return "Tool get_article_sources is unavailable."

        return invoke_tool(tool, question)

    if any(
        keyword in normalized
        for keyword in [
            "web terbaru",
            "latest web",
            "internet",
            "tavily",
        ]
    ):
        tool = tool_map.get("tavily_web_search")
        if not tool:
            return "Tavily fallback is unavailable."

        return invoke_tool(tool, question)

    tool = tool_map.get("search_ai_articles")
    if not tool:
        return "Tool search_ai_articles is unavailable."

    return invoke_tool(tool, question)


def execute_text_tool_call(answer: str, tools: list[Any]) -> str | None:
    """Execute a serialized text tool call emitted by a model, if present."""
    text = answer.strip()
    marker = "<tool_call>"

    if not text.startswith(marker):
        return None

    payload = text[len(marker):].strip()
    match = re.match(r"([a-zA-Z_][a-zA-Z0-9_]*)\s*(\{.*\})", payload, re.DOTALL)

    if not match:
        return None

    tool_name = match.group(1)
    raw_args = match.group(2)

    try:
        parsed_args = json.loads(raw_args)
    except json.JSONDecodeError:
        return None

    arguments = parsed_args.get("arguments", parsed_args)

    if isinstance(arguments, dict):
        value = (
            arguments.get("__arg1")
            or arguments.get("query")
            or arguments.get("question")
            or arguments.get("input")
            or arguments.get("limit")
            or ""
        )
    else:
        value = arguments

    tool = get_tool_map(tools).get(tool_name)
    if not tool:
        return None

    return invoke_tool(tool, value)


def main() -> None:
    """Run the interactive command-line AI article agent."""
    config = load_config()
    logger = setup_logger(config)
    logger.info("Agent started", extra={"event": "agent.start"})

    provider = os.getenv("LLM_PROVIDER", "local").strip().lower()
    tools = create_agent_tools(config, logger)

    agent = None
    if provider in {"openai", "openagentic"}:
        llm = get_chat_llm(config)
        agent = create_agent(
            model=llm,
            tools=tools,
            system_prompt=AGENT_SYSTEM_PROMPT,
        )

    while True:
        try:
            question = input("Ask: ").strip()
        except KeyboardInterrupt:
            print("\nAgent stopped.")
            break

        if question.lower() in {"exit", "quit", "q"}:
            break
        if not question:
            continue

        logger.info("Agent question", extra={"event": "agent.question"})

        try:
            if agent is not None:
                result = agent.invoke(
                    {"messages": [{"role": "user", "content": question}]}
                )
                answer = extract_agent_output(result)

                tool_result = execute_text_tool_call(answer, tools)
                if tool_result is not None:
                    answer = tool_result
            else:
                answer = answer_with_local_router(question, tools)

            print(answer)
            logger.info("Agent answer", extra={"event": "agent.answer"})

        except KeyboardInterrupt:
            print("\nAgent stopped.")
            break
        except Exception as error:
            logger.error(
                "Agent failed",
                extra={
                    "event": "agent.failed",
                    "error_code": "AGENT_FAILED",
                    "error_message": str(error),
                },
            )
            print("Agent failed to answer. Check logs for details.")


if __name__ == "__main__":
    main()
