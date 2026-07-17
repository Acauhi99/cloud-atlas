import logging
import sys
import uuid
from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar("request_id", default="")


def setup_logging(log_level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)s | %(request_id)s | "
            "%(method)s %(path)s | %(status_code)s | %(duration_ms)sms | %(message)s"
        )
    )
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO), handlers=[handler]
    )


def generate_request_id() -> str:
    return str(uuid.uuid4())
