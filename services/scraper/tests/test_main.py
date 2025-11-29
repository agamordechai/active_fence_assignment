"""Tests for main entry point"""
import pytest
from unittest.mock import patch, MagicMock
import sys


class TestRunSingle:
    """Tests for run_single function"""

    @patch("src.main.settings")
    @patch("src.main.DataPipeline")
    def test_run_single_success(self, MockPipeline, mock_settings):
        """Test successful single run"""
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

        from src.main import run_single

        result = run_single()

        mock_pipeline.run_full_pipeline.assert_called_once()
        assert result == {"posts": [], "users": []}

    @patch("src.main.settings")
    @patch("src.main.DataPipeline")
    def test_run_single_keyboard_interrupt(self, MockPipeline, mock_settings):
        """Test single run handles keyboard interrupt"""
        mock_settings.subreddits_list = ["test_sub"]
        mock_settings.posts_per_subreddit = 10
        mock_settings.max_users_to_enrich = 5
        mock_settings.search_terms_list = []
        mock_settings.posts_per_search = 10

        mock_pipeline = MagicMock()
        mock_pipeline.run_full_pipeline.side_effect = KeyboardInterrupt()
        MockPipeline.return_value = mock_pipeline

        from src.main import run_single

        # Should not raise, just return None
        result = run_single()
        assert result is None

    @patch("src.main.settings")
    @patch("src.main.DataPipeline")
    def test_run_single_exception(self, MockPipeline, mock_settings):
        """Test single run re-raises exceptions"""
        mock_settings.subreddits_list = ["test_sub"]
        mock_settings.posts_per_subreddit = 10
        mock_settings.max_users_to_enrich = 5
        mock_settings.search_terms_list = []
        mock_settings.posts_per_search = 10

        mock_pipeline = MagicMock()
        mock_pipeline.run_full_pipeline.side_effect = Exception("Pipeline error")
        MockPipeline.return_value = mock_pipeline

        from src.main import run_single

        with pytest.raises(Exception, match="Pipeline error"):
            run_single()


class TestRunScheduler:
    """Tests for run_scheduler function"""

    @patch("src.main.time.sleep")
    @patch("src.main.settings")
    @patch("src.main.DataPipeline")
    def test_run_scheduler_executes_pipeline(self, MockPipeline, mock_settings, mock_sleep):
        """Test scheduler executes pipeline and handles interrupt"""
        mock_settings.subreddits_list = ["test_sub"]
        mock_settings.posts_per_subreddit = 10
        mock_settings.max_users_to_enrich = 5
        mock_settings.search_terms_list = []
        mock_settings.posts_per_search = 10

        mock_pipeline = MagicMock()
        # First call succeeds, second raises KeyboardInterrupt
        mock_pipeline.run_full_pipeline.side_effect = [
            {"posts": [], "users": []},
            KeyboardInterrupt(),
        ]
        MockPipeline.return_value = mock_pipeline

        # Make sleep raise KeyboardInterrupt to exit loop
        mock_sleep.side_effect = KeyboardInterrupt()

        from src.main import run_scheduler

        # Should not raise
        run_scheduler()

        # Pipeline should have been called at least once
        assert mock_pipeline.run_full_pipeline.call_count >= 1

    @patch("src.main.time.sleep")
    @patch("src.main.settings")
    @patch("src.main.DataPipeline")
    def test_run_scheduler_handles_pipeline_error(self, MockPipeline, mock_settings, mock_sleep):
        """Test scheduler continues after pipeline error"""
        mock_settings.subreddits_list = ["test_sub"]
        mock_settings.posts_per_subreddit = 10
        mock_settings.max_users_to_enrich = 5
        mock_settings.search_terms_list = []
        mock_settings.posts_per_search = 10

        mock_pipeline = MagicMock()
        # First call raises error, then interrupt via sleep
        mock_pipeline.run_full_pipeline.side_effect = Exception("Error")
        MockPipeline.return_value = mock_pipeline

        mock_sleep.side_effect = KeyboardInterrupt()

        from src.main import run_scheduler

        # Should not raise
        run_scheduler()


class TestRunContinuous:
    """Tests for run_continuous function"""

    @patch("src.main.time.sleep")
    @patch("src.main.settings")
    @patch("src.main.DataPipeline")
    def test_run_continuous_executes_pipeline(self, MockPipeline, mock_settings, mock_sleep):
        """Test continuous mode executes pipeline"""
        mock_settings.subreddits_list = ["test_sub"]
        mock_settings.posts_per_subreddit = 10
        mock_settings.max_users_to_enrich = 5
        mock_settings.search_terms_list = []
        mock_settings.posts_per_search = 10

        mock_pipeline = MagicMock()
        mock_pipeline.run_full_pipeline.return_value = {"posts": [], "users": []}
        MockPipeline.return_value = mock_pipeline

        mock_sleep.side_effect = KeyboardInterrupt()

        from src.main import run_continuous

        # Should not raise
        run_continuous()

        assert mock_pipeline.run_full_pipeline.call_count >= 1

    @patch("src.main.time.sleep")
    @patch("src.main.settings")
    @patch("src.main.DataPipeline")
    def test_run_continuous_handles_error(self, MockPipeline, mock_settings, mock_sleep):
        """Test continuous mode handles pipeline errors"""
        mock_settings.subreddits_list = ["test_sub"]
        mock_settings.posts_per_subreddit = 10
        mock_settings.max_users_to_enrich = 5
        mock_settings.search_terms_list = []
        mock_settings.posts_per_search = 10

        mock_pipeline = MagicMock()
        mock_pipeline.run_full_pipeline.side_effect = Exception("Error")
        MockPipeline.return_value = mock_pipeline

        mock_sleep.side_effect = KeyboardInterrupt()

        from src.main import run_continuous

        # Should not raise
        run_continuous()


class TestMain:
    """Tests for main function"""

    @patch("src.main.run_single")
    @patch("src.main.settings")
    def test_main_single_mode(self, mock_settings, mock_run):
        """Test main runs single mode"""
        mock_settings.run_mode = "single"
        mock_settings.subreddits_list = ["test"]
        mock_settings.posts_per_subreddit = 10
        mock_settings.print_config = MagicMock()

        from src.main import main

        main()

        mock_run.assert_called_once()

    @patch("src.main.run_scheduler")
    @patch("src.main.settings")
    def test_main_scheduler_mode(self, mock_settings, mock_run):
        """Test main runs scheduler mode"""
        mock_settings.run_mode = "scheduler"
        mock_settings.subreddits_list = ["test"]
        mock_settings.posts_per_subreddit = 10
        mock_settings.print_config = MagicMock()

        from src.main import main

        main()

        mock_run.assert_called_once()

    @patch("src.main.run_continuous")
    @patch("src.main.settings")
    def test_main_continuous_mode(self, mock_settings, mock_run):
        """Test main runs continuous mode"""
        mock_settings.run_mode = "continuous"
        mock_settings.subreddits_list = ["test"]
        mock_settings.posts_per_subreddit = 10
        mock_settings.print_config = MagicMock()

        from src.main import main

        main()

        mock_run.assert_called_once()

    @patch("src.main.sys.exit")
    @patch("src.main.settings")
    def test_main_invalid_mode(self, mock_settings, mock_exit):
        """Test main handles invalid mode"""
        mock_settings.run_mode = "invalid_mode"
        mock_settings.subreddits_list = ["test"]
        mock_settings.posts_per_subreddit = 10
        mock_settings.print_config = MagicMock()

        from src.main import main

        main()

        mock_exit.assert_called_once_with(1)

    @patch("src.main.run_single")
    @patch("src.main.settings")
    def test_main_prints_config(self, mock_settings, mock_run_single):
        """Test main prints configuration"""
        mock_settings.run_mode = "single"
        mock_settings.subreddits_list = ["test"]
        mock_settings.posts_per_subreddit = 10
        mock_settings.print_config = MagicMock()

        from src.main import main

        main()

        mock_settings.print_config.assert_called_once()
