from src.collector.filesystem import (
    append_indexed_file,
    list_markdown_files,
    read_indexed_files,
)
from src.exceptions import AppError
from src.rag.loader import load_markdown_file
from src.rag.splitter import split_documents
from src.rag.vectorstore import add_documents_to_vectorstore
from src.types import AppConfig


def index_markdown_articles(config: AppConfig, logger) -> int:
    """Index newly saved Markdown articles into the vector store."""
    logger.info("Indexing Markdown articles", extra={"event": "rag.index.start"})
    all_files = list_markdown_files(config.output_dir)
    indexed_files = read_indexed_files(config.indexed_files_file)

    new_files: list[str] = []
    for file_path in all_files:
        if file_path in indexed_files:
            logger.info(
                "Skipping indexed file",
                extra={"event": "rag.index.skip.duplicate", "file_path": file_path},
            )
            continue
        new_files.append(file_path)

    if not new_files:
        logger.info("No new files to index", extra={"event": "rag.index.done", "count": 0})
        return 0

    documents = []
    loaded_files = []
    for file_path in new_files:
        try:
            documents.append(load_markdown_file(file_path))
            loaded_files.append(file_path)
        except AppError as error:
            logger.error(
                "Failed to load Markdown",
                extra={
                    "event": "rag.index.failed",
                    "file_path": file_path,
                    "error_code": error.code,
                    "error_message": error.message,
                },
            )

    logger.info("Loaded documents", extra={"event": "rag.documents.loaded", "count": len(documents)})
    if not documents:
        logger.info("No loaded documents", extra={"event": "rag.index.done", "count": 0})
        return 0

    chunks = split_documents(
        documents,
        config.rag_chunk_size,
        config.rag_chunk_overlap,
    )
    logger.info("Split documents", extra={"event": "rag.documents.split", "count": len(chunks)})

    try:
        add_documents_to_vectorstore(config, chunks, logger)
    except AppError as error:
        logger.error(
            "Indexing failed",
            extra={
                "event": "rag.index.failed",
                "error_code": error.code,
                "error_message": error.message,
            },
        )
        raise

    for file_path in loaded_files:
        append_indexed_file(config.indexed_files_file, file_path)

    logger.info("Indexed Markdown articles", extra={"event": "rag.index.done", "count": len(loaded_files)})
    return len(loaded_files)
