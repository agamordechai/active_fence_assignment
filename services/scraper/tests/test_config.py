"""Tests for configuration management"""
import pytest
import logging
from unittest.mock import patch, MagicMock
from pathlib import Path
import os

from src.config import Settings, LogLevel, RunMode, setup_logging


class TestLogLevelEnum:
    """Tests for LogLevel enum"""

    def test_log_levels_exist(self):
        """Test all expected log levels exist"""
        assert LogLevel.DEBUG == "DEBUG"
        assert LogLevel.INFO == "INFO"
        assert LogLevel.WARNING == "WARNING"
        assert LogLevel.ERROR == "ERROR"
        assert LogLevel.CRITICAL == "CRITICAL"


class TestRunModeEnum:
    """Tests for RunMode enum"""

    def test_run_modes_exist(self):
        """Test all expected run modes exist"""
        assert RunMode.SINGLE == "single"
        assert RunMode.SCHEDULER == "scheduler"
        assert RunMode.CONTINUOUS == "continuous"


class TestSettings:
    """Tests for Settings class"""

    def test_default_settings(self):
        """Test default settings values"""
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()

            assert settings.log_level == LogLevel.INFO
            assert settings.run_mode == RunMode.SINGLE
            assert settings.rate_limit_delay == 2.0
            assert settings.request_timeout == 10
            assert settings.posts_per_subreddit == 10
            assert settings.max_users_to_enrich == 20
            assert settings.user_history_days == 60
            assert settings.critical_risk_threshold == 70
            assert settings.high_risk_threshold == 50
            assert settings.medium_risk_threshold == 30
            assert settings.low_risk_threshold == 10
            assert settings.api_url == "http://localhost:8000"
            assert settings.api_timeout == 30

    def test_settings_from_env(self):
        """Test settings can be loaded from environment variables"""
        env_vars = {
            "LOG_LEVEL": "DEBUG",
            "RUN_MODE": "scheduler",
            "RATE_LIMIT_DELAY": "3.5",
            "POSTS_PER_SUBREDDIT": "50",
            "API_URL": "http://example.com:8080",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()

            assert settings.log_level == LogLevel.DEBUG
            assert settings.run_mode == RunMode.SCHEDULER
            assert settings.rate_limit_delay == 3.5
            assert settings.posts_per_subreddit == 50
            assert settings.api_url == "http://example.com:8080"

    def test_subreddits_list_property(self):
        """Test subreddits_list parses comma-separated string"""
        with patch.dict(os.environ, {"TARGET_SUBREDDITS": "sub1, sub2, sub3"}, clear=True):
            settings = Settings()
            # Clear cached property
            if hasattr(settings, "__dict__") and "subreddits_list" in settings.__dict__:
                del settings.__dict__["subreddits_list"]

            result = settings.subreddits_list
            assert result == ["sub1", "sub2", "sub3"]

    def test_search_terms_list_property(self):
        """Test search_terms_list parses comma-separated string"""
        with patch.dict(os.environ, {"SEARCH_TERMS": "term1, term2, term3"}, clear=True):
            settings = Settings()
            # Clear cached property
            if hasattr(settings, "__dict__") and "search_terms_list" in settings.__dict__:
                del settings.__dict__["search_terms_list"]

            result = settings.search_terms_list
            assert result == ["term1", "term2", "term3"]

    def test_get_log_level_int_debug(self):
        """Test get_log_level_int returns correct int for DEBUG"""
        with patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"}, clear=True):
            settings = Settings()
            assert settings.get_log_level_int() == logging.DEBUG

    def test_get_log_level_int_info(self):
        """Test get_log_level_int returns correct int for INFO"""
        with patch.dict(os.environ, {"LOG_LEVEL": "INFO"}, clear=True):
            settings = Settings()
            assert settings.get_log_level_int() == logging.INFO

    def test_get_log_level_int_warning(self):
        """Test get_log_level_int returns correct int for WARNING"""
        with patch.dict(os.environ, {"LOG_LEVEL": "WARNING"}, clear=True):
            settings = Settings()
            assert settings.get_log_level_int() == logging.WARNING

    def test_get_log_level_int_error(self):
        """Test get_log_level_int returns correct int for ERROR"""
        with patch.dict(os.environ, {"LOG_LEVEL": "ERROR"}, clear=True):
            settings = Settings()
            assert settings.get_log_level_int() == logging.ERROR

    def test_print_config(self, caplog):
        """Test print_config logs configuration"""
        settings = Settings()
        mock_logger = MagicMock()

        settings.print_config(mock_logger)

        # Verify logger.info was called multiple times
        assert mock_logger.info.call_count >= 5

    def test_settings_extra_ignored(self):
        """Test that extra env vars are ignored"""
        env_vars = {
            "SOME_UNKNOWN_VAR": "value",
            "ANOTHER_UNKNOWN": "123",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            # Should not raise error
            settings = Settings()
            assert settings is not None


class TestSetupLogging:
    """Tests for setup_logging function"""

    @patch("src.config.settings")
    def test_setup_logging_creates_logs_dir(self, mock_settings, tmp_path):
        """Test setup_logging creates logs directory"""
        mock_settings.get_log_level_int.return_value = logging.INFO
        mock_settings.log_level = LogLevel.INFO

        # Change to temp directory
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            logger = setup_logging()
            assert Path("logs").exists()
        finally:
            os.chdir(original_cwd)

    @patch("src.config.settings")
    def test_setup_logging_returns_logger(self, mock_settings, tmp_path):
        """Test setup_logging returns a logger"""
        mock_settings.get_log_level_int.return_value = logging.INFO
        mock_settings.log_level = LogLevel.INFO

        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            logger = setup_logging()
            assert isinstance(logger, logging.Logger)
        finally:
            os.chdir(original_cwd)


class TestRiskThresholds:
    """Tests for risk threshold configuration"""

    def test_default_thresholds_hierarchy(self):
        """Test default thresholds are in correct hierarchy"""
        settings = Settings()

        assert settings.low_risk_threshold < settings.medium_risk_threshold
        assert settings.medium_risk_threshold < settings.high_risk_threshold
        assert settings.high_risk_threshold < settings.critical_risk_threshold

    def test_custom_thresholds_from_env(self):
        """Test custom thresholds from environment"""
        env_vars = {
            "CRITICAL_RISK_THRESHOLD": "80",
            "HIGH_RISK_THRESHOLD": "60",
            "MEDIUM_RISK_THRESHOLD": "40",
            "LOW_RISK_THRESHOLD": "20",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()

            assert settings.critical_risk_threshold == 80
            assert settings.high_risk_threshold == 60
            assert settings.medium_risk_threshold == 40
            assert settings.low_risk_threshold == 20


class TestOutputSettings:
    """Tests for output settings"""

    def test_default_output_settings(self):
        """Test default output settings"""
        settings = Settings()

        assert settings.save_raw_data is True
        assert settings.save_processed_data is True
        assert settings.generate_reports is True
        assert settings.output_format == "json"

    def test_output_settings_from_env(self):
        """Test output settings from environment"""
        env_vars = {
            "SAVE_RAW_DATA": "false",
            "SAVE_PROCESSED_DATA": "false",
            "GENERATE_REPORTS": "false",
            "OUTPUT_FORMAT": "csv",
        }
        with patch.dict(os.environ, env_vars, clear=True):
            settings = Settings()

            assert settings.save_raw_data is False
            assert settings.save_processed_data is False
            assert settings.generate_reports is False
            assert settings.output_format == "csv"


class TestPerformanceSettings:
    """Tests for performance settings"""

    def test_default_performance_settings(self):
        """Test default performance settings"""
        settings = Settings()

        assert settings.max_concurrent_requests == 5
        assert settings.max_memory_mb == 2048
        assert settings.debug_mode is False
        assert settings.max_retries == 3
        assert settings.retry_delay == 5

    def test_content_filtering_settings(self):
        """Test content filtering settings"""
        settings = Settings()

        assert settings.min_post_length == 10
        assert settings.filter_bots is True
        assert settings.filter_deleted is True