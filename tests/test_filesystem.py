from src.collector.filesystem import (
    append_indexed_file,
    append_ingested_url,
    generate_unique_markdown_path,
    list_markdown_files,
    read_indexed_files,
    read_ingested_urls,
    save_text_file,
)


def test_read_ingested_urls_missing(tmp_path):
    assert read_ingested_urls(str(tmp_path / "missing.txt")) == set()


def test_read_ingested_urls_values(tmp_path):
    path = tmp_path / "urls.txt"
    path.write_text("https://a.com\nhttps://b.com\n", encoding="utf-8")
    assert read_ingested_urls(str(path)) == {"https://a.com", "https://b.com"}


def test_append_ingested_url(tmp_path):
    path = tmp_path / "urls.txt"
    append_ingested_url(str(path), "https://a.com")
    assert "https://a.com" in path.read_text(encoding="utf-8")


def test_read_indexed_files_missing(tmp_path):
    assert read_indexed_files(str(tmp_path / "missing.txt")) == set()


def test_append_indexed_file(tmp_path):
    path = tmp_path / "indexed.txt"
    append_indexed_file(str(path), "a.md")
    assert read_indexed_files(str(path)) == {"a.md"}


def test_generate_unique_markdown_path(tmp_path):
    first = generate_unique_markdown_path(str(tmp_path), "Hello AI")
    assert first.endswith("hello-ai.md")
    save_text_file(first, "x")
    second = generate_unique_markdown_path(str(tmp_path), "Hello AI")
    assert second.endswith("hello-ai-2.md")


def test_save_text_file_and_list_markdown_files(tmp_path):
    path = tmp_path / "nested" / "a.md"
    save_text_file(str(path), "hello")
    assert path.read_text(encoding="utf-8") == "hello"
    assert str(path) in list_markdown_files(str(tmp_path))
