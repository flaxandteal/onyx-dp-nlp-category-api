# https://til.codeinthehole.com/posts/how-to-get-gunicorn-to-log-as-json/

import datetime
import logging
import sys
import json_log_formatter
from category_api.settings import settings
import re

def format_stack_trace(stack_trace):
    # Split the stack trace into lines removing caret chars
    lines = "".join(stack_trace.split("\n")).replace("^", "")

    # Split by File as there's always 1 file per entry
    lines = lines.split("File")

    # Remove first entry as it's always Traceback(mostrecentcalllast)
    lines = lines[1:]

    # Initialize an empty list to store formatted stack trace entries
    formatted_stack_trace = []
    
    # Iterate through each line in the stack trace
    for line in lines:
        # split by "," to separate file_path, line_number, function_name
        line = line.split(",")
        file_path, line_number, function_name = line[0], line[1], line[2]

        # remove unnecessary spaces in function name
        function_name = re.sub(r'\s{2,}', ' ', function_name).rstrip()

        formatted_entry = {
            "file": file_path.strip("\""),
            "function": function_name,
            # remove unnecessary spaces in line
            "line": "".join(line_number.split("line")).strip(" "),
        }

        formatted_stack_trace.append(formatted_entry)

    return formatted_stack_trace

class SuppressInfoFilter(logging.Filter):
    def filter(self, record):
        return record.levelno != logging.INFO or record.name != "uvicorn.error"

class SuppressErrorFilter(logging.Filter):
    def filter(self, record):
        return record.levelno != logging.ERROR or record.name != "uvicorn.error"

class JsonRequestFormatter(json_log_formatter.JSONFormatter):
    def json_record(
        self,
        event: str,
        extra: dict[str, str | int | float],
        record: logging.LogRecord,
    ) -> dict[str, str | int | float]:
        
        # Convert the log record to a JSON object.
        # See https://docs.gunicorn.org/en/stable/settings.html#access-log-format
        started_at = datetime.datetime.now().isoformat(timespec="milliseconds") + "Z"
        # Extracting path and query from the log message
        path, query_string = record.args[2].split('?', 1) if '?' in record.args[2] else (record.args[2], '')

        return dict(
            namespace=settings.NAMESPACE,
            created_at=datetime.datetime.now().isoformat(timespec="milliseconds") + "Z",
            event="http request received",
            http={
                "method": record.args[1],
                "scheme": record.args[3],
                "path": path,
                **({'query': query_string} if query_string else {}),
                "status_code": str(record.args[4]),
                "started_at": started_at,
            },
            severity=3,
        )

class JsonErrorFormatter(json_log_formatter.JSONFormatter):
    def json_record(
        self,
        event: str,
        extra: dict[str, str | int | float],
        record: logging.LogRecord,
    ):

        return dict(
            namespace=settings.NAMESPACE,
            created_at=datetime.datetime.now().isoformat(timespec="milliseconds") + "Z",
            event=record.getMessage(),
            severity=3,
        )

class JsonServerInfoFormatter(json_log_formatter.JSONFormatter):
    def json_record(
        self,
        event: str,
        extra: dict[str, str | int | float],
        record: logging.LogRecord,
    ):

        return dict(
            namespace=settings.NAMESPACE,
            created_at=datetime.datetime.now().isoformat(timespec="milliseconds") + "Z",
            event=record.getMessage(),
            severity=3,
        )

class JsonServerErrorFormatter(json_log_formatter.JSONFormatter):
    def json_record(
        self,
        event: str,
        extra: dict[str, str | int | float],
        record: logging.LogRecord,
    ) -> dict[str, str | int | float]:
        errors=[
                {
                    **({'message': record.getMessage().strip().splitlines()[-1]} if "Traceback" in record.getMessage() else {"message": record.getMessage()}),
                    **({'error': format_stack_trace(record.getMessage())} if "Traceback" in record.getMessage() else {}),
                }
            ]

        return dict(
            namespace=settings.NAMESPACE,
            created_at=datetime.datetime.now().isoformat(timespec="milliseconds") + "Z",
            event="Uvicorn has experienced an error",
            severity=1,
            errors=errors
        )

class JsonServerErrorHandler(logging.StreamHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stream = sys.stderr
        self.setFormatter(JsonServerErrorFormatter())
        self.addFilter(SuppressInfoFilter())

class JsonServerInfoHandler(logging.StreamHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stream = sys.stdout
        self.setFormatter(JsonServerInfoFormatter())
        self.addFilter(SuppressErrorFilter())

# Ensure the two named loggers that Gunicorn uses are configured to use a custom
# JSON formatter.
logconfig_dict = {
    "version": 1,
    "formatters": {
        "json_server_error": {
            "()": JsonServerErrorFormatter,
        },
        "json_request": {
            "()": JsonRequestFormatter,
        },
        "json_server_info": {
            "()": JsonServerInfoFormatter,
        },
    },
    "handlers": {
        "json_server_error": {
            "class": "gunicorn_config.JsonServerErrorHandler",
            "stream": sys.stderr,
            "formatter": "json_server_error",
        },
        "json_request": {
            "class": "logging.StreamHandler",
            "stream": sys.stdout,
            "formatter": "json_request",
        },
        "json_server_info": {
            "class": "gunicorn_config.JsonServerInfoHandler",
            "stream": sys.stdout,
            "formatter": "json_server_info",
        },
    },
    "root": {"level": "INFO", "handlers": []},
    "loggers": {
        "uvicorn.access": {
            "level": "INFO",
            "handlers": ["json_request"],
            "propagate": False,
        },
        "uvicorn.error": {
            "level": "INFO",
            "handlers": ["json_server_info", "json_server_error"],
            "propagate": False,
        },
    },
}

bind = f"0.0.0.0:{settings.PORT}"
timeout = int(settings.TIMEOUT or 0)
