from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from src.fallback.tavily_search import format_tavily_results_for_context, search_tavily
from src.llm import get_chat_llm, get_llm_provider, get_local_chat_llm
from src.rag.retriever import retrieve_documents
from src.types import AppConfig, RAGAnswer

INSUFFICIENT_ANSWER = "The available article data is not enough."

LOCAL_RAG_PROMPT = """You are an AI article research assistant.

Answer the user's question using only the provided local article context.

Rules:
- Use only the provided local article context.
- Do not use outside knowledge.
- Do not use web results unless they are explicitly provided in the context.
- Do not infer years, trends, companies, or claims that are not present in the context.
- If the user asks about collected articles, summarize only the collected local articles.
- If the context is limited, answer with what can be concluded from the available articles.
- If the context is not enough, say exactly: "The available article data is not enough."
- Mention source URLs when relevant.
- Keep the answer concise, practical, and clear.
- Do not invent facts.

Context:
{context}

Question:
{question}
"""

FALLBACK_PROMPT = """You are an AI article research assistant.

The user explicitly allowed web fallback, and web fallback results are provided.

Answer the user's question using the provided web fallback context.

Rules:
- Mention that the answer used web fallback.
- Use only the provided fallback context.
- Mention source URLs.
- Do not invent facts.
- Keep the answer concise, practical, and clear.

Fallback Context:
{context}

Question:
{question}
"""


def format_documents_for_context(documents: list) -> str:
    """Format retrieved documents into prompt-ready context blocks."""
    blocks: list[str] = []

    for document in documents:
        metadata = document.metadata
        blocks.append(
            "\n".join(
                [
                    f"Title: {metadata.get('title', 'Untitled')}",
                    f"Source: {metadata.get('source_url', '')}",
                    f"File: {metadata.get('file_path', '')}",
                    document.page_content,
                ]
            )
        )

    return "\n\n---\n\n".join(blocks)


def invoke_with_model_fallback(
    prompt: ChatPromptTemplate,
    payload: dict,
    config: AppConfig,
    logger,
) -> str:
    """Invoke the configured model and fall back to local LLM when allowed."""
    try:
        llm = get_chat_llm(config)
        chain = prompt | llm | StrOutputParser()
        return chain.invoke(payload)

    except Exception as error:
        if get_llm_provider() == "local":
            raise

        logger.warning(
            "Primary model failed, using local model fallback",
            extra={
                "event": "model.fallback.used",
                "error_code": "MODEL_FALLBACK_USED",
                "error_message": str(error),
            },
        )

        fallback_llm = get_local_chat_llm(config)
        fallback_chain = prompt | fallback_llm | StrOutputParser()
        return fallback_chain.invoke(payload)


def _unique_sources(documents: list) -> list[str]:
    """Return source URLs from documents while preserving first-seen order."""
    sources: list[str] = []
    seen: set[str] = set()

    for document in documents:
        source = document.metadata.get("source_url")
        if source and source not in seen:
            seen.add(source)
            sources.append(source)

    return sources


def _needs_fallback(answer: str, docs_count: int, min_docs: int) -> bool:
    """Decide whether a local answer needs external fallback support."""
    return (
        docs_count < min_docs
        or INSUFFICIENT_ANSWER.lower() in answer.lower()
    )


def ask_local_rag(
    question: str,
    config: AppConfig,
    logger,
) -> RAGAnswer:
    """Answer a question using only locally indexed article documents."""
    docs = retrieve_documents(question, config, logger)
    sources = _unique_sources(docs)

    if len(docs) < config.rag_min_relevant_docs:
        return RAGAnswer(
            answer=INSUFFICIENT_ANSWER,
            used_fallback=False,
            sources=sources,
        )

    prompt = ChatPromptTemplate.from_template(LOCAL_RAG_PROMPT)
    payload = {
        "context": format_documents_for_context(docs),
        "question": question,
    }

    answer = invoke_with_model_fallback(prompt, payload, config, logger)

    return RAGAnswer(
        answer=answer,
        used_fallback=False,
        sources=sources,
    )


def ask_with_fallback(
    question: str,
    config: AppConfig,
    logger,
    use_fallback: bool = False,
) -> RAGAnswer:
    """Answer a question with optional Tavily fallback context."""
    local_answer = ask_local_rag(question, config, logger)

    if not use_fallback:
        if _needs_fallback(
            local_answer.answer,
            len(local_answer.sources),
            config.rag_min_relevant_docs,
        ):
            logger.info(
                "Fallback skipped",
                extra={"event": "agent.fallback.skipped"},
            )
        return local_answer

    tavily_results = search_tavily(question, config, logger)

    if not tavily_results:
        if not config.tavily_api_key:
            local_answer.answer = (
                f"{local_answer.answer} "
                "Web fallback is disabled because TAVILY_API_KEY is not configured."
            )
        return local_answer

    prompt = ChatPromptTemplate.from_template(FALLBACK_PROMPT)
    payload = {
        "context": format_tavily_results_for_context(tavily_results),
        "question": question,
    }

    answer = invoke_with_model_fallback(prompt, payload, config, logger)

    logger.info("Fallback used", extra={"event": "agent.fallback.used"})

    return RAGAnswer(
        answer=answer,
        used_fallback=True,
        sources=[result.url for result in tavily_results],
    )
