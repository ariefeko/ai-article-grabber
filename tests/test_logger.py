from unittest.mock import Mock

from src.logger import setup_logger


def test_setup_logger_writes_to_log_file(tmp_path):
    log_file = tmp_path / "logs" / "app.log"
    config = Mock(log_level="INFO", log_file=str(log_file))

    logger = setup_logger(config)
    logger.info("hello", extra={"event": "test.event"})

    assert log_file.exists()
    log_text = log_file.read_text(encoding="utf-8")
    assert "hello" in log_text
    assert "test.event" in log_text
