import logging
from pathlib import Path

from pythonjsonlogger.json import JsonFormatter

from src.types import AppConfig


class AppJsonFormatter(JsonFormatter):
    """JSON formatter that emits the compact application log schema."""
    def add_fields(self, log_record, record, message_dict):
        """Keep application logs focused on time, message, and event fields."""
        super().add_fields(log_record, record, message_dict)

        log_record["time"] = log_record.pop("asctime", None)
        log_record["message"] = record.getMessage()
        log_record["event"] = getattr(record, "event", None)

        for key in list(log_record.keys()):
            if key not in {"time", "message", "event"}:
                log_record.pop(key, None)


def setup_logger(config: AppConfig) -> logging.Logger:
    """Configure the application logger with JSON console and file handlers."""
    logger = logging.getLogger("ai_article_grabber")
    logger.setLevel(config.log_level.upper())
    logger.handlers.clear()

    formatter = AppJsonFormatter("%(asctime)s %(message)s %(event)s")

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    log_path = Path(config.log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)

    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)
    logger.propagate = False
    return logger
