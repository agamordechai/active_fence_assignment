"""Tests for main entry point"""
import pytest
from unittest.mock import patch, MagicMock
import sys


class TestRun:
    """Tests for run function"""

    @patch("src.main.time.sleep")
    @patch("src.main.settings")
    @patch("src.main.DataPipeline")
    def test_run_executes_pipeline(self, MockPipeline, mock_settings, mock_sleep):
        """Test run executes pipeline and waits"""
        mock_settings.subreddits_list = ["test_sub"]
        mock_settings.posts_per_subreddit = 10
        mock_settings.max_users_to_enrich = 5
        mock_settings.search_terms_list = ["test"]
        mock_settings.posts_per_search = 10

        mock_pipeline = MagicMock()
        mock_pipeline.run_full_pipeline.return_value = {
            "posts": [],
            "users": [],
        }
        MockPipeline.return_value = mock_pipeline

        # Make sleep raise KeyboardInterrupt to exit loop after first run
        mock_sleep.side_effect = KeyboardInterrupt()

        from src.main import run

        # Should not raise
        run()

        # Pipeline should have been called once
        assert mock_pipeline.run_full_pipeline.call_count == 1
        mock_sleep.assert_called_once()

    @patch("src.main.time.sleep")
    @patch("src.main.settings")
    @patch("src.main.DataPipeline")
    def test_run_handles_pipeline_error(self, MockPipeline, mock_settings, mock_sleep):
        """Test run continues after pipeline error"""
        mock_settings.subreddits_list = ["test_sub"]
        mock_settings.posts_per_subreddit = 10
        mock_settings.max_users_to_enrich = 5
        mock_settings.search_terms_list = []
        mock_settings.posts_per_search = 10

        mock_pipeline = MagicMock()
        mock_pipeline.run_full_pipeline.side_effect = Exception("Pipeline error")
        MockPipeline.return_value = mock_pipeline

        # Make sleep raise KeyboardInterrupt to exit loop
        mock_sleep.side_effect = KeyboardInterrupt()

        from src.main import run

        # Should not raise
        run()

        # Pipeline should have been called once despite error
        assert mock_pipeline.run_full_pipeline.call_count == 1


class TestMain:
    """Tests for main function"""

    @patch("src.main.run")
    @patch("src.main.settings")
    def test_main_calls_run(self, mock_settings, mock_run):
        """Test main calls run function"""
        mock_settings.subreddits_list = ["test"]
        mock_settings.posts_per_subreddit = 10
        mock_settings.print_config = MagicMock()

        from src.main import main

        main()

        mock_run.assert_called_once()

    @patch("src.main.run")
    @patch("src.main.settings")
    def test_main_prints_config(self, mock_settings, mock_run):
        """Test main prints configuration"""
        mock_settings.subreddits_list = ["test"]
        mock_settings.posts_per_subreddit = 10
        mock_settings.print_config = MagicMock()

        from src.main import main

        main()

        mock_settings.print_config.assert_called_once()


