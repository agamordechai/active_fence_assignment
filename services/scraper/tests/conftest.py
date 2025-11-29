"""Test fixtures and configuration for scraper tests"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
import json
from pathlib import Path


@pytest.fixture
def sample_reddit_post_response():
    """Sample Reddit JSON API response for a subreddit"""
    return {
        "data": {
            "children": [
                {
                    "data": {
                        "id": "abc123",
                        "title": "Test Post Title",
                        "selftext": "This is the content of the test post",
                        "author": "test_user",
                        "subreddit": "test_subreddit",
                        "created_utc": 1609459200.0,
                        "score": 100,
                        "upvote_ratio": 0.95,
                        "num_comments": 50,
                        "permalink": "/r/test_subreddit/comments/abc123/test_post/",
                        "url": "https://reddit.com/r/test_subreddit/comments/abc123/",
                        "is_self": True,
                        "over_18": False,
                        "spoiler": False,
                        "locked": False,
                        "link_flair_text": "Discussion",
                    }
                },
                {
                    "data": {
                        "id": "def456",
                        "title": "Another Test Post",
                        "selftext": "More content here",
                        "author": "another_user",
                        "subreddit": "test_subreddit",
                        "created_utc": 1609545600.0,
                        "score": 50,
                        "upvote_ratio": 0.85,
                        "num_comments": 25,
                        "permalink": "/r/test_subreddit/comments/def456/another_test/",
                        "url": "https://reddit.com/r/test_subreddit/comments/def456/",
                        "is_self": True,
                        "over_18": False,
                        "spoiler": False,
                        "locked": False,
                        "link_flair_text": None,
                    }
                },
            ]
        }
    }


@pytest.fixture
def sample_user_posts_response():
    """Sample Reddit JSON API response for user posts"""
    return {
        "data": {
            "children": [
                {
                    "data": {
                        "id": "user_post_1",
                        "title": "User's Post",
                        "selftext": "User post content",
                        "subreddit": "some_subreddit",
                        "created_utc": datetime.now().timestamp() - 86400,  # 1 day ago
                        "score": 10,
                        "num_comments": 5,
                        "permalink": "/r/some_subreddit/comments/user_post_1/",
                    }
                }
            ]
        }
    }


@pytest.fixture
def sample_user_comments_response():
    """Sample Reddit JSON API response for user comments"""
    return {
        "data": {
            "children": [
                {
                    "data": {
                        "id": "comment_1",
                        "body": "This is a test comment",
                        "subreddit": "some_subreddit",
                        "created_utc": datetime.now().timestamp() - 43200,  # 12 hours ago
                        "score": 5,
                        "permalink": "/r/some_subreddit/comments/xyz/comment/comment_1/",
                        "link_title": "Original Post Title",
                    }
                }
            ]
        }
    }


@pytest.fixture
def sample_raw_user_data():
    """Sample raw user data from scraper"""
    now = datetime.now()
    recent_timestamp = (now - timedelta(days=30)).timestamp()
    old_timestamp = (now - timedelta(days=90)).timestamp()

    return {
        "username": "test_user",
        "posts": [
            {
                "id": "post1",
                "title": "Recent Post",
                "selftext": "Recent content",
                "subreddit": "subreddit_a",
                "created_utc": recent_timestamp,
                "score": 100,
            },
            {
                "id": "post2",
                "title": "Old Post",
                "selftext": "Old content",
                "subreddit": "subreddit_b",
                "created_utc": old_timestamp,
                "score": 50,
            },
        ],
        "comments": [
            {
                "id": "comment1",
                "body": "Recent comment",
                "subreddit": "subreddit_a",
                "created_utc": recent_timestamp,
                "score": 10,
            },
            {
                "id": "comment2",
                "body": "Old comment",
                "subreddit": "subreddit_c",
                "created_utc": old_timestamp,
                "score": 5,
            },
        ],
        "fetched_at": now.isoformat(),
    }


@pytest.fixture
def sample_enriched_user_data():
    """Sample enriched user data"""
    return {
        "username": "test_user",
        "enrichment_timestamp": datetime.now().isoformat(),
        "activity_metrics": {
            "total_posts": 5,
            "total_comments": 10,
            "recent_posts_2m": 3,
            "recent_comments_2m": 7,
            "total_recent_activity": 10,
            "activity_per_day": 0.17,
            "avg_post_score": 50.0,
            "avg_comment_score": 10.0,
        },
        "subreddit_diversity": {
            "unique_subreddits_count": 3,
            "subreddits": ["subreddit_a", "subreddit_b", "subreddit_c"],
            "primary_subreddits_posted": ["subreddit_a"],
            "primary_subreddits_commented": ["subreddit_b", "subreddit_c"],
        },
        "content": {
            "all_text": [
                "Normal post title",
                "Just a regular comment",
                "Another harmless post",
            ],
            "total_text_items": 3,
        },
        "raw_data": {
            "posts": [],
            "comments": [],
        },
        "profile_status": "moderate_activity",
    }


@pytest.fixture
def sample_high_risk_user_data():
    """Sample enriched user data with potentially offensive content"""
    return {
        "username": "risky_user",
        "enrichment_timestamp": datetime.now().isoformat(),
        "activity_metrics": {
            "total_posts": 20,
            "total_comments": 50,
            "recent_posts_2m": 15,
            "recent_comments_2m": 40,
            "total_recent_activity": 55,
            "activity_per_day": 0.92,
            "avg_post_score": -5.0,
            "avg_comment_score": -10.0,
        },
        "subreddit_diversity": {
            "unique_subreddits_count": 5,
            "subreddits": ["controversial_sub", "debate_sub"],
            "primary_subreddits_posted": ["controversial_sub"],
            "primary_subreddits_commented": ["debate_sub"],
        },
        "content": {
            "all_text": [
                "I hate everyone",
                "Kill them all",
                "Normal post here",
            ],
            "total_text_items": 3,
        },
        "raw_data": {
            "posts": [],
            "comments": [],
        },
        "profile_status": "high_activity",
    }


@pytest.fixture
def sample_post():
    """Sample post dictionary"""
    return {
        "id": "test_post_123",
        "title": "Test Post Title",
        "selftext": "This is the body content of the post",
        "author": "test_user",
        "subreddit": "test_subreddit",
        "created_utc": 1609459200.0,
        "created_date": "2021-01-01T00:00:00",
        "score": 100,
        "upvote_ratio": 0.95,
        "num_comments": 50,
        "permalink": "/r/test_subreddit/comments/test_post_123/",
        "url": "https://reddit.com/r/test_subreddit/comments/test_post_123/",
        "is_self": True,
        "over_18": False,
        "spoiler": False,
        "locked": False,
    }


@pytest.fixture
def sample_scored_post():
    """Sample scored post"""
    return {
        "id": "scored_post_123",
        "title": "Scored Post",
        "selftext": "Content here",
        "author": "test_user",
        "subreddit": "test_subreddit",
        "created_utc": 1609459200.0,
        "created_date": "2021-01-01T00:00:00",
        "score": 100,
        "upvote_ratio": 0.95,
        "num_comments": 50,
        "permalink": "/r/test_subreddit/comments/scored_post_123/",
        "url": "https://reddit.com/r/test_subreddit/comments/scored_post_123/",
        "is_self": True,
        "over_18": False,
        "spoiler": False,
        "locked": False,
        "risk_assessment": {
            "risk_score": 15,
            "risk_level": "low",
            "hate_score": 10,
            "violence_score": 5,
            "explanation": "Low risk content",
            "flags": [],
        },
        "scored_at": "2021-01-01T12:00:00",
    }


@pytest.fixture
def sample_scored_user():
    """Sample scored user"""
    return {
        "username": "scored_user",
        "activity_metrics": {"total_posts": 10},
        "risk_assessment": {
            "overall_risk_score": 25,
            "risk_level": "low",
            "average_hate_score": 15,
            "average_violence_score": 10,
            "high_risk_content_count": 1,
            "total_content_analyzed": 10,
            "explanation": "Low risk user",
            "scored_at": "2021-01-01T12:00:00",
        },
    }


@pytest.fixture
def mock_lexicon(tmp_path):
    """Create a mock HurtLex lexicon file for testing"""
    lexicon = {
        "source": "Test Lexicon",
        "hate_keywords": {
            "extreme": ["hate_extreme_word"],
            "high": ["hate_high_word"],
            "medium": ["hate_medium_word"],
        },
        "violence_keywords": {
            "extreme": ["kill", "murder"],
            "high": ["attack", "destroy"],
            "medium": ["fight", "hurt"],
        },
        "slur_patterns": [r"test_slur_\w+"],
        "context_indicators": {
            "discussion": ["discussing", "talking about", "article about"],
            "quotation": ["he said", "she said", "quote"],
            "negation": ["not", "never", "don't"],
        },
    }

    lexicon_path = tmp_path / "hurtlex_processed.json"
    with open(lexicon_path, "w") as f:
        json.dump(lexicon, f)

    return lexicon_path


@pytest.fixture
def mock_api_response():
    """Mock successful API response"""
    return {
        "created": 5,
        "skipped": 2,
        "errors": [],
    }
