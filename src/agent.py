from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_ollama import ChatOllama

from src.config import load_config
from src.logger import setup_logger
from src.rag.tools import create_agent_tools

AGENT_PROMPT = """You are an AI Article Research Agent.

You have access to these tools:

{tools}

Use the tools when needed to answer questions about collected AI articles.

Rules:
- Prefer search_ai_articles for questions about AI trends, topics, companies, models, or article content.
- Use list_recent_articles when the user asks what articles were collected.
- Use get_article_sources when the user asks for sources or references.
- Use tavily_web_search only when the user explicitly asks for latest web info or local data is insufficient.
- Do not invent facts.
- If the local knowledge base does not contain enough information and Tavily is unavailable, say so.
- Always mention relevant source URLs when available.
- Keep answers concise and practical.

Use this format:

Question: the input question
Thought: think about what tool is needed
Action: the action to take, must be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
Thought: I now know the final answer
Final Answer: the final answer to the user

Question: {input}
Thought: {agent_scratchpad}
"""


def main() -> None:
    config = load_config()
    logger = setup_logger(config)
    logger.info("Agent started", extra={"event": "agent.start"})

    llm = ChatOllama(model=config.ollama_chat_model)
    tools = create_agent_tools(config, logger)
    prompt = PromptTemplate.from_template(AGENT_PROMPT)
    agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)
    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=False,
        handle_parsing_errors=True,
    )

    while True:
        question = input("Ask: ").strip()
        if question.lower() in {"exit", "quit", "q"}:
            break
        if not question:
            continue

        logger.info("Agent question", extra={"event": "agent.question"})
        try:
            result = executor.invoke({"input": question})
            print(result["output"])
            logger.info("Agent answer", extra={"event": "agent.answer"})
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
