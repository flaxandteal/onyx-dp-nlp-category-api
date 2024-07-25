import logging
import logging.config

import structlog
import structlog._log_levels

from category_api.settings import settings
from gunicorn_config import format_stack_trace

severity_info = 3
severity_warning = 2
severity_error = 1
severity_fatal = 0


def level_to_severity(level):
    level_int = logging.getLevelName(level.upper())
    match level_int:
        case logging.INFO:
            return severity_info
        case logging.WARNING:
            return severity_warning
        case logging.ERROR:
            return severity_error
        case logging.FATAL:
            return severity_fatal
        case _:
            return severity_info


def add_severity_level(logger, method_name, event_dict):
    event_dict[0][0]["severity"] = level_to_severity(event_dict[0][0]["level"])
    del event_dict[0][0]["level"]
    return event_dict


def remove_microseconds(logger, method_name, event_dict):
    event_dict[0][0]["created_at"] = event_dict[0][0]["created_at"][:-3] + "Z"
    return event_dict


def format_errors(*excs: BaseException, trace=None):
    errors = []

    for exc in excs:
        error = {
            "message": str(exc),
        }
        if trace:
            error["error"] = format_stack_trace(trace)

        errors.append(error)

    return errors


def setup_logging():
    shared_processors = []
    processors = shared_processors + [
        structlog.processors.TimeStamper(
            fmt="%Y-%m-%dT%H:%M:%S.%f", utc=False, key="created_at"
        ),
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        add_severity_level,
        remove_microseconds,
    ]
    structlog.configure(
        cache_logger_on_first_use=True,
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
    )

    stdlib_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processor": structlog.processors.JSONRenderer(),
                "foreign_pre_chain": shared_processors,
            },
        },
        "handlers": {
            "stream": {
                "level": "DEBUG",
                "formatter": "json",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stderr",
            },
        },
        "loggers": {
            "category_api": {
                "handlers": ["stream"],
                "level": "DEBUG",
                "propagate": True,
            },
        },
    }
    logging.config.dictConfig(stdlib_config)

    return structlog.get_logger(
        namespace=settings.NAMESPACE,
        event="",
        severity=3,  # default
    )


logger = setup_logging()
