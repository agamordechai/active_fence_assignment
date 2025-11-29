"""Tests for RedditScraper"""
import pytest
import responses
import json
from unittest.mock import patch, MagicMock
from requests.exceptions import HTTPError, RequestException

from src.collectors.reddit_scraper import RedditScraper


class TestRedditScraperInit:
    """Tests for RedditScraper initialization"""

    def test_init_default_rate_limit(self):
        """Test default rate limit delay"""
        scraper = RedditScraper()
        assert scraper.rate_limit_delay == 2.0

    def test_init_custom_rate_limit(self):
        """Test custom rate limit delay"""
        scraper = RedditScraper(rate_limit_delay=5.0)
        assert scraper.rate_limit_delay == 5.0

    def test_init_sets_headers(self):
        """Test that headers are set correctly"""
        scraper = RedditScraper()
        assert "User-Agent" in scraper.session.headers


class TestGetSubredditPosts:
    """Tests for get_subreddit_posts method"""

    @responses.activate
    def test_get_subreddit_posts_success(self, sample_reddit_post_response):
        """Test successful fetching of subreddit posts"""
        responses.add(
            responses.GET,
            "https://www.reddit.com/r/test_subreddit/new.json?limit=100",
            json=sample_reddit_post_response,
            status=200,
        )

        scraper = RedditScraper(rate_limit_delay=0)
        posts = scraper.get_subreddit_posts("test_subreddit", limit=100)

        assert len(posts) == 2
        assert posts[0]["id"] == "abc123"
        assert posts[0]["title"] == "Test Post Title"
        assert posts[0]["author"] == "test_user"
        assert posts[0]["subreddit"] == "test_subreddit"
        assert "created_date" in posts[0]

    @responses.activate
    def test_get_subreddit_posts_empty(self):
        """Test fetching from empty subreddit"""
        responses.add(
            responses.GET,
            "https://www.reddit.com/r/empty_subreddit/new.json?limit=100",
            json={"data": {"children": []}},
            status=200,
        )

        scraper = RedditScraper(rate_limit_delay=0)
        posts = scraper.get_subreddit_posts("empty_subreddit")

        assert posts == []

    @responses.activate
    def test_get_subreddit_posts_http_error(self):
        """Test handling of HTTP errors"""
        responses.add(
            responses.GET,
            "https://www.reddit.com/r/private_subreddit/new.json?limit=100",
            status=403,
        )

        scraper = RedditScraper(rate_limit_delay=0)
        posts = scraper.get_subreddit_posts("private_subreddit")

        assert posts == []

    @responses.activate
    def test_get_subreddit_posts_json_error(self):
        """Test handling of invalid JSON"""
        responses.add(
            responses.GET,
            "https://www.reddit.com/r/broken/new.json?limit=100",
            body="not valid json",
            status=200,
        )

        scraper = RedditScraper(rate_limit_delay=0)
        posts = scraper.get_subreddit_posts("broken")

        assert posts == []

    @responses.activate
    def test_get_subreddit_posts_different_sort(self, sample_reddit_post_response):
        """Test fetching with different sort options"""
        responses.add(
            responses.GET,
            "https://www.reddit.com/r/test/hot.json?limit=50",
            json=sample_reddit_post_response,
            status=200,
        )

        scraper = RedditScraper(rate_limit_delay=0)
        posts = scraper.get_subreddit_posts("test", limit=50, sort="hot")

        assert len(posts) == 2

    @responses.activate
    def test_get_subreddit_posts_limit_cap(self, sample_reddit_post_response):
        """Test that limit is capped at 100"""
        responses.add(
            responses.GET,
            "https://www.reddit.com/r/test/new.json?limit=100",
            json=sample_reddit_post_response,
            status=200,
        )

        scraper = RedditScraper(rate_limit_delay=0)
        # Request more than 100, should be capped
        posts = scraper.get_subreddit_posts("test", limit=500)

        assert len(posts) == 2


class TestGetUserPosts:
    """Tests for get_user_posts method"""

    @responses.activate
    def test_get_user_posts_success(self, sample_user_posts_response):
        """Test successful fetching of user posts"""
        responses.add(
            responses.GET,
            "https://www.reddit.com/user/test_user/submitted.json?limit=100",
            json=sample_user_posts_response,
            status=200,
        )

        scraper = RedditScraper(rate_limit_delay=0)
        posts = scraper.get_user_posts("test_user")

        assert len(posts) == 1
        assert posts[0]["id"] == "user_post_1"
        assert "created_date" in posts[0]

    @responses.activate
    def test_get_user_posts_not_found(self):
        """Test handling of non-existent user"""
        responses.add(
            responses.GET,
            "https://www.reddit.com/user/nonexistent/submitted.json?limit=100",
            status=404,
        )

        scraper = RedditScraper(rate_limit_delay=0)
        posts = scraper.get_user_posts("nonexistent")

        assert posts == []


class TestGetUserComments:
    """Tests for get_user_comments method"""

    @responses.activate
    def test_get_user_comments_success(self, sample_user_comments_response):
        """Test successful fetching of user comments"""
        responses.add(
            responses.GET,
            "https://www.reddit.com/user/test_user/comments.json?limit=100",
            json=sample_user_comments_response,
            status=200,
        )

        scraper = RedditScraper(rate_limit_delay=0)
        comments = scraper.get_user_comments("test_user")

        assert len(comments) == 1
        assert comments[0]["id"] == "comment_1"
        assert comments[0]["body"] == "This is a test comment"
        assert "created_date" in comments[0]

    @responses.activate
    def test_get_user_comments_not_found(self):
        """Test handling of non-existent user"""
        responses.add(
            responses.GET,
            "https://www.reddit.com/user/nonexistent/comments.json?limit=100",
            status=404,
        )

        scraper = RedditScraper(rate_limit_delay=0)
        comments = scraper.get_user_comments("nonexistent")

        assert comments == []


class TestGetUserHistory:
    """Tests for get_user_history method"""

    @responses.activate
    def test_get_user_history_success(
        self, sample_user_posts_response, sample_user_comments_response
    ):
        """Test successful fetching of complete user history"""
        responses.add(
            responses.GET,
            "https://www.reddit.com/user/test_user/submitted.json?limit=100",
            json=sample_user_posts_response,
            status=200,
        )
        responses.add(
            responses.GET,
            "https://www.reddit.com/user/test_user/comments.json?limit=100",
            json=sample_user_comments_response,
            status=200,
        )

        scraper = RedditScraper(rate_limit_delay=0)
        history = scraper.get_user_history("test_user")

        assert history["username"] == "test_user"
        assert history["total_posts"] == 1
        assert history["total_comments"] == 1
        assert "fetched_at" in history

    @responses.activate
    def test_get_user_history_empty(self):
        """Test user history with no content"""
        responses.add(
            responses.GET,
            "https://www.reddit.com/user/lurker/submitted.json?limit=100",
            json={"data": {"children": []}},
            status=200,
        )
        responses.add(
            responses.GET,
            "https://www.reddit.com/user/lurker/comments.json?limit=100",
            json={"data": {"children": []}},
            status=200,
        )

        scraper = RedditScraper(rate_limit_delay=0)
        history = scraper.get_user_history("lurker")

        assert history["username"] == "lurker"
        assert history["total_posts"] == 0
        assert history["total_comments"] == 0


class TestSearchPosts:
    """Tests for search_posts method"""

    @responses.activate
    def test_search_posts_success(self, sample_reddit_post_response):
        """Test successful search"""
        responses.add(
            responses.GET,
            "https://www.reddit.com/search.json?q=test&limit=100&sort=new",
            json=sample_reddit_post_response,
            status=200,
        )

        scraper = RedditScraper(rate_limit_delay=0)
        posts = scraper.search_posts("test")

        assert len(posts) == 2

    @responses.activate
    def test_search_posts_in_subreddit(self, sample_reddit_post_response):
        """Test search within specific subreddit"""
        responses.add(
            responses.GET,
            "https://www.reddit.com/r/specific_sub/search.json?q=test&restrict_sr=1&limit=100&sort=new",
            json=sample_reddit_post_response,
            status=200,
        )

        scraper = RedditScraper(rate_limit_delay=0)
        posts = scraper.search_posts("test", subreddit="specific_sub")

        assert len(posts) == 2

    @responses.activate
    def test_search_posts_error(self):
        """Test search error handling"""
        responses.add(
            responses.GET,
            "https://www.reddit.com/search.json?q=error&limit=100&sort=new",
            status=500,
        )

        scraper = RedditScraper(rate_limit_delay=0)
        posts = scraper.search_posts("error")

        assert posts == []


class TestCollectFromMultipleSubreddits:
    """Tests for collect_from_multiple_subreddits method"""

    @responses.activate
    def test_collect_from_multiple_subreddits(self, sample_reddit_post_response):
        """Test collecting from multiple subreddits"""
        for sub in ["sub1", "sub2", "sub3"]:
            responses.add(
                responses.GET,
                f"https://www.reddit.com/r/{sub}/new.json?limit=10",
                json=sample_reddit_post_response,
                status=200,
            )

        scraper = RedditScraper(rate_limit_delay=0)
        posts = scraper.collect_from_multiple_subreddits(
            ["sub1", "sub2", "sub3"], posts_per_subreddit=10
        )

        # 2 posts per subreddit * 3 subreddits = 6
        assert len(posts) == 6

    @responses.activate
    def test_collect_from_multiple_subreddits_partial_failure(
        self, sample_reddit_post_response
    ):
        """Test collection continues even if some subreddits fail"""
        responses.add(
            responses.GET,
            "https://www.reddit.com/r/good_sub/new.json?limit=10",
            json=sample_reddit_post_response,
            status=200,
        )
        responses.add(
            responses.GET,
            "https://www.reddit.com/r/bad_sub/new.json?limit=10",
            status=403,
        )

        scraper = RedditScraper(rate_limit_delay=0)
        posts = scraper.collect_from_multiple_subreddits(
            ["good_sub", "bad_sub"], posts_per_subreddit=10
        )

        # Only posts from good_sub
        assert len(posts) == 2


class TestRateLimiting:
    """Tests for rate limiting"""

    @responses.activate
    def test_rate_limiting_applied(self, sample_reddit_post_response):
        """Test that rate limiting delay is applied"""
        responses.add(
            responses.GET,
            "https://www.reddit.com/r/test/new.json?limit=100",
            json=sample_reddit_post_response,
            status=200,
        )

        scraper = RedditScraper(rate_limit_delay=0.1)

        with patch.object(scraper, "_wait") as mock_wait:
            scraper.get_subreddit_posts("test")
            mock_wait.assert_called_once()
