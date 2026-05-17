import logging
import re
import sys

from loguru import logger

from app.config import Settings
from app.utils.correlation import get_correlation_id

_BEARER_RE = re.compile(r"Bearer\s+[A-Za-z0-9_\-\.=]+")
_JWT_RE = re.compile(r"eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+")
_SENSITIVE_KEYS = frozenset(
    {"password", "refresh_token", "access_token", "token", "secret", "api_key"}
)


def _redact(value: str) -> str:
    return _JWT_RE.sub("***JWT***", _BEARER_RE.sub("Bearer ***", value))


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
    msg = record.get("message")
    if isinstance(msg, str):
        record["message"] = _redact(msg)
    for key in list(record["extra"].keys()):
        if key in _SENSITIVE_KEYS:
            record["extra"][key] = "***"
        elif isinstance(record["extra"][key], str):
            record["extra"][key] = _redact(record["extra"][key])


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
