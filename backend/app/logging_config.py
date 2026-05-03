import logging
import sys

from loguru import logger

from app.config import Settings
from app.utils.correlation import get_correlation_id


class _InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            level: str | int = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back  # type: ignore[assignment]
            depth += 1
        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def _patch_record(record):  # type: ignore[no-untyped-def]
    record["extra"]["correlation_id"] = get_correlation_id()


def configure_logging(settings: Settings) -> None:
    logger.remove()
    serialize = settings.environment != "development"
    logger.configure(patcher=_patch_record)
    logger.add(
        sys.stdout,
        level=settings.log_level,
        serialize=serialize,
        backtrace=settings.debug,
        diagnose=settings.debug,
        enqueue=False,
    )

    logging.basicConfig(handlers=[_InterceptHandler()], level=0, force=True)
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "celery", "sqlalchemy.engine"):
        logging.getLogger(name).handlers = [_InterceptHandler()]
        logging.getLogger(name).propagate = False
