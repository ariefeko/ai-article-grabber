from pathlib import Path

from langchain_core.documents import Document

from src.rag.loader import load_markdown_file, parse_frontmatter

FIXTURE = Path(__file__).parent / "fixtures" / "sample_article.md"


def test_parse_frontmatter_extracts_values():
    metadata = parse_frontmatter(FIXTURE.read_text(encoding="utf-8"))
    assert metadata["title"] == "Sample AI Article"
    assert metadata["source_url"] == "https://example.com/sample-ai-article"


def test_load_markdown_file_document():
    document = load_markdown_file(str(FIXTURE))
    assert isinstance(document, Document)
    assert document.metadata["file_path"] == str(FIXTURE)
    assert "retrieval augmented generation" in document.page_content
