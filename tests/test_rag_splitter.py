from langchain_core.documents import Document

from src.rag.splitter import split_documents


def test_split_documents_chunks_metadata_size():
    document = Document(page_content="AI " * 200, metadata={"source_url": "https://example.com"})
    chunks = split_documents([document], chunk_size=80, chunk_overlap=10)
    assert chunks
    assert chunks[0].metadata["source_url"] == "https://example.com"
    assert all(len(chunk.page_content) <= 100 for chunk in chunks)
