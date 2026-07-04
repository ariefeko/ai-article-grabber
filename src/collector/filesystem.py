from pathlib import Path

from slugify import slugify

from src.exceptions import AppError
from src.types import AppConfig


def ensure_directories(config: AppConfig) -> None:
    """Create output, state, and log directories required by the app."""
    for path in [
        config.output_dir,
        Path(config.ingested_urls_file).parent,
        Path(config.indexed_files_file).parent,
        Path(config.log_file).parent,
    ]:
        Path(path).mkdir(parents=True, exist_ok=True)


def _read_lines(file_path: str) -> set[str]:
    """Read non-empty stripped lines from a text file."""
    path = Path(file_path)
    if not path.exists():
        return set()
    try:
        return {line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}
    except OSError as error:
        raise AppError("FILE_READ_FAILED", f"Failed to read {file_path}", error) from error


def _append_line(file_path: str, value: str) -> None:
    """Append one line to a text file, creating its parent directory."""
    try:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as file:
            file.write(f"{value}\n")
    except OSError as error:
        raise AppError("FILE_WRITE_FAILED", f"Failed to write {file_path}", error) from error


def read_ingested_urls(file_path: str) -> set[str]:
    """Read the set of article URLs that have already been ingested."""
    return _read_lines(file_path)


def append_ingested_url(file_path: str, url: str) -> None:
    """Record an ingested article URL in the state file."""
    _append_line(file_path, url)


def read_indexed_files(file_path: str) -> set[str]:
    """Read the set of Markdown files that have already been indexed."""
    return _read_lines(file_path)


def append_indexed_file(file_path: str, markdown_file_path: str) -> None:
    """Record an indexed Markdown file path in the state file."""
    _append_line(file_path, markdown_file_path)


def get_output_directory(output_dir: str, date_folder: str) -> str:
    """Return and create the dated output directory for saved articles."""
    path = Path(output_dir) / date_folder
    path.mkdir(parents=True, exist_ok=True)
    return str(path)


def generate_unique_markdown_path(output_directory: str, title: str) -> str:
    """Generate an unused Markdown file path based on an article title."""
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
    """Save text content to a UTF-8 file."""
    try:
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    except OSError as error:
        raise AppError("MARKDOWN_SAVE_FAILED", f"Failed to save {file_path}", error) from error


def list_markdown_files(output_dir: str) -> list[str]:
    """List all Markdown files under an output directory."""
    path = Path(output_dir)
    if not path.exists():
        return []
    return sorted(str(file_path) for file_path in path.rglob("*.md") if file_path.is_file())
