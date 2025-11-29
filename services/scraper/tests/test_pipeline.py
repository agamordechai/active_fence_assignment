"""Tests for DataPipeline"""
import pytest
from unittest.mock import patch, MagicMock, call

from src.pipeline import DataPipeline
from src.api_client import BulkResult


class TestDataPipelineInit:
    """Tests for DataPipeline initialization"""

    def test_init_creates_components(self, mock_lexicon):
        """Test that pipeline initializes all components"""
        with patch("src.pipeline.HateSpeechScorer") as MockScorer:
            with patch("src.pipeline.APIClient"):
                pipeline = DataPipeline()

                assert pipeline.scraper is not None
                assert pipeline.enricher is not None


class TestRunFullPipeline:
    """Tests for run_full_pipeline method"""

    def test_run_full_pipeline_basic(self):
        """Test basic pipeline execution"""
        with patch("src.pipeline.RedditScraper") as MockScraper:
            with patch("src.pipeline.UserEnricher") as MockEnricher:
                with patch("src.pipeline.HateSpeechScorer") as MockScorer:
                    with patch("src.pipeline.APIClient") as MockAPIClient:
                        # Setup mocks
                        mock_scraper = MagicMock()
                        mock_scraper.collect_from_multiple_subreddits.return_value = [
                            {
                                "id": "post1",
                                "author": "user1",
                                "title": "Test",
                                "selftext": "Content",
                            }
                        ]
                        mock_scraper.get_user_history.return_value = {
                            "username": "user1",
                            "posts": [],
                            "comments": [],
                        }
                        MockScraper.return_value = mock_scraper

                        mock_enricher = MagicMock()
                        mock_enricher.enrich_multiple_users.return_value = [
                            {
                                "username": "user1",
                                "content": {"all_text": []},
                            }
                        ]
                        MockEnricher.return_value = mock_enricher

                        mock_scorer = MagicMock()
                        mock_scorer.score_multiple_posts.return_value = [
                            {
                                "id": "post1",
                                "author": "user1",
                                "risk_assessment": {"risk_score": 10},
                            }
                        ]
                        mock_scorer.score_multiple_users.return_value = [
                            {
                                "username": "user1",
                                "risk_assessment": {
                                    "overall_risk_score": 5,
                                    "risk_level": "minimal",
                                },
                            }
                        ]
                        MockScorer.return_value = mock_scorer

                        mock_api_client = MagicMock()
                        mock_api_client.health_check.return_value = True
                        mock_api_client.send_posts.return_value = BulkResult(created=1)
                        mock_api_client.send_users.return_value = BulkResult(created=1)
                        MockAPIClient.return_value = mock_api_client

                        # Run pipeline
                        pipeline = DataPipeline()
                        result = pipeline.run_full_pipeline(
                            subreddits=["test"],
                            posts_per_subreddit=10,
                            max_users_to_enrich=5,
                        )

                        # Verify results
                        assert "posts" in result
                        assert "users" in result
                        assert len(result["posts"]) == 1
                        assert len(result["users"]) == 1

    def test_run_full_pipeline_filters_special_authors(self):
        """Test that deleted/bot authors are filtered"""
        with patch("src.pipeline.RedditScraper") as MockScraper:
            with patch("src.pipeline.UserEnricher") as MockEnricher:
                with patch("src.pipeline.HateSpeechScorer") as MockScorer:
                    with patch("src.pipeline.APIClient") as MockAPIClient:
                        # Setup mocks
                        mock_scraper = MagicMock()
                        mock_scraper.collect_from_multiple_subreddits.return_value = [
                            {"id": "post1", "author": "[deleted]", "title": "Test"},
                            {"id": "post2", "author": "AutoModerator", "title": "Test"},
                            {"id": "post3", "author": "real_user", "title": "Test"},
                        ]
                        mock_scraper.get_user_history.return_value = {
                            "username": "real_user",
                            "posts": [],
                            "comments": [],
                        }
                        MockScraper.return_value = mock_scraper

                        mock_enricher = MagicMock()
                        mock_enricher.enrich_multiple_users.return_value = [
                            {"username": "real_user", "content": {"all_text": []}}
                        ]
                        MockEnricher.return_value = mock_enricher

                        mock_scorer = MagicMock()
                        mock_scorer.score_multiple_posts.return_value = [
                            {"id": "post1", "author": "[deleted]", "risk_assessment": {"risk_score": 0}},
                            {"id": "post2", "author": "AutoModerator", "risk_assessment": {"risk_score": 0}},
                            {"id": "post3", "author": "real_user", "risk_assessment": {"risk_score": 0}},
                        ]
                        mock_scorer.score_multiple_users.return_value = [
                            {
                                "username": "real_user",
                                "risk_assessment": {"overall_risk_score": 0, "risk_level": "minimal"},
                            }
                        ]
                        MockScorer.return_value = mock_scorer

                        mock_api_client = MagicMock()
                        mock_api_client.health_check.return_value = True
                        mock_api_client.send_posts.return_value = BulkResult(created=3)
                        mock_api_client.send_users.return_value = BulkResult(created=1)
                        MockAPIClient.return_value = mock_api_client

                        # Run pipeline
                        pipeline = DataPipeline()
                        result = pipeline.run_full_pipeline(
                            subreddits=["test"],
                            posts_per_subreddit=10,
                            max_users_to_enrich=10,
                        )

                        # Only real_user should be enriched (not [deleted] or AutoModerator)
                        assert mock_scraper.get_user_history.call_count == 1
                        mock_scraper.get_user_history.assert_called_with("real_user", limit=100)

    def test_run_full_pipeline_prioritizes_high_risk_authors(self):
        """Test that high-risk authors are prioritized for enrichment"""
        with patch("src.pipeline.RedditScraper") as MockScraper:
            with patch("src.pipeline.UserEnricher") as MockEnricher:
                with patch("src.pipeline.HateSpeechScorer") as MockScorer:
                    with patch("src.pipeline.APIClient") as MockAPIClient:
                        # Setup mocks
                        mock_scraper = MagicMock()
                        mock_scraper.collect_from_multiple_subreddits.return_value = [
                            {"id": "post1", "author": "low_risk_user", "title": "Normal post"},
                            {"id": "post2", "author": "high_risk_user", "title": "Risky post"},
                        ]
                        mock_scraper.get_user_history.return_value = {
                            "username": "high_risk_user",
                            "posts": [],
                            "comments": [],
                        }
                        MockScraper.return_value = mock_scraper

                        mock_enricher = MagicMock()
                        mock_enricher.enrich_multiple_users.return_value = [
                            {"username": "high_risk_user", "content": {"all_text": []}}
                        ]
                        MockEnricher.return_value = mock_enricher

                        mock_scorer = MagicMock()
                        # High risk post
                        mock_scorer.score_multiple_posts.return_value = [
                            {
                                "id": "post1",
                                "author": "low_risk_user",
                                "risk_assessment": {"risk_score": 10},
                            },
                            {
                                "id": "post2",
                                "author": "high_risk_user",
                                "risk_assessment": {"risk_score": 70},
                            },
                        ]
                        mock_scorer.score_multiple_users.return_value = [
                            {
                                "username": "high_risk_user",
                                "risk_assessment": {"overall_risk_score": 70, "risk_level": "critical"},
                            }
                        ]
                        MockScorer.return_value = mock_scorer

                        mock_api_client = MagicMock()
                        mock_api_client.health_check.return_value = True
                        mock_api_client.send_posts.return_value = BulkResult(created=2)
                        mock_api_client.send_users.return_value = BulkResult(created=1)
                        MockAPIClient.return_value = mock_api_client

                        # Run pipeline with limit of 1 user
                        pipeline = DataPipeline()
                        result = pipeline.run_full_pipeline(
                            subreddits=["test"],
                            posts_per_subreddit=10,
                            max_users_to_enrich=1,
                        )

                        # High risk user should be prioritized
                        mock_scraper.get_user_history.assert_called_with("high_risk_user", limit=100)


class TestSendToAPI:
    """Tests for _send_to_api method"""

    def test_send_to_api_success(self):
        """Test successful API sending"""
        with patch("src.pipeline.RedditScraper"):
            with patch("src.pipeline.UserEnricher"):
                with patch("src.pipeline.HateSpeechScorer"):
                    with patch("src.pipeline.APIClient") as MockAPIClient:
                        mock_api_client = MagicMock()
                        mock_api_client.health_check.return_value = True
                        mock_api_client.send_posts.return_value = BulkResult(created=5)
                        mock_api_client.send_users.return_value = BulkResult(created=3)
                        MockAPIClient.return_value = mock_api_client

                        pipeline = DataPipeline()
                        pipeline._send_to_api(
                            [{"id": "post1"}],
                            [{"username": "user1"}],
                        )

                        mock_api_client.health_check.assert_called_once()
                        mock_api_client.send_posts.assert_called_once()
                        mock_api_client.send_users.assert_called_once()

    def test_send_to_api_health_check_fails(self):
        """Test API sending when health check fails"""
        with patch("src.pipeline.RedditScraper"):
            with patch("src.pipeline.UserEnricher"):
                with patch("src.pipeline.HateSpeechScorer"):
                    with patch("src.pipeline.APIClient") as MockAPIClient:
                        mock_api_client = MagicMock()
                        mock_api_client.health_check.return_value = False
                        MockAPIClient.return_value = mock_api_client

                        pipeline = DataPipeline()
                        pipeline._send_to_api(
                            [{"id": "post1"}],
                            [{"username": "user1"}],
                        )

                        # Should not attempt to send if health check fails
                        mock_api_client.send_posts.assert_not_called()
                        mock_api_client.send_users.assert_not_called()

    def test_send_to_api_handles_exception(self):
        """Test API sending handles exceptions gracefully"""
        with patch("src.pipeline.RedditScraper"):
            with patch("src.pipeline.UserEnricher"):
                with patch("src.pipeline.HateSpeechScorer"):
                    with patch("src.pipeline.APIClient") as MockAPIClient:
                        mock_api_client = MagicMock()
                        mock_api_client.health_check.return_value = True
                        mock_api_client.send_posts.side_effect = Exception("API Error")
                        MockAPIClient.return_value = mock_api_client

                        pipeline = DataPipeline()
                        # Should not raise exception
                        pipeline._send_to_api(
                            [{"id": "post1"}],
                            [{"username": "user1"}],
                        )


class TestLogSummaryReport:
    """Tests for _log_summary_report method"""

    def test_log_summary_report(self):
        """Test summary report logging"""
        with patch("src.pipeline.RedditScraper"):
            with patch("src.pipeline.UserEnricher"):
                with patch("src.pipeline.HateSpeechScorer"):
                    with patch("src.pipeline.APIClient"):
                        pipeline = DataPipeline()

                        all_posts = [{"id": "1"}, {"id": "2"}]
                        scored_posts = [
                            {"id": "1", "risk_assessment": {"risk_score": 10}},
                            {"id": "2", "risk_assessment": {"risk_score": 60}},
                        ]
                        high_risk_posts = [scored_posts[1]]
                        scored_users = [
                            {
                                "username": "user1",
                                "risk_assessment": {"overall_risk_score": 50, "risk_level": "high"},
                            }
                        ]
                        risk_distribution = {
                            "critical": 0,
                            "high": 1,
                            "medium": 0,
                            "low": 0,
                            "minimal": 0,
                        }

                        # Should not raise any exceptions
                        pipeline._log_summary_report(
                            all_posts,
                            scored_posts,
                            high_risk_posts,
                            scored_users,
                            risk_distribution,
                        )

    def test_log_summary_report_empty_data(self):
        """Test summary report with empty data"""
        with patch("src.pipeline.RedditScraper"):
            with patch("src.pipeline.UserEnricher"):
                with patch("src.pipeline.HateSpeechScorer"):
                    with patch("src.pipeline.APIClient"):
                        pipeline = DataPipeline()

                        # Should handle empty data without errors
                        pipeline._log_summary_report([], [], [], [], {})
