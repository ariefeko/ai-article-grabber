import logging

from pythonjsonlogger import jsonlogger

from src.types import AppConfig


def setup_logger(config: AppConfig) -> logging.Logger:
    logger = logging.getLogger("ai_article_grabber")
    logger.setLevel(config.log_level.upper())
    logger.handlers.clear()

    handler = logging.StreamHandler()
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s "
        "%(event)s %(url)s %(count)s %(file_path)s "
        "%(error_code)s %(error_message)s"
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.propagate = False
    return logger
