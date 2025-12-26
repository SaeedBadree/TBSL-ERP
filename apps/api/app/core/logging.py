import logging
import logging.config


def setup_logging(level: str = "INFO") -> None:
    """Configure basic structured logging for the service."""
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s [%(levelname)s] %(name)s - %(message)s",
            },
            "access": {
                "format": '%(asctime)s [%(levelname)s] %(name)s - "%(message)s"',
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
            },
        },
        "loggers": {
            "uvicorn": {"handlers": ["console"], "level": level, "propagate": False},
            "uvicorn.error": {"handlers": ["console"], "level": level, "propagate": False},
            "uvicorn.access": {"handlers": ["console"], "level": level, "propagate": False},
            "": {"handlers": ["console"], "level": level},
        },
    }

    logging.config.dictConfig(logging_config)


