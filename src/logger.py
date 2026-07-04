import logging

from pythonjsonlogger import jsonlogger

from src.types import AppConfig


class AppJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)

        log_record["time"] = log_record.pop("asctime", None)
        log_record["message"] = record.getMessage()
        log_record["event"] = getattr(record, "event", None)

        for key in list(log_record.keys()):
            if key not in {"time", "message", "event"}:
                log_record.pop(key, None)


def setup_logger(config: AppConfig) -> logging.Logger:
    logger = logging.getLogger("ai_article_grabber")
    logger.setLevel(config.log_level.upper())
    logger.handlers.clear()

    handler = logging.StreamHandler()
    handler.setFormatter(AppJsonFormatter("%(asctime)s %(message)s %(event)s"))

    logger.addHandler(handler)
    logger.propagate = False
    return logger
