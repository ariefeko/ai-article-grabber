from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

from src.fallback.tavily_search import format_tavily_results_for_context, search_tavily
from src.rag.retriever import retrieve_documents
from src.types import AppConfig, RAGAnswer

INSUFFICIENT_ANSWER = "The available article data is not enough."

LOCAL_RAG_PROMPT = """You are an AI article research assistant.

Answer the user's question using only the provided local article context.

Rules:
- If the context is not enough, say: "The available article data is not enough."
- Keep the answer concise, practical, and clear.
- Mention source URLs when relevant.
- Do not invent facts.
- If multiple articles disagree, explain the difference.

Context:
{context}

Question:
{question}
"""

FALLBACK_PROMPT = """You are an AI article research assistant.

The local article database was not enough, so web fallback results are provided.

Answer the user's question using the provided web fallback context.

Rules:
- Mention that the answer used web fallback.
- Mention source URLs.
- Do not invent facts.
- Keep the answer concise, practical, and clear.

Fallback Context:
{context}

Question:
{question}
"""


def format_documents_for_context(documents: list) -> str:
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


def create_local_rag_chain(config: AppConfig, logger):
    prompt = ChatPromptTemplate.from_template(LOCAL_RAG_PROMPT)
    llm = ChatOllama(model=config.ollama_chat_model)
    return prompt | llm | StrOutputParser()


def _unique_sources(documents: list) -> list[str]:
    sources: list[str] = []
    seen: set[str] = set()
    for document in documents:
        source = document.metadata.get("source_url")
        if source and source not in seen:
            seen.add(source)
            sources.append(source)
    return sources


def _needs_fallback(question: str, answer: str, docs_count: int, min_docs: int) -> bool:
    latest_terms = ["latest", "terbaru", "web", "internet", "hari ini", "today"]
    return (
        docs_count < min_docs
        or INSUFFICIENT_ANSWER.lower() in answer.lower()
        or any(term in question.lower() for term in latest_terms)
    )


def ask_local_rag(
    question: str,
    config: AppConfig,
    logger,
) -> RAGAnswer:
    docs = retrieve_documents(question, config, logger)
    sources = _unique_sources(docs)
    if len(docs) < config.rag_min_relevant_docs:
        return RAGAnswer(answer=INSUFFICIENT_ANSWER, used_fallback=False, sources=sources)

    chain = create_local_rag_chain(config, logger)
    answer = chain.invoke({"context": format_documents_for_context(docs), "question": question})
    return RAGAnswer(answer=answer, used_fallback=False, sources=sources)


def ask_with_fallback(
    question: str,
    config: AppConfig,
    logger,
) -> RAGAnswer:
    local_answer = ask_local_rag(question, config, logger)
    if not _needs_fallback(
        question,
        local_answer.answer,
        len(local_answer.sources),
        config.rag_min_relevant_docs,
    ):
        return local_answer

    tavily_results = search_tavily(question, config, logger)
    if not tavily_results:
        if not config.tavily_api_key:
            local_answer.answer = f"{local_answer.answer} Web fallback is disabled because TAVILY_API_KEY is not configured."
        return local_answer

    prompt = ChatPromptTemplate.from_template(FALLBACK_PROMPT)
    llm = ChatOllama(model=config.ollama_chat_model)
    chain = prompt | llm | StrOutputParser()
    answer = chain.invoke(
        {
            "context": format_tavily_results_for_context(tavily_results),
            "question": question,
        }
    )
    logger.info("Fallback used", extra={"event": "agent.fallback.used"})
    return RAGAnswer(
        answer=answer,
        used_fallback=True,
        sources=[result.url for result in tavily_results],
    )
