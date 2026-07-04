from pathlib import Path

from langchain_core.documents import Document

from src.exceptions import AppError


def parse_frontmatter(markdown_text: str) -> dict:
    """Parse simple YAML-style frontmatter from Markdown text."""
    if not markdown_text.startswith("---"):
        return {}
    parts = markdown_text.split("---", 2)
    if len(parts) < 3:
        return {}

    metadata: dict[str, str] = {}
    for line in parts[1].splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"')
    return metadata


def load_markdown_file(file_path: str) -> Document:
    """Load a Markdown file into a LangChain document with metadata."""
    try:
        text = Path(file_path).read_text(encoding="utf-8")
    except OSError as error:
        raise AppError("RAG_LOAD_FAILED", f"Failed to load {file_path}", error) from error

    metadata = parse_frontmatter(text)
    metadata["file_path"] = file_path
    return Document(page_content=text, metadata=metadata)


def load_markdown_documents(file_paths: list[str]) -> list[Document]:
    """Load multiple Markdown files into LangChain documents."""
    return [load_markdown_file(file_path) for file_path in file_paths]
