"""Tests for logging configuration."""

import pytest
from loguru import logger
from unittest.mock import patch
from app.core.logging_config import setup_logging, get_logger


class TestLoggingConfiguration:
    """Test logging configuration setup."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures."""
        # Reset logger before each test
        logger.remove()
        yield
        logger.remove()

    def test_setup_logging_basic(self):
        """Test that setup_logging configures logger without errors."""
        # Should not raise any exceptions
        setup_logging()

        # Verify logger is configured
        logger.info("Test message")

    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a logger instance."""
        setup_logging()

        test_logger = get_logger("test_module")

        assert test_logger is not None
        # Should be able to log messages
        test_logger.info("Test message")

    def test_get_logger_with_default_name(self):
        """Test get_logger with default name."""
        setup_logging()

        test_logger = get_logger("default")

        assert test_logger is not None
        test_logger.info("Test message")

    def test_logging_with_exception(self):
        """Test logging with exception information."""
        setup_logging()

        try:
            raise ValueError("Test exception")
        except Exception:
            logger.exception("An error occurred")

    def test_multiple_log_calls(self):
        """Test multiple log calls at different levels."""
        setup_logging()

        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")

    def test_log_with_context_binding(self):
        """Test logging with bound context."""
        setup_logging()

        bound_logger = logger.bind(user_id="123", action="test")
        bound_logger.info("Action performed")

    def test_setup_logging_with_env_settings(self):
        """Test that setup_logging uses settings from config."""
        # Mock settings with custom values
        with patch('app.core.logging_config.settings') as mock_settings:
            mock_settings.LOG_LEVEL = "DEBUG"

            setup_logging()

            # Should use mocked settings
            logger.info("Test with mocked settings")


class TestLoggingIntegration:
    """Integration tests for logging in application context."""

    def test_logger_available_in_app_context(self):
        """Test that logger is available and working."""
        from app.core.logging_config import get_logger

        test_logger = get_logger("integration_test")
        test_logger.info("Integration test message")

    def test_logger_with_special_characters(self):
        """Test logging messages with special characters."""
        setup_logging()

        logger.info("Message with special chars: @#$%^&*()")
        logger.info("Message with unicode: 你好世界")
        logger.info("Message with emojis: 🚀 🎉 ✅")

    def test_logger_performance_with_many_messages(self):
        """Test logging performance with many messages."""
        setup_logging()

        import time
        start = time.time()

        for i in range(100):
            logger.info(f"Message {i}")

        elapsed = time.time() - start

        # Should complete 100 logs in reasonable time (< 5 seconds)
        assert elapsed < 5.0
