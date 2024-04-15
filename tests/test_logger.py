"""Tests for the agatha.logger module."""

import logging
import operator
import sys
from logging import Logger, StreamHandler
from typing import List, Tuple
from unittest.mock import Mock, patch

import pytest

from agatha.util.config import Config
from agatha.util.logger import MaxLevelFilter, setup_logger


@pytest.fixture
def logger_and_emit_mock() -> Tuple[Logger, Mock]:
    """Logger and  mock being called on emit of logger."""
    result = Logger(__name__)
    emit_mock = Mock()

    class MockEmitHandler(StreamHandler):
        """StreamHandler with `emit` replaced by `emit_mock`."""

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.emit = emit_mock

    result.addHandler(MockEmitHandler())
    return result, emit_mock


def test_max_level_filter(logger_and_emit_mock: Tuple[Logger, Mock]):
    """Test MaxLevelFilter."""
    logger, emit_mock = logger_and_emit_mock
    logger.setLevel(logging.INFO)
    logger.addFilter(MaxLevelFilter(logging.ERROR))
    logger.info("")
    emit_mock.assert_called()
    logger.warning("")
    assert emit_mock.call_count == 2
    logger.error("")
    logger.critical("")
    assert emit_mock.call_count == 2


def test_max_level_filter_max_edge(logger_and_emit_mock: Tuple[Logger, Mock]):
    """Test the top edge case for MaxLevelFilter."""
    logger, emit_mock = logger_and_emit_mock
    logger.addFilter(MaxLevelFilter(logging.CRITICAL))
    logger.setLevel(logging.WARNING)
    logger.warning("")
    logger.error("")
    assert emit_mock.call_count == 2
    logger.critical("")
    assert emit_mock.call_count == 2


def test_max_level_filter_min_edge(logger_and_emit_mock: Tuple[Logger, Mock]):
    """Test the bottom edge case for MaxLevelFilter."""
    logger, emit_mock = logger_and_emit_mock
    logger.addFilter(MaxLevelFilter(logging.NOTSET))
    logger.setLevel(logging.NOTSET)
    logger.debug("")
    logger.info("")
    logger.warning("")
    logger.error("")
    logger.critical("")
    emit_mock.assert_not_called()


def logger_writes_to(
    target_stream_name: str, logger: Logger, log_function_name: str
) -> bool:
    """Check if `logger` writes to `target_stream` for `log_function_name` log level.

    Args:
        target_stream_name (str): Stream for which to test if logger logs to.
        logger (Logger): Logger instance.
        log_function_name (str): Function name of the log level (e.g. "info").

    Returns:
        bool: True if `logger` logs to `target_stream` for `log_function_name` level
    """
    with patch(f"{target_stream_name}.write") as stream_mock:
        operator.methodcaller(log_function_name.lower(), msg="")(logger)
        return stream_mock.call_count >= 1


def test_logger_writes_to():
    """Test `logger_writes_to`."""
    logger = logging.Logger("")
    logger.setLevel(logging.WARNING)
    logger.addHandler(StreamHandler(sys.stderr))
    assert logger_writes_to("sys.stderr", logger, "error")
    assert not logger_writes_to("sys.stderr", logger, "info")


def assert_exclusive_logging(
    logger, not_logged: List[str], logged_to_out: List[str], logged_to_err: List[str]
):
    """Assert that the given log levels were exclusively logged to the respective outputs.

    Args:
        logger: Logger which to test.
        not_logged (list[str]): Log level strings which should not be logged.
        logged_to_out (list[str]): Log level strings which should only be logged to sys.stdout.
        logged_to_err (list[str]): Log level strings which should only be logged to sys.stderr.
    """
    log_levels = set(not_logged + logged_to_out + logged_to_err)

    for log_level in log_levels - set(logged_to_out):
        assert not logger_writes_to("sys.stdout", logger, log_level)
    for log_level in log_levels - set(logged_to_err):
        assert not logger_writes_to("sys.stderr", logger, log_level)

    for log_level in logged_to_out:
        assert logger_writes_to("sys.stdout", logger, log_level)
    for log_level in logged_to_err:
        assert logger_writes_to("sys.stderr", logger, log_level)


def test_setup_logger_dev():
    """Test setup_logger in development mode."""
    with patch.dict(Config.conf, {"development_mode": True}):
        setup_logger()
        logger = logging.getLogger(__name__)
        assert_exclusive_logging(
            logger,
            not_logged=[],
            logged_to_out=["debug", "info"],
            logged_to_err=["warning", "error", "critical"],
        )


def test_setup_logger_not_dev():
    """Test setup_logger in non-development mode."""
    with patch.dict(Config.conf, {"development_mode": False}):
        setup_logger()
        logger = logging.getLogger(__name__)
        assert_exclusive_logging(
            logger,
            not_logged=["debug"],
            logged_to_out=["info"],
            logged_to_err=["warning", "error", "critical"],
        )
