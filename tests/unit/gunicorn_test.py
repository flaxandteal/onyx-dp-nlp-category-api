import logging.config
import unittest

from datetime import datetime
from io import StringIO
from unittest.mock import patch
from gunicorn_config import (JsonRequestFormatter, JsonServerErrorFormatter,
                             JsonServerInfoFormatter, logconfig_dict)

e = """
Traceback (most recent call last):
File "/home/kamen/dev/work/github/onyx/onyx-dp-nlp-category-api/.venv/lib/python3.12/site-packages/starlette/routing.py", line 677, in lifespan
    async with self.lifespan_context(app) as maybe_state:
File "/usr/lib64/python3.12/contextlib.py", line 210, in __aenter__
    return await anext(self.gen)
        ^^^^^^^^^^^^^^^^^^^^^
File "/home/kamen/dev/work/github/onyx/onyx-dp-nlp-category-api/category_api/server.py", line 39, in lifespan
    with retrieve(app.settings, app.settings_bonn) as (settings, settings_bonn):
File "/usr/lib64/python3.12/contextlib.py", line 137, in __enter__
    return next(self.gen)
        ^^^^^^^^^^^^^^
File "/home/kamen/dev/work/github/onyx/onyx-dp-nlp-category-api/category_api/data.py", line 51, in retrieve
    raise ValueError("This is a custom error message")
ValueError: This is a custom error message
"""

class TestLogFormatting(unittest.TestCase):
    def setUp(self):
        logging.config.dictConfig(logconfig_dict)

    def test_request_formatting(self):
        record = logging.LogRecord(
            name="uvicorn.access",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Log message",
            args=[
                "", "GET", "/path/to/resource?search=query", "1.1", "200"
            ],
            exc_info="",
        )

        stream_buffer = StringIO()

        with patch("sys.stdout", stream_buffer):
            formatter = JsonRequestFormatter()
            formatted_log = formatter.json_record(event="testing request logs", extra={}, record=record)

            expected={
                'namespace': 'dp-nlp-category-api', 
                'event': 'http request received', 
                'http': {
                    'method': 'GET', 
                    'scheme': '1.1', 
                    'path': '/path/to/resource',
                    'query': 'search=query', 
                    'status_code': '200',
                }, 
                'severity': 3
            }

            # Default required logs 
            self.assertEqual(expected["namespace"], formatted_log["namespace"])
            self.assertEqual(expected["event"], formatted_log["event"])
            self.assertEqual(expected["severity"], formatted_log["severity"])

            # Http logs 
            self.assertEqual(expected["http"]["method"], formatted_log["http"]["method"])
            self.assertEqual(expected["http"]["scheme"], formatted_log["http"]["scheme"])
            self.assertEqual(expected["http"]["path"], formatted_log["http"]["path"])
            self.assertEqual(expected["http"]["query"], formatted_log["http"]["query"])
            self.assertTrue(parsable_isoformat(time=formatted_log["http"]["started_at"]))
            self.assertTrue(parsable_isoformat(formatted_log["created_at"]))

    def test_server_log_formatting(self):
        record = logging.LogRecord(
            name="uvicorn.error",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="server starting",
            args=[],
            exc_info="",
        )

        stream_buffer = StringIO()

        with patch("sys.stdout", stream_buffer):
            formatter = JsonServerInfoFormatter()
            formatted_log = formatter.json_record(event="testing server logs", extra={}, record=record)

            expected={
                'namespace': 'dp-nlp-category-api', 
                'event': 'server starting', 
                'severity': 3
            }

            self.assertEqual(expected["namespace"], formatted_log["namespace"])
            self.assertEqual(expected["event"], formatted_log["event"])
            self.assertEqual(expected["severity"], formatted_log["severity"])
            self.assertTrue(parsable_isoformat(formatted_log["created_at"]))

    def test_server_error_formatting(self):
        record = logging.LogRecord(
            name="uvicorn.error",
            level=logging.ERROR,
            pathname="",
            lineno=0,
            msg=e,
            args=[],
            exc_info=None,
        )

        stream_buffer = StringIO()

        with patch("sys.stderr", stream_buffer):
            formatter = JsonServerErrorFormatter()
            formatted_log = formatter.json_record(event="", extra={}, record=record)

            expected={
                'namespace': 'dp-nlp-category-api', 
                'event': 'Uvicorn has experienced an error',
                'errors': [
                    {
                        "message": 'ValueError: This is a custom error message',
                    }
                ],
                'severity': 1
            }

            # Default required logs 
            self.assertEqual(expected["namespace"], formatted_log["namespace"])
            self.assertEqual(expected["event"], formatted_log["event"])
            self.assertEqual(expected["severity"], formatted_log["severity"])

            # Error logs 
            self.assertEqual(expected["errors"][0]["message"], formatted_log["errors"][0]["message"])
            assert "routing.py" in formatted_log["errors"][0]["error"][0]["file"]
            assert "self.lifespan_context(app) as maybe_state:" in formatted_log["errors"][0]["error"][0]["function"]
            assert formatted_log["errors"][0]["error"][0]["line"]
            assert parsable_isoformat(formatted_log["created_at"])
            
def parsable_isoformat(time):
    desired_format = "%Y-%m-%dT%H:%M:%S.%fZ"
    try:
        _ = datetime.strptime(time, desired_format)
        return True  # If parsing succeeds, the format is correct
    except ValueError:
        return False, "Invalid format"

if __name__ == "__main__":
    unittest.main()
