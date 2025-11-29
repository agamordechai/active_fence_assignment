"""Test fixtures and configuration"""
import pytest
from datetime import datetime
from typing import Generator
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from src.database.database import get_db
from src.database.models import Base, Post, User, Alert, MonitoringLog


# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """Create a fresh database session for each test"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Create a test client with overridden database dependency"""
    # Import app here to avoid import-time side effects
    from src.api import app

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    # Mock the init_db to prevent connecting to the real database
    with patch("src.api.init_db"):
        with TestClient(app) as test_client:
            yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data() -> dict:
    """Sample user data for testing (with datetime objects for CRUD tests)"""
    return {
        "username": "test_user",
        "account_created_utc": 1609459200.0,
        "account_created_date": datetime(2021, 1, 1, 0, 0, 0),
        "link_karma": 1000,
        "comment_karma": 500,
        "is_gold": False,
        "is_mod": False,
        "has_verified_email": True,
        "risk_assessment": {
            "risk_score": 25,
            "risk_level": "low",
            "hate_score": 10,
            "violence_score": 5,
            "explanation": "Some low-risk patterns detected",
            "flags": ["mild_language"]
        },
        "statistics": {
            "total_posts_analyzed": 10,
            "flagged_posts_count": 2,
            "flagged_comments_count": 1,
            "avg_post_risk_score": 15.5,
            "avg_comment_risk_score": 12.0,
            "max_risk_score_seen": 25
        }
    }


@pytest.fixture
def sample_user_data_api() -> dict:
    """Sample user data for API tests (with ISO string dates for JSON serialization)"""
    return {
        "username": "test_user",
        "account_created_utc": 1609459200.0,
        "account_created_date": "2021-01-01T00:00:00",
        "link_karma": 1000,
        "comment_karma": 500,
        "is_gold": False,
        "is_mod": False,
        "has_verified_email": True,
        "risk_assessment": {
            "risk_score": 25,
            "risk_level": "low",
            "hate_score": 10,
            "violence_score": 5,
            "explanation": "Some low-risk patterns detected",
            "flags": ["mild_language"]
        },
        "statistics": {
            "total_posts_analyzed": 10,
            "flagged_posts_count": 2,
            "flagged_comments_count": 1,
            "avg_post_risk_score": 15.5,
            "avg_comment_risk_score": 12.0,
            "max_risk_score_seen": 25
        }
    }


@pytest.fixture
def sample_post_data() -> dict:
    """Sample post data for testing (with datetime objects for CRUD tests)"""
    return {
        "id": "abc123",
        "title": "Test Post Title",
        "selftext": "This is the content of the test post",
        "author": "test_user",
        "subreddit": "test_subreddit",
        "created_utc": 1609459200.0,
        "created_date": datetime(2021, 1, 1, 0, 0, 0),
        "score": 100,
        "upvote_ratio": 0.95,
        "num_comments": 50,
        "permalink": "/r/test_subreddit/comments/abc123/test_post/",
        "url": "https://reddit.com/r/test_subreddit/comments/abc123/test_post/",
        "is_self": True,
        "over_18": False,
        "spoiler": False,
        "locked": False,
        "link_flair_text": "Discussion",
        "risk_assessment": {
            "risk_score": 15,
            "risk_level": "low",
            "hate_score": 5,
            "violence_score": 3,
            "explanation": "Minor concerns detected",
            "flags": ["some_flag"]
        }
    }


@pytest.fixture
def sample_post_data_api() -> dict:
    """Sample post data for API tests (with ISO string dates for JSON serialization)"""
    return {
        "id": "abc123",
        "title": "Test Post Title",
        "selftext": "This is the content of the test post",
        "author": "test_user",
        "subreddit": "test_subreddit",
        "created_utc": 1609459200.0,
        "created_date": "2021-01-01T00:00:00",
        "score": 100,
        "upvote_ratio": 0.95,
        "num_comments": 50,
        "permalink": "/r/test_subreddit/comments/abc123/test_post/",
        "url": "https://reddit.com/r/test_subreddit/comments/abc123/test_post/",
        "is_self": True,
        "over_18": False,
        "spoiler": False,
        "locked": False,
        "link_flair_text": "Discussion",
        "risk_assessment": {
            "risk_score": 15,
            "risk_level": "low",
            "hate_score": 5,
            "violence_score": 3,
            "explanation": "Minor concerns detected",
            "flags": ["some_flag"]
        }
    }


@pytest.fixture
def sample_high_risk_user_data() -> dict:
    """Sample high-risk user data for testing (with datetime objects)"""
    return {
        "username": "high_risk_user",
        "account_created_utc": 1609459200.0,
        "account_created_date": datetime(2021, 1, 1, 0, 0, 0),
        "link_karma": 100,
        "comment_karma": 50,
        "is_gold": False,
        "is_mod": False,
        "has_verified_email": False,
        "risk_assessment": {
            "risk_score": 75,
            "risk_level": "high",
            "hate_score": 60,
            "violence_score": 40,
            "explanation": "High-risk patterns detected",
            "flags": ["hate_speech", "threats"]
        },
        "statistics": {
            "total_posts_analyzed": 50,
            "flagged_posts_count": 20,
            "flagged_comments_count": 15,
            "avg_post_risk_score": 65.0,
            "avg_comment_risk_score": 55.0,
            "max_risk_score_seen": 90
        }
    }


@pytest.fixture
def sample_high_risk_user_data_api() -> dict:
    """Sample high-risk user data for API tests (with ISO string dates)"""
    return {
        "username": "high_risk_user",
        "account_created_utc": 1609459200.0,
        "account_created_date": "2021-01-01T00:00:00",
        "link_karma": 100,
        "comment_karma": 50,
        "is_gold": False,
        "is_mod": False,
        "has_verified_email": False,
        "risk_assessment": {
            "risk_score": 75,
            "risk_level": "high",
            "hate_score": 60,
            "violence_score": 40,
            "explanation": "High-risk patterns detected",
            "flags": ["hate_speech", "threats"]
        },
        "statistics": {
            "total_posts_analyzed": 50,
            "flagged_posts_count": 20,
            "flagged_comments_count": 15,
            "avg_post_risk_score": 65.0,
            "avg_comment_risk_score": 55.0,
            "max_risk_score_seen": 90
        }
    }


@pytest.fixture
def sample_high_risk_post_data() -> dict:
    """Sample high-risk post data for testing (with datetime objects for CRUD tests)"""
    return {
        "id": "high_risk_post_123",
        "title": "High Risk Post",
        "selftext": "High risk content",
        "author": "test_user",
        "subreddit": "controversial_sub",
        "created_utc": 1609459200.0,
        "created_date": datetime(2021, 1, 1, 0, 0, 0),
        "score": 10,
        "upvote_ratio": 0.5,
        "num_comments": 100,
        "permalink": "/r/controversial_sub/comments/high_risk_post_123/",
        "is_self": True,
        "over_18": True,
        "spoiler": False,
        "locked": True,
        "risk_assessment": {
            "risk_score": 80,
            "risk_level": "high",
            "hate_score": 70,
            "violence_score": 50,
            "explanation": "High-risk content detected",
            "flags": ["hate_speech", "violence"]
        }
    }


@pytest.fixture
def sample_high_risk_post_data_api() -> dict:
    """Sample high-risk post data for API tests (with ISO string dates for JSON serialization)"""
    return {
        "id": "high_risk_post_123",
        "title": "High Risk Post",
        "selftext": "High risk content",
        "author": "test_user",
        "subreddit": "controversial_sub",
        "created_utc": 1609459200.0,
        "created_date": "2021-01-01T00:00:00",
        "score": 10,
        "upvote_ratio": 0.5,
        "num_comments": 100,
        "permalink": "/r/controversial_sub/comments/high_risk_post_123/",
        "is_self": True,
        "over_18": True,
        "spoiler": False,
        "locked": True,
        "risk_assessment": {
            "risk_score": 80,
            "risk_level": "high",
            "hate_score": 70,
            "violence_score": 50,
            "explanation": "High-risk content detected",
            "flags": ["hate_speech", "violence"]
        }
    }


@pytest.fixture
def db_with_user(db_session: Session, sample_user_data: dict) -> tuple[Session, User]:
    """Create a database session with a pre-existing user"""
    user = User(
        username=sample_user_data["username"],
        account_created_utc=sample_user_data["account_created_utc"],
        link_karma=sample_user_data["link_karma"],
        comment_karma=sample_user_data["comment_karma"],
        is_gold=sample_user_data["is_gold"],
        is_mod=sample_user_data["is_mod"],
        has_verified_email=sample_user_data["has_verified_email"],
        risk_score=sample_user_data["risk_assessment"]["risk_score"],
        risk_level=sample_user_data["risk_assessment"]["risk_level"],
        hate_score=sample_user_data["risk_assessment"]["hate_score"],
        violence_score=sample_user_data["risk_assessment"]["violence_score"],
        risk_explanation=sample_user_data["risk_assessment"]["explanation"],
        risk_factors=[{"type": "mild_language", "severity": "low"}],
        total_posts_analyzed=sample_user_data["statistics"]["total_posts_analyzed"],
        flagged_posts_count=sample_user_data["statistics"]["flagged_posts_count"],
        flagged_comments_count=sample_user_data["statistics"]["flagged_comments_count"],
        avg_post_risk_score=sample_user_data["statistics"]["avg_post_risk_score"],
        avg_comment_risk_score=sample_user_data["statistics"]["avg_comment_risk_score"],
        max_risk_score_seen=sample_user_data["statistics"]["max_risk_score_seen"],
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return db_session, user


@pytest.fixture
def db_with_post(db_with_user: tuple[Session, User], sample_post_data: dict) -> tuple[Session, Post]:
    """Create a database session with a pre-existing post (and user)"""
    db_session, user = db_with_user
    post = Post(
        id=sample_post_data["id"],
        title=sample_post_data["title"],
        selftext=sample_post_data["selftext"],
        author=sample_post_data["author"],
        subreddit=sample_post_data["subreddit"],
        created_utc=sample_post_data["created_utc"],
        created_date=sample_post_data["created_date"],
        score=sample_post_data["score"],
        upvote_ratio=sample_post_data["upvote_ratio"],
        num_comments=sample_post_data["num_comments"],
        permalink=sample_post_data["permalink"],
        url=sample_post_data["url"],
        is_self=sample_post_data["is_self"],
        over_18=sample_post_data["over_18"],
        spoiler=sample_post_data["spoiler"],
        locked=sample_post_data["locked"],
        link_flair_text=sample_post_data["link_flair_text"],
        risk_score=sample_post_data["risk_assessment"]["risk_score"],
        risk_level=sample_post_data["risk_assessment"]["risk_level"],
        hate_score=sample_post_data["risk_assessment"]["hate_score"],
        violence_score=sample_post_data["risk_assessment"]["violence_score"],
        risk_explanation=sample_post_data["risk_assessment"]["explanation"],
        risk_flags=sample_post_data["risk_assessment"]["flags"],
    )
    db_session.add(post)
    db_session.commit()
    db_session.refresh(post)
    return db_session, post


# ==================== Alert Fixtures ====================

@pytest.fixture
def sample_alert_data() -> dict:
    """Sample alert data for testing"""
    return {
        "username": "test_user",
        "post_id": "abc123",
        "alert_type": "high_risk_content",
        "severity": "high",
        "risk_score": 75,
        "description": "High-risk content detected in post",
        "details": {"flags": ["hate_speech"], "context": "Detected offensive language"}
    }


@pytest.fixture
def sample_alert_data_api() -> dict:
    """Sample alert data for API tests"""
    return {
        "username": "test_user",
        "post_id": "abc123",
        "alert_type": "high_risk_content",
        "severity": "high",
        "risk_score": 75,
        "description": "High-risk content detected in post",
        "details": {"flags": ["hate_speech"], "context": "Detected offensive language"}
    }


@pytest.fixture
def db_with_alert(db_with_user: tuple[Session, User], sample_alert_data: dict) -> tuple[Session, Alert]:
    """Create a database session with a pre-existing alert (and user)"""
    db_session, user = db_with_user
    alert = Alert(
        username=sample_alert_data["username"],
        post_id=sample_alert_data["post_id"],
        alert_type=sample_alert_data["alert_type"],
        severity=sample_alert_data["severity"],
        risk_score=sample_alert_data["risk_score"],
        description=sample_alert_data["description"],
        details=sample_alert_data["details"],
        status="new"
    )
    db_session.add(alert)
    db_session.commit()
    db_session.refresh(alert)
    return db_session, alert


# ==================== Monitoring Log Fixtures ====================

@pytest.fixture
def sample_monitoring_log_data() -> dict:
    """Sample monitoring log data for testing"""
    return {
        "username": "test_user",
        "activity_type": "post_review",
        "description": "Reviewed user posts for potential violations",
        "findings": {"posts_reviewed": 10, "flagged": 2, "action_taken": "none"}
    }


@pytest.fixture
def sample_monitoring_log_data_api() -> dict:
    """Sample monitoring log data for API tests"""
    return {
        "username": "test_user",
        "activity_type": "post_review",
        "description": "Reviewed user posts for potential violations",
        "findings": {"posts_reviewed": 10, "flagged": 2, "action_taken": "none"}
    }


@pytest.fixture
def db_with_monitoring_log(db_with_user: tuple[Session, User], sample_monitoring_log_data: dict) -> tuple[Session, MonitoringLog]:
    """Create a database session with a pre-existing monitoring log (and user)"""
    db_session, user = db_with_user
    log = MonitoringLog(
        username=sample_monitoring_log_data["username"],
        activity_type=sample_monitoring_log_data["activity_type"],
        description=sample_monitoring_log_data["description"],
        findings=sample_monitoring_log_data["findings"]
    )
    db_session.add(log)
    db_session.commit()
    db_session.refresh(log)
    return db_session, log
