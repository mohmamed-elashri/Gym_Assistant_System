"""Structured logging and non-leaky error handling."""

import json
import logging

from django.conf import settings

from fitness_api.views import custom_exception_handler
from gym_config.logging_utils import JsonFormatter


def test_json_formatter_emits_valid_json_with_exception():
    try:
        raise ValueError("boom")
    except ValueError:
        import sys

        record = logging.LogRecord(
            "x", logging.ERROR, __file__, 1, "failed %s", ("op",), sys.exc_info()
        )
    data = json.loads(JsonFormatter().format(record))
    assert data["level"] == "ERROR"
    assert data["message"] == "failed op"
    assert "ValueError" in data["exception"]


def test_logging_configured_for_json_console():
    assert settings.LOGGING["formatters"]["json"]["()"].endswith("JsonFormatter")


def test_unhandled_exception_does_not_leak_details(caplog):
    secret = "db password is hunter2"
    with caplog.at_level(logging.ERROR):
        response = custom_exception_handler(RuntimeError(secret), {"view": object()})
    assert response.status_code == 500
    assert secret not in response.content.decode()
    assert any("Unhandled API exception" in r.message for r in caplog.records)
