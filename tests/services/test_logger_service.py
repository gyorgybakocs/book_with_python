import pytest
import logging
import os
from unittest.mock import MagicMock, patch
from src.services.logger_service import LoggerService

@pytest.fixture
def mock_config():
    """
    Creates a mock config object that simulates the ConfigService.
    This provides predictable config values for tests.
    """
    config = MagicMock()
    config_values = {
        "logger.log_format": "%(message)s",
        "paths.log_dir": "/tmp/test_logs",
        "logger.process_log": "process.log",
        "logger.error_log": "error.log"
    }
    config.get.side_effect = lambda key, fallback=None: config_values.get(key, fallback)
    return config

@pytest.fixture(autouse=True)
def cleanup_singleton_and_handlers():
    """
    This fixture automatically runs before and after each test.
    It ensures that the singleton instances and logging handlers are reset,
    so tests do not interfere with each other.
    """
    yield
    LoggerService._instance = None
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

@pytest.fixture
def mock_logging_handlers(mocker):
    """
    A dedicated fixture to mock both FileHandler and StreamHandler.
    It configures the mock instances to have the required '.level' attribute.
    """
    mock_file_handler_class = mocker.patch("logging.FileHandler")
    mock_file_handler_class.return_value.level = logging.NOTSET # Set the required attribute
    mock_stream_handler_class = mocker.patch("logging.StreamHandler")
    mock_stream_handler_class.return_value.level = logging.NOTSET # Set the required attribute

    return mock_file_handler_class, mock_stream_handler_class

def test_initialize_from_config_full(mock_config, mock_logging_handlers):
    """
    Tests that initialize_from_config correctly sets up all handlers
    when a full configuration is provided.
    """
    mock_file_handler, mock_stream_handler = mock_logging_handlers

    with patch("os.makedirs") as mocker_makedirs:
        service = LoggerService.get_instance()
        service.initialize_from_config(mock_config)

        mocker_makedirs.assert_called_once_with("/tmp/test_logs", exist_ok=True)

        assert mock_file_handler.call_count == 2
        assert mock_stream_handler.call_count == 1

def test_initialize_from_config_minimal(mock_logging_handlers):
    """
    Tests that only the console handler is set up if file paths are missing.
    """
    mock_file_handler, mock_stream_handler = mock_logging_handlers

    minimal_config = MagicMock()
    minimal_config.get.return_value = None

    with patch("os.makedirs") as mocker_makedirs:
        service = LoggerService.get_instance()
        service.initialize_from_config(minimal_config)

        mocker_makedirs.assert_not_called()
        mock_file_handler.assert_not_called()

        mock_stream_handler.assert_called_once()

def test_get_instance_returns_singleton():
    """
    Tests that get_instance() always returns the same object instance.
    """
    instance1 = LoggerService.get_instance()
    instance2 = LoggerService.get_instance()
    assert instance1 is instance2
