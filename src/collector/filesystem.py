from pathlib import Path

from slugify import slugify

from src.exceptions import AppError
from src.types import AppConfig


def ensure_directories(config: AppConfig) -> None:
    for path in [
        config.output_dir,
        Path(config.ingested_urls_file).parent,
        Path(config.indexed_files_file).parent,
        Path(config.log_file).parent,
    ]:
        Path(path).mkdir(parents=True, exist_ok=True)


def _read_lines(file_path: str) -> set[str]:
    path = Path(file_path)
    if not path.exists():
        return set()
    try:
        return {line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}
    except OSError as error:
        raise AppError("FILE_READ_FAILED", f"Failed to read {file_path}", error) from error


def _append_line(file_path: str, value: str) -> None:
    try:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as file:
            file.write(f"{value}\n")
    except OSError as error:
        raise AppError("FILE_WRITE_FAILED", f"Failed to write {file_path}", error) from error


def read_ingested_urls(file_path: str) -> set[str]:
    return _read_lines(file_path)


def append_ingested_url(file_path: str, url: str) -> None:
    _append_line(file_path, url)


def read_indexed_files(file_path: str) -> set[str]:
    return _read_lines(file_path)


def append_indexed_file(file_path: str, markdown_file_path: str) -> None:
    _append_line(file_path, markdown_file_path)


def get_output_directory(output_dir: str, date_folder: str) -> str:
    path = Path(output_dir) / date_folder
    path.mkdir(parents=True, exist_ok=True)
    return str(path)


def generate_unique_markdown_path(output_directory: str, title: str) -> str:
    directory = Path(output_directory)
    directory.mkdir(parents=True, exist_ok=True)
    base_slug = slugify(title) or "untitled-article"
    candidate = directory / f"{base_slug}.md"
    counter = 2
    while candidate.exists():
        candidate = directory / f"{base_slug}-{counter}.md"
        counter += 1
    return str(candidate)


def save_text_file(file_path: str, content: str) -> None:
    try:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    except OSError as error:
        raise AppError("MARKDOWN_SAVE_FAILED", f"Failed to save {file_path}", error) from error


def list_markdown_files(output_dir: str) -> list[str]:
    path = Path(output_dir)
    if not path.exists():
        return []
    return sorted(str(file_path) for file_path in path.rglob("*.md") if file_path.is_file())
