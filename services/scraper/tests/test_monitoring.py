"""Tests for UserMonitor class"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from src.monitoring import UserMonitor


class TestUserMonitorInit:
    """Tests for UserMonitor initialization"""

    @patch("src.monitoring.APIClient")
    @patch("src.monitoring.HateSpeechScorer")
    @patch("src.monitoring.UserEnricher")
    @patch("src.monitoring.RedditScraper")
    def test_init_default_thresholds(self, MockScraper, MockEnricher, MockScorer, MockAPIClient):
        """Test initialization with default thresholds"""
        monitor = UserMonitor()
        assert monitor.high_risk_threshold == 50
        assert monitor.critical_risk_threshold == 70

    @patch("src.monitoring.APIClient")
    @patch("src.monitoring.HateSpeechScorer")
    @patch("src.monitoring.UserEnricher")
    @patch("src.monitoring.RedditScraper")
    def test_init_custom_thresholds(self, MockScraper, MockEnricher, MockScorer, MockAPIClient):
        """Test initialization with custom thresholds"""
        monitor = UserMonitor(high_risk_threshold=40, critical_risk_threshold=80)
        assert monitor.high_risk_threshold == 40
        assert monitor.critical_risk_threshold == 80


class TestGetMonitoredUsers:
    """Tests for get_monitored_users method"""

    @patch("src.monitoring.APIClient")
    @patch("src.monitoring.HateSpeechScorer")
    @patch("src.monitoring.UserEnricher")
    @patch("src.monitoring.RedditScraper")
    def test_get_monitored_users_success(self, MockScraper, MockEnricher, MockScorer, MockAPIClient):
        """Test successful fetch of monitored users"""
        mock_api = MagicMock()
        mock_api.get_monitored_users.return_value = [
            {"username": "user1"},
            {"username": "user2"},
        ]
        MockAPIClient.return_value = mock_api

        monitor = UserMonitor()
        result = monitor.get_monitored_users()

        assert len(result) == 2
        mock_api.get_monitored_users.assert_called_once()

    @patch("src.monitoring.APIClient")
    @patch("src.monitoring.HateSpeechScorer")
    @patch("src.monitoring.UserEnricher")
    @patch("src.monitoring.RedditScraper")
    def test_get_monitored_users_api_error(self, MockScraper, MockEnricher, MockScorer, MockAPIClient):
        """Test handling of API error"""
        mock_api = MagicMock()
        mock_api.get_monitored_users.side_effect = Exception("API Error")
        MockAPIClient.return_value = mock_api

        monitor = UserMonitor()
        result = monitor.get_monitored_users()

        assert result == []


class TestScanUser:
    """Tests for scan_user method"""

    @patch("src.monitoring.APIClient")
    @patch("src.monitoring.HateSpeechScorer")
    @patch("src.monitoring.UserEnricher")
    @patch("src.monitoring.RedditScraper")
    def test_scan_user_success(self, MockScraper, MockEnricher, MockScorer, MockAPIClient):
        """Test successful user scan"""
        # Setup scraper mock
        mock_scraper = MagicMock()
        mock_scraper.get_user_history.return_value = {
            "username": "test_user",
            "total_posts": 5,
            "total_comments": 10,
            "posts": [],
            "comments": [],
        }
        MockScraper.return_value = mock_scraper

        # Setup enricher mock
        mock_enricher = MagicMock()
        mock_enricher.enrich_user_data.return_value = {
            "username": "test_user",
            "content": {"all_text": ["Normal post content"]},
        }
        MockEnricher.return_value = mock_enricher

        # Setup scorer mock
        mock_scorer = MagicMock()
        mock_scorer.score_user.return_value = {
            "username": "test_user",
            "risk_assessment": {"overall_risk_score": 25},
        }
        mock_scorer.score_text.return_value = {
            "risk_score": 10,
            "risk_level": "low",
            "flags": [],
        }
        MockScorer.return_value = mock_scorer

        # Setup API client mock
        mock_api = MagicMock()
        MockAPIClient.return_value = mock_api

        monitor = UserMonitor()
        result = monitor.scan_user("test_user")

        assert result["username"] == "test_user"
        assert result["status"] == "success"
        assert result["new_posts_count"] == 5
        assert result["new_comments_count"] == 10
        assert result["max_risk_score"] == 25

    @patch("src.monitoring.APIClient")
    @patch("src.monitoring.HateSpeechScorer")
    @patch("src.monitoring.UserEnricher")
    @patch("src.monitoring.RedditScraper")
    def test_scan_user_no_content(self, MockScraper, MockEnricher, MockScorer, MockAPIClient):
        """Test scan when user has no content"""
        mock_scraper = MagicMock()
        mock_scraper.get_user_history.return_value = {
            "username": "deleted_user",
            "total_posts": 0,
            "total_comments": 0,
            "posts": [],
            "comments": [],
        }
        MockScraper.return_value = mock_scraper

        monitor = UserMonitor()
        result = monitor.scan_user("deleted_user")

        assert result["status"] == "no_content"

    @patch("src.monitoring.APIClient")
    @patch("src.monitoring.HateSpeechScorer")
    @patch("src.monitoring.UserEnricher")
    @patch("src.monitoring.RedditScraper")
    def test_scan_user_high_risk_content(self, MockScraper, MockEnricher, MockScorer, MockAPIClient):
        """Test scan with high-risk content generates alerts"""
        # Setup scraper mock
        mock_scraper = MagicMock()
        mock_scraper.get_user_history.return_value = {
            "username": "risky_user",
            "total_posts": 1,
            "total_comments": 1,
            "posts": [],
            "comments": [],
        }
        MockScraper.return_value = mock_scraper

        # Setup enricher mock
        mock_enricher = MagicMock()
        mock_enricher.enrich_user_data.return_value = {
            "username": "risky_user",
            "content": {"all_text": ["Hateful content here"]},
        }
        MockEnricher.return_value = mock_enricher

        # Setup scorer mock
        mock_scorer = MagicMock()
        mock_scorer.score_user.return_value = {
            "username": "risky_user",
            "risk_assessment": {"overall_risk_score": 75},
        }
        # High risk score on text
        mock_scorer.score_text.return_value = {
            "risk_score": 60,
            "risk_level": "high",
            "flags": ["hate_speech"],
        }
        MockScorer.return_value = mock_scorer

        # Setup API client mock
        mock_api = MagicMock()
        MockAPIClient.return_value = mock_api

        monitor = UserMonitor()
        result = monitor.scan_user("risky_user")

        assert result["status"] == "success"
        assert len(result["high_risk_items"]) == 1
        assert len(result["alerts_generated"]) == 1
        assert result["alerts_generated"][0]["severity"] == "high"

    @patch("src.monitoring.APIClient")
    @patch("src.monitoring.HateSpeechScorer")
    @patch("src.monitoring.UserEnricher")
    @patch("src.monitoring.RedditScraper")
    def test_scan_user_critical_risk_content(self, MockScraper, MockEnricher, MockScorer, MockAPIClient):
        """Test scan with critical-risk content generates critical alerts"""
        # Setup scraper mock
        mock_scraper = MagicMock()
        mock_scraper.get_user_history.return_value = {
            "username": "critical_user",
            "total_posts": 1,
            "total_comments": 0,
            "posts": [],
            "comments": [],
        }
        MockScraper.return_value = mock_scraper

        # Setup enricher mock
        mock_enricher = MagicMock()
        mock_enricher.enrich_user_data.return_value = {
            "username": "critical_user",
            "content": {"all_text": ["Extremely violent content"]},
        }
        MockEnricher.return_value = mock_enricher

        # Setup scorer mock
        mock_scorer = MagicMock()
        mock_scorer.score_user.return_value = {
            "username": "critical_user",
            "risk_assessment": {"overall_risk_score": 85},
        }
        # Critical risk score (>= 70)
        mock_scorer.score_text.return_value = {
            "risk_score": 80,
            "risk_level": "critical",
            "flags": ["violence", "threats"],
        }
        MockScorer.return_value = mock_scorer

        # Setup API client mock
        mock_api = MagicMock()
        MockAPIClient.return_value = mock_api

        monitor = UserMonitor()
        result = monitor.scan_user("critical_user")

        assert result["alerts_generated"][0]["severity"] == "critical"

    @patch("src.monitoring.APIClient")
    @patch("src.monitoring.HateSpeechScorer")
    @patch("src.monitoring.UserEnricher")
    @patch("src.monitoring.RedditScraper")
    def test_scan_user_error_handling(self, MockScraper, MockEnricher, MockScorer, MockAPIClient):
        """Test error handling during scan"""
        mock_scraper = MagicMock()
        mock_scraper.get_user_history.side_effect = Exception("Network error")
        MockScraper.return_value = mock_scraper

        monitor = UserMonitor()
        result = monitor.scan_user("error_user")

        assert result["status"] == "error"
        assert "error" in result


class TestRunDailyMonitoring:
    """Tests for run_daily_monitoring method"""

    @patch("src.monitoring.APIClient")
    @patch("src.monitoring.HateSpeechScorer")
    @patch("src.monitoring.UserEnricher")
    @patch("src.monitoring.RedditScraper")
    def test_run_daily_monitoring_no_users(self, MockScraper, MockEnricher, MockScorer, MockAPIClient):
        """Test daily monitoring when no users to monitor"""
        mock_api = MagicMock()
        mock_api.get_monitored_users.return_value = []
        MockAPIClient.return_value = mock_api

        monitor = UserMonitor()
        result = monitor.run_daily_monitoring()

        assert result["status"] == "completed"
        assert result["users_scanned"] == 0
        assert result["message"] == "No users to monitor"

    @patch("src.monitoring.APIClient")
    @patch("src.monitoring.HateSpeechScorer")
    @patch("src.monitoring.UserEnricher")
    @patch("src.monitoring.RedditScraper")
    def test_run_daily_monitoring_with_users(self, MockScraper, MockEnricher, MockScorer, MockAPIClient):
        """Test daily monitoring with users to scan"""
        # Setup API mock to return monitored users
        mock_api = MagicMock()
        mock_api.get_monitored_users.return_value = [
            {"username": "user1"},
            {"username": "user2"},
        ]
        MockAPIClient.return_value = mock_api

        # Setup scraper mock
        mock_scraper = MagicMock()
        mock_scraper.get_user_history.return_value = {
            "username": "test",
            "total_posts": 1,
            "total_comments": 1,
            "posts": [],
            "comments": [],
        }
        MockScraper.return_value = mock_scraper

        # Setup enricher mock
        mock_enricher = MagicMock()
        mock_enricher.enrich_user_data.return_value = {
            "username": "test",
            "content": {"all_text": ["Test content"]},
        }
        MockEnricher.return_value = mock_enricher

        # Setup scorer mock
        mock_scorer = MagicMock()
        mock_scorer.score_user.return_value = {
            "username": "test",
            "risk_assessment": {"overall_risk_score": 20},
        }
        mock_scorer.score_text.return_value = {
            "risk_score": 10,
            "risk_level": "low",
            "flags": [],
        }
        MockScorer.return_value = mock_scorer

        monitor = UserMonitor()
        result = monitor.run_daily_monitoring()

        assert result["status"] == "completed"
        assert result["users_scanned"] == 2
        assert "started_at" in result
        assert "completed_at" in result
        assert "duration_seconds" in result

    @patch("src.monitoring.APIClient")
    @patch("src.monitoring.HateSpeechScorer")
    @patch("src.monitoring.UserEnricher")
    @patch("src.monitoring.RedditScraper")
    def test_run_daily_monitoring_finds_high_risk_users(self, MockScraper, MockEnricher, MockScorer, MockAPIClient):
        """Test daily monitoring identifies high-risk users"""
        # Setup API mock
        mock_api = MagicMock()
        mock_api.get_monitored_users.return_value = [{"username": "risky_user"}]
        MockAPIClient.return_value = mock_api

        # Setup scraper mock
        mock_scraper = MagicMock()
        mock_scraper.get_user_history.return_value = {
            "username": "risky_user",
            "total_posts": 1,
            "total_comments": 0,
            "posts": [],
            "comments": [],
        }
        MockScraper.return_value = mock_scraper

        # Setup enricher mock
        mock_enricher = MagicMock()
        mock_enricher.enrich_user_data.return_value = {
            "username": "risky_user",
            "content": {"all_text": ["Hateful content"]},
        }
        MockEnricher.return_value = mock_enricher

        # Setup scorer mock - high risk
        mock_scorer = MagicMock()
        mock_scorer.score_user.return_value = {
            "username": "risky_user",
            "risk_assessment": {"overall_risk_score": 65},
        }
        mock_scorer.score_text.return_value = {
            "risk_score": 60,
            "risk_level": "high",
            "flags": ["hate"],
        }
        MockScorer.return_value = mock_scorer

        monitor = UserMonitor()
        result = monitor.run_daily_monitoring()

        assert result["high_risk_users_found"] == 1
        assert len(result["high_risk_users"]) == 1
        assert result["high_risk_users"][0]["username"] == "risky_user"


class TestCreateAlert:
    """Tests for _create_alert method"""

    @patch("src.monitoring.APIClient")
    @patch("src.monitoring.HateSpeechScorer")
    @patch("src.monitoring.UserEnricher")
    @patch("src.monitoring.RedditScraper")
    def test_create_alert_high_severity(self, MockScraper, MockEnricher, MockScorer, MockAPIClient):
        """Test alert creation with high severity"""
        mock_api = MagicMock()
        MockAPIClient.return_value = mock_api

        monitor = UserMonitor()
        high_risk_item = {
            "text_preview": "Offensive content...",
            "risk_score": 55,
            "risk_level": "high",
            "flags": ["hate"],
        }

        alert = monitor._create_alert("test_user", high_risk_item)

        assert alert["severity"] == "high"
        assert alert["username"] == "test_user"
        assert alert["alert_type"] == "monitored_user_content"
        mock_api.create_alert.assert_called_once()

    @patch("src.monitoring.APIClient")
    @patch("src.monitoring.HateSpeechScorer")
    @patch("src.monitoring.UserEnricher")
    @patch("src.monitoring.RedditScraper")
    def test_create_alert_critical_severity(self, MockScraper, MockEnricher, MockScorer, MockAPIClient):
        """Test alert creation with critical severity"""
        mock_api = MagicMock()
        MockAPIClient.return_value = mock_api

        monitor = UserMonitor()
        critical_item = {
            "text_preview": "Very violent content...",
            "risk_score": 85,
            "risk_level": "critical",
            "flags": ["violence", "threats"],
        }

        alert = monitor._create_alert("dangerous_user", critical_item)

        assert alert["severity"] == "critical"


class TestLogMonitoringActivity:
    """Tests for _log_monitoring_activity method"""

    @patch("src.monitoring.APIClient")
    @patch("src.monitoring.HateSpeechScorer")
    @patch("src.monitoring.UserEnricher")
    @patch("src.monitoring.RedditScraper")
    def test_log_monitoring_activity_success(self, MockScraper, MockEnricher, MockScorer, MockAPIClient):
        """Test successful logging of monitoring activity"""
        mock_api = MagicMock()
        MockAPIClient.return_value = mock_api

        monitor = UserMonitor()
        result = {
            "new_posts_count": 5,
            "new_comments_count": 10,
            "high_risk_items": [],
            "alerts_generated": [],
            "max_risk_score": 25,
            "status": "success",
        }

        monitor._log_monitoring_activity("test_user", result)

        mock_api.create_monitoring_log.assert_called_once()
        call_args = mock_api.create_monitoring_log.call_args[0][0]
        assert call_args["username"] == "test_user"
        assert call_args["activity_type"] == "daily_scan"

    @patch("src.monitoring.APIClient")
    @patch("src.monitoring.HateSpeechScorer")
    @patch("src.monitoring.UserEnricher")
    @patch("src.monitoring.RedditScraper")
    def test_log_monitoring_activity_api_error(self, MockScraper, MockEnricher, MockScorer, MockAPIClient):
        """Test handling of API error when logging"""
        mock_api = MagicMock()
        mock_api.create_monitoring_log.side_effect = Exception("API Error")
        MockAPIClient.return_value = mock_api

        monitor = UserMonitor()
        result = {
            "new_posts_count": 0,
            "new_comments_count": 0,
            "high_risk_items": [],
            "alerts_generated": [],
            "max_risk_score": 0,
            "status": "success",
        }

        # Should not raise exception
        monitor._log_monitoring_activity("test_user", result)
