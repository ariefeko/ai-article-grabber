from langchain_ollama import OllamaEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

from src.exceptions import AppError
from src.types import AppConfig


def create_embeddings(config: AppConfig):
    return OllamaEmbeddings(model=config.ollama_embedding_model)


def get_qdrant_vectorstore(config: AppConfig, logger):
    logger.info("Connecting to Qdrant", extra={"event": "qdrant.connect.start"})
    try:
        embeddings = create_embeddings(config)
        client = QdrantClient(
            url=config.qdrant_url,
            api_key=config.qdrant_api_key or None,
        )
        vectorstore = QdrantVectorStore(
            client=client,
            collection_name=config.qdrant_collection_name,
            embedding=embeddings,
        )
        logger.info("Connected to Qdrant", extra={"event": "qdrant.connect.done"})
        return vectorstore
    except Exception as error:
        logger.error(
            "Qdrant connection failed",
            extra={
                "event": "qdrant.connect.failed",
                "error_code": "QDRANT_FAILED",
                "error_message": str(error),
            },
        )
        raise AppError("QDRANT_FAILED", "Failed to connect to Qdrant", error) from error


def add_documents_to_vectorstore(
    config: AppConfig,
    documents: list,
    logger,
) -> None:
    try:
        vectorstore = get_qdrant_vectorstore(config, logger)
        vectorstore.add_documents(documents)
        logger.info(
            "Updated vector store",
            extra={"event": "rag.vectorstore.updated", "count": len(documents)},
        )
    except AppError:
        raise
    except Exception as error:
        raise AppError("RAG_INDEX_FAILED", "Failed to add documents to Qdrant", error) from error
