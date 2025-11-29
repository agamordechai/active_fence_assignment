"""Tests for UserEnricher"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from src.enrichers.user_enricher import UserEnricher


class TestUserEnricherInit:
    """Tests for UserEnricher initialization"""

    def test_init_sets_two_months_ago(self):
        """Test that two_months_ago is set correctly"""
        enricher = UserEnricher()
        expected = (datetime.now() - timedelta(days=60)).timestamp()
        # Allow 1 second tolerance
        assert abs(enricher.two_months_ago - expected) < 1


class TestEnrichUserData:
    """Tests for enrich_user_data method"""

    def test_enrich_user_data_basic(self, sample_raw_user_data):
        """Test basic user data enrichment"""
        enricher = UserEnricher()
        enriched = enricher.enrich_user_data(sample_raw_user_data)

        assert enriched["username"] == "test_user"
        assert "enrichment_timestamp" in enriched
        assert "activity_metrics" in enriched
        assert "subreddit_diversity" in enriched
        assert "content" in enriched
        assert "profile_status" in enriched

    def test_enrich_user_data_filters_recent(self, sample_raw_user_data):
        """Test that only recent activity (last 2 months) is counted"""
        enricher = UserEnricher()
        enriched = enricher.enrich_user_data(sample_raw_user_data)

        # Only 1 recent post and 1 recent comment (within 60 days)
        assert enriched["activity_metrics"]["recent_posts_2m"] == 1
        assert enriched["activity_metrics"]["recent_comments_2m"] == 1
        assert enriched["activity_metrics"]["total_recent_activity"] == 2

    def test_enrich_user_data_calculates_averages(self, sample_raw_user_data):
        """Test average score calculations"""
        enricher = UserEnricher()
        enriched = enricher.enrich_user_data(sample_raw_user_data)

        # Recent post has score 100, recent comment has score 10
        assert enriched["activity_metrics"]["avg_post_score"] == 100.0
        assert enriched["activity_metrics"]["avg_comment_score"] == 10.0

    def test_enrich_user_data_calculates_subreddits(self, sample_raw_user_data):
        """Test subreddit diversity calculation"""
        enricher = UserEnricher()
        enriched = enricher.enrich_user_data(sample_raw_user_data)

        # Only subreddit_a appears in recent activity (for both post and comment)
        assert enriched["subreddit_diversity"]["unique_subreddits_count"] == 1
        assert "subreddit_a" in enriched["subreddit_diversity"]["subreddits"]

    def test_enrich_user_data_collects_text(self, sample_raw_user_data):
        """Test that text content is collected"""
        enricher = UserEnricher()
        enriched = enricher.enrich_user_data(sample_raw_user_data)

        all_text = enriched["content"]["all_text"]
        assert "Recent Post" in all_text  # Title
        assert "Recent content" in all_text  # Selftext
        assert "Recent comment" in all_text  # Comment body
        assert len(all_text) == 3  # Only recent content

    def test_enrich_user_data_empty_user(self):
        """Test enrichment of user with no activity"""
        enricher = UserEnricher()
        empty_user = {"username": "new_user", "posts": [], "comments": []}

        enriched = enricher.enrich_user_data(empty_user)

        assert enriched["username"] == "new_user"
        assert enriched["activity_metrics"]["total_recent_activity"] == 0
        assert enriched["profile_status"] == "new_user_no_activity"

    def test_enrich_user_data_missing_fields(self):
        """Test handling of missing fields"""
        enricher = UserEnricher()
        minimal_user = {"username": "minimal"}

        enriched = enricher.enrich_user_data(minimal_user)

        assert enriched["username"] == "minimal"
        assert enriched["activity_metrics"]["total_posts"] == 0
        assert enriched["activity_metrics"]["total_comments"] == 0


class TestDetermineProfileStatus:
    """Tests for _determine_profile_status method"""

    def test_new_user_no_activity(self):
        """Test new user with no activity"""
        enricher = UserEnricher()
        status = enricher._determine_profile_status(0, [], [])
        assert status == "new_user_no_activity"

    def test_no_recent_activity(self):
        """Test user with old activity only"""
        enricher = UserEnricher()
        status = enricher._determine_profile_status(0, [{"id": 1}], [{"id": 2}])
        assert status == "no_recent_activity"

    def test_low_activity(self):
        """Test user with low activity (1-9)"""
        enricher = UserEnricher()
        status = enricher._determine_profile_status(5, [], [])
        assert status == "low_activity"

    def test_moderate_activity(self):
        """Test user with moderate activity (10-49)"""
        enricher = UserEnricher()
        status = enricher._determine_profile_status(25, [], [])
        assert status == "moderate_activity"

    def test_high_activity(self):
        """Test user with high activity (50+)"""
        enricher = UserEnricher()
        status = enricher._determine_profile_status(100, [], [])
        assert status == "high_activity"


class TestEnrichMultipleUsers:
    """Tests for enrich_multiple_users method"""

    def test_enrich_multiple_users(self, sample_raw_user_data):
        """Test enriching multiple users"""
        enricher = UserEnricher()

        user1 = sample_raw_user_data.copy()
        user1["username"] = "user1"

        user2 = sample_raw_user_data.copy()
        user2["username"] = "user2"

        users = [user1, user2]
        enriched = enricher.enrich_multiple_users(users)

        assert len(enriched) == 2
        assert enriched[0]["username"] == "user1"
        assert enriched[1]["username"] == "user2"

    def test_enrich_multiple_users_handles_errors(self, sample_raw_user_data):
        """Test that errors don't stop processing"""
        enricher = UserEnricher()

        valid_user = sample_raw_user_data.copy()

        # Create an invalid user that will cause an error but is not None
        # (so the error handler can still call .get() on it)
        invalid_user = {"username": "broken_user", "posts": "not_a_list"}  # Invalid type

        users = [valid_user, invalid_user]
        enriched = enricher.enrich_multiple_users(users)

        # Only valid user should be in results (invalid user should be skipped due to error)
        assert len(enriched) == 1
        assert enriched[0]["username"] == "test_user"

    def test_enrich_multiple_users_empty_list(self):
        """Test enriching empty list"""
        enricher = UserEnricher()
        enriched = enricher.enrich_multiple_users([])
        assert enriched == []


class TestActivityPerDay:
    """Tests for activity per day calculation"""

    def test_activity_per_day_calculation(self, sample_raw_user_data):
        """Test activity per day is calculated correctly"""
        enricher = UserEnricher()
        enriched = enricher.enrich_user_data(sample_raw_user_data)

        # 2 recent activities over 60 days = 0.03 per day
        expected = round(2 / 60, 2)
        assert enriched["activity_metrics"]["activity_per_day"] == expected
