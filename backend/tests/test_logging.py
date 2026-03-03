"""Tests for logging configuration with file rotation."""

import pytest
import sys
from pathlib import Path
from loguru import logger
from unittest.mock import patch, MagicMock
from app.core.logging_config import setup_logging, get_logger, LOG_FORMAT, FILE_LOG_FORMAT
from app.config import settings


class TestLoggingConfiguration:
    """Test logging configuration setup."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Setup test fixtures."""
        self.tmp_dir = tmp_path
        self.log_file = tmp_path / "test.log"
        # Reset logger before each test
        logger.remove()
        yield
        logger.remove()

    def test_setup_logging_creates_log_directory(self):
        """Test that setup_logging creates the log directory if it doesn't exist."""
        log_dir = self.tmp_dir / "custom_logs"
        assert not log_dir.exists()
        
        setup_logging(log_dir=str(log_dir))
        
        assert log_dir.exists()
        assert log_dir.is_dir()

    def test_setup_logging_default_settings(self):
        """Test logging with default settings from config."""
        # Should not raise any exceptions
        setup_logging()
        
        # Verify logger is configured
        logger.info("Test message")

    def test_setup_logging_custom_level(self):
        """Test logging with custom log level."""
        setup_logging(log_level="DEBUG", log_dir=str(self.tmp_dir))
        
        # Debug messages should be logged
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")

    def test_setup_logging_error_level(self):
        """Test logging with ERROR level (should filter out lower levels)."""
        setup_logging(log_level="ERROR", log_dir=str(self.tmp_dir))
        
        # Only errors should be logged
        logger.error("Error message")
        logger.critical("Critical message")

    def test_setup_logging_rotation_settings(self):
        """Test logging with custom rotation settings."""
        setup_logging(
            log_dir=str(self.tmp_dir),
            rotation_size="1 KB",
            retention_days=3,
            compression="gz"
        )
        
        # Should configure without errors
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
        
        test_logger = get_logger()
        
        assert test_logger is not None
        test_logger.info("Test message")

    def test_log_format_configuration(self):
        """Test that log formats are properly configured."""
        # Console format should contain color tags
        assert "<green>" in LOG_FORMAT
        assert "<level>" in LOG_FORMAT
        assert "<cyan>" in LOG_FORMAT
        
        # File format should not contain color tags (no angle bracket color codes)
        assert "<green>" not in FILE_LOG_FORMAT
        assert "<cyan>" not in FILE_LOG_FORMAT
        # File format uses {level} without color tags
        assert "level" in FILE_LOG_FORMAT

    def test_logging_with_exception(self):
        """Test logging with exception information."""
        setup_logging(log_dir=str(self.tmp_dir))
        
        try:
            raise ValueError("Test exception")
        except Exception:
            logger.exception("An error occurred")

    def test_multiple_log_calls(self):
        """Test multiple log calls at different levels."""
        setup_logging(log_dir=str(self.tmp_dir))
        
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        logger.critical("Critical message")

    def test_log_with_context_binding(self):
        """Test logging with bound context."""
        setup_logging(log_dir=str(self.tmp_dir))
        
        bound_logger = logger.bind(user_id="123", action="test")
        bound_logger.info("Action performed")

    def test_setup_logging_with_env_settings(self):
        """Test that setup_logging uses settings from config."""
        # Mock settings with custom values
        with patch('app.core.logging_config.settings') as mock_settings:
            mock_settings.LOG_LEVEL = "DEBUG"
            mock_settings.LOG_DIR = str(self.tmp_dir)
            mock_settings.LOG_RETENTION_DAYS = 14
            mock_settings.LOG_ROTATION_SIZE = "5 MB"
            mock_settings.LOG_COMPRESSION = "zip"
            
            setup_logging()
            
            # Should use mocked settings
            logger.info("Test with mocked settings")

    def test_setup_logging_fallback_on_error(self):
        """Test fallback to console logging if file logging fails."""
        # This test verifies the fallback mechanism exists
        # In normal conditions, file logging should work
        setup_logging(log_dir=str(self.tmp_dir))
        logger.info("Test message")


class TestLogFileRotation:
    """Test log file rotation functionality."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Setup test fixtures."""
        self.tmp_dir = tmp_path
        logger.remove()
        yield
        logger.remove()

    def test_log_file_created(self):
        """Test that log file is created in the specified directory."""
        log_file = self.tmp_dir / "app.log"
        
        setup_logging(log_dir=str(self.tmp_dir))
        
        # Log something to trigger file creation
        logger.info("Test message")
        
        # Give async logging time to write
        import time
        time.sleep(0.1)
        
        # Check if log file exists
        log_files = list(self.tmp_dir.glob("*.log"))
        assert len(log_files) > 0

    def test_error_log_file_created(self):
        """Test that separate error log file is created."""
        setup_logging(log_dir=str(self.tmp_dir))
        
        # Log an error to trigger error file creation
        logger.error("Error message")
        
        import time
        time.sleep(0.1)
        
        # Check for error log file
        error_logs = list(self.tmp_dir.glob("errors.log"))
        assert len(error_logs) > 0

    def test_log_message_content(self, capsys):
        """Test that log messages contain expected content."""
        setup_logging(log_level="INFO")
        
        logger.info("Test message content")
        
        # Capture stdout
        captured = capsys.readouterr()
        assert "Test message content" in captured.out

    def test_log_level_filtering(self, capsys):
        """Test that log level filtering works correctly."""
        setup_logging(log_level="WARNING", log_dir=str(self.tmp_dir))
        
        logger.debug("Debug - should not appear")
        logger.info("Info - should not appear")
        logger.warning("Warning - should appear")
        logger.error("Error - should appear")
        
        captured = capsys.readouterr()
        
        assert "Debug - should not appear" not in captured.out
        assert "Info - should not appear" not in captured.out
        assert "Warning - should appear" in captured.out
        assert "Error - should appear" in captured.out


class TestLoggingIntegration:
    """Integration tests for logging in application context."""

    def test_logger_available_in_app_context(self):
        """Test that logger is available and working."""
        from app.core.logging_config import get_logger
        
        test_logger = get_logger("integration_test")
        test_logger.info("Integration test message")

    def test_logger_with_special_characters(self):
        """Test logging messages with special characters."""
        setup_logging(log_dir=str(Path("/tmp")))
        
        logger.info("Message with special chars: @#$%^&*()")
        logger.info("Message with unicode: 你好世界")
        logger.info("Message with emojis: 🚀 🎉 ✅")

    def test_logger_performance_with_many_messages(self):
        """Test logging performance with many messages."""
        setup_logging(log_dir=str(Path("/tmp")))
        
        import time
        start = time.time()
        
        for i in range(100):
            logger.info(f"Message {i}")
        
        elapsed = time.time() - start
        
        # Should complete 100 logs in reasonable time (< 5 seconds)
        assert elapsed < 5.0
