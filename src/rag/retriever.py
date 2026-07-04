from langchain_core.documents import Document

from src.exceptions import AppError
from src.rag.vectorstore import get_qdrant_vectorstore
from src.types import AppConfig


def get_retriever(config: AppConfig, logger):
    """Create a configured retriever from the Qdrant vector store."""
    vectorstore = get_qdrant_vectorstore(config, logger)
    return vectorstore.as_retriever(search_kwargs={"k": config.rag_retriever_k})


def retrieve_documents(
    question: str,
    config: AppConfig,
    logger,
) -> list[Document]:
    """Retrieve relevant article documents for a question."""
    logger.info("Retrieving documents", extra={"event": "rag.retrieve.start"})
    try:
        retriever = get_retriever(config, logger)
        docs = retriever.invoke(question)
        if docs:
            logger.info(
                "Retrieved documents",
                extra={"event": "rag.retrieve.done", "count": len(docs)},
            )
        else:
            logger.info("No documents retrieved", extra={"event": "rag.retrieve.empty"})
        return docs
    except Exception as error:
        raise AppError("RAG_RETRIEVE_FAILED", "Failed to retrieve documents", error) from error
