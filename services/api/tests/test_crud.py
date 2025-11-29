"""Tests for CRUD operations"""
import copy
import pytest
from datetime import datetime
from sqlalchemy.orm import Session

from src.database import crud
from src.database.models import User, Post, Alert, MonitoringLog


class TestPostCRUD:
    """Tests for Post CRUD operations"""

    def test_create_post(self, db_with_user: tuple[Session, User], sample_post_data: dict):
        """Test creating a post via CRUD"""
        db_session, user = db_with_user
        post_data = copy.deepcopy(sample_post_data)
        expected_risk_score = post_data["risk_assessment"]["risk_score"]
        expected_risk_level = post_data["risk_assessment"]["risk_level"]
        post = crud.create_post(db_session, post_data)

        assert post.id == sample_post_data["id"]
        assert post.title == sample_post_data["title"]
        assert post.author == sample_post_data["author"]
        assert post.risk_score == expected_risk_score
        assert post.risk_level == expected_risk_level

    def test_create_post_without_risk_assessment(
        self, db_with_user: tuple[Session, User], sample_post_data: dict
    ):
        """Test creating a post without risk assessment"""
        db_session, user = db_with_user
        post_data = copy.deepcopy(sample_post_data)
        del post_data["risk_assessment"]

        post = crud.create_post(db_session, post_data)

        assert post.id == sample_post_data["id"]
        assert post.risk_score == 0
        assert post.risk_level == "minimal"

    def test_get_post(self, db_with_post: tuple[Session, Post]):
        """Test getting a post by ID"""
        db_session, existing_post = db_with_post
        post = crud.get_post(db_session, existing_post.id)

        assert post is not None
        assert post.id == existing_post.id
        assert post.title == existing_post.title

    def test_get_post_not_found(self, db_session: Session):
        """Test getting a non-existent post"""
        post = crud.get_post(db_session, "nonexistent")
        assert post is None

    def test_get_posts(self, db_with_post: tuple[Session, Post]):
        """Test getting all posts"""
        db_session, _ = db_with_post
        posts = crud.get_posts(db_session)

        assert len(posts) == 1

    def test_get_posts_with_filters(
        self, db_with_user: tuple[Session, User], sample_post_data: dict
    ):
        """Test getting posts with filters"""
        db_session, user = db_with_user

        # Create multiple posts
        post1_data = copy.deepcopy(sample_post_data)
        post1_data["id"] = "post1"
        post1_data["subreddit"] = "subreddit_a"

        post2_data = copy.deepcopy(sample_post_data)
        post2_data["id"] = "post2"
        post2_data["subreddit"] = "subreddit_b"

        crud.create_post(db_session, post1_data)
        crud.create_post(db_session, post2_data)

        # Filter by subreddit
        posts = crud.get_posts(db_session, subreddit="subreddit_a")
        assert len(posts) == 1
        assert posts[0].subreddit == "subreddit_a"

        # Filter by author
        posts = crud.get_posts(db_session, author="test_user")
        assert len(posts) == 2

    def test_get_posts_pagination(
        self, db_with_user: tuple[Session, User], sample_post_data: dict
    ):
        """Test posts pagination"""
        db_session, user = db_with_user

        # Create multiple posts
        for i in range(5):
            post_data = copy.deepcopy(sample_post_data)
            post_data["id"] = f"post_{i}"
            crud.create_post(db_session, post_data)

        # Test pagination
        posts = crud.get_posts(db_session, skip=0, limit=2)
        assert len(posts) == 2

        posts = crud.get_posts(db_session, skip=2, limit=2)
        assert len(posts) == 2

        posts = crud.get_posts(db_session, skip=4, limit=2)
        assert len(posts) == 1

    def test_get_high_risk_posts(
        self, db_with_user: tuple[Session, User], sample_post_data: dict
    ):
        """Test getting high-risk posts"""
        db_session, user = db_with_user

        # Create a low-risk post
        low_risk = copy.deepcopy(sample_post_data)
        low_risk["id"] = "low_risk"
        low_risk["risk_assessment"]["risk_score"] = 10
        crud.create_post(db_session, low_risk)

        # Create a high-risk post
        high_risk = copy.deepcopy(sample_post_data)
        high_risk["id"] = "high_risk"
        high_risk["risk_assessment"]["risk_score"] = 80
        crud.create_post(db_session, high_risk)

        # Get high-risk posts
        posts = crud.get_high_risk_posts(db_session, min_score=50)
        assert len(posts) == 1
        assert posts[0].id == "high_risk"

    def test_update_post(self, db_with_post: tuple[Session, Post]):
        """Test updating a post"""
        db_session, post = db_with_post

        updated = crud.update_post(
            db_session,
            post.id,
            {"risk_score": 99, "risk_level": "critical"}
        )

        assert updated is not None
        assert updated.risk_score == 99
        assert updated.risk_level == "critical"

    def test_update_post_not_found(self, db_session: Session):
        """Test updating a non-existent post"""
        updated = crud.update_post(db_session, "nonexistent", {"risk_score": 50})
        assert updated is None

    def test_delete_post(self, db_with_post: tuple[Session, Post]):
        """Test deleting a post"""
        db_session, post = db_with_post

        result = crud.delete_post(db_session, post.id)
        assert result is True

        # Verify deletion
        deleted = crud.get_post(db_session, post.id)
        assert deleted is None

    def test_delete_post_not_found(self, db_session: Session):
        """Test deleting a non-existent post"""
        result = crud.delete_post(db_session, "nonexistent")
        assert result is False


class TestUserCRUD:
    """Tests for User CRUD operations"""

    def test_create_user(self, db_session: Session, sample_user_data: dict):
        """Test creating a user via CRUD"""
        user_data = copy.deepcopy(sample_user_data)
        expected_risk_score = user_data["risk_assessment"]["risk_score"]
        expected_posts_analyzed = user_data["statistics"]["total_posts_analyzed"]
        user = crud.create_user(db_session, user_data)

        assert user.username == sample_user_data["username"]
        assert user.risk_score == expected_risk_score
        assert user.total_posts_analyzed == expected_posts_analyzed

    def test_create_user_without_optional_fields(self, db_session: Session):
        """Test creating a user without optional fields"""
        user_data = {
            "username": "minimal_user",
            "link_karma": 100,
            "comment_karma": 50,
        }
        user = crud.create_user(db_session, user_data)

        assert user.username == "minimal_user"
        assert user.risk_score == 0
        assert user.risk_level == "minimal"

    def test_get_user(self, db_with_user: tuple[Session, User]):
        """Test getting a user by username"""
        db_session, existing_user = db_with_user
        user = crud.get_user(db_session, existing_user.username)

        assert user is not None
        assert user.username == existing_user.username

    def test_get_user_not_found(self, db_session: Session):
        """Test getting a non-existent user"""
        user = crud.get_user(db_session, "nonexistent")
        assert user is None

    def test_get_users(self, db_with_user: tuple[Session, User]):
        """Test getting all users"""
        db_session, _ = db_with_user
        users = crud.get_users(db_session)

        assert len(users) == 1

    def test_get_users_with_filters(self, db_session: Session, sample_user_data: dict):
        """Test getting users with filters"""
        # Create users with different risk levels
        low_risk = copy.deepcopy(sample_user_data)
        low_risk["username"] = "low_risk_user"
        low_risk["risk_assessment"]["risk_score"] = 10
        low_risk["risk_assessment"]["risk_level"] = "low"
        crud.create_user(db_session, low_risk)

        high_risk = copy.deepcopy(sample_user_data)
        high_risk["username"] = "high_risk_user"
        high_risk["risk_assessment"]["risk_score"] = 80
        high_risk["risk_assessment"]["risk_level"] = "high"
        crud.create_user(db_session, high_risk)

        # Filter by min_risk_score
        users = crud.get_users(db_session, min_risk_score=50)
        assert len(users) == 1
        assert users[0].username == "high_risk_user"

        # Filter by risk_level
        users = crud.get_users(db_session, risk_level="low")
        assert len(users) == 1
        assert users[0].username == "low_risk_user"

    def test_get_users_ordering(self, db_session: Session, sample_user_data: dict):
        """Test users ordering"""
        # Create multiple users
        for i, score in enumerate([30, 70, 50]):
            user_data = copy.deepcopy(sample_user_data)
            user_data["username"] = f"user_{i}"
            user_data["risk_assessment"]["risk_score"] = score
            crud.create_user(db_session, user_data)

        # Order by risk_score (default, descending)
        users = crud.get_users(db_session, order_by="risk_score")
        assert users[0].risk_score >= users[1].risk_score >= users[2].risk_score

    def test_get_high_risk_users(self, db_session: Session, sample_user_data: dict):
        """Test getting high-risk users"""
        # Create a low-risk user
        low_risk = copy.deepcopy(sample_user_data)
        low_risk["username"] = "low_risk"
        low_risk["risk_assessment"]["risk_score"] = 10
        crud.create_user(db_session, low_risk)

        # Create a high-risk user
        high_risk = copy.deepcopy(sample_user_data)
        high_risk["username"] = "high_risk"
        high_risk["risk_assessment"]["risk_score"] = 80
        crud.create_user(db_session, high_risk)

        users = crud.get_high_risk_users(db_session, min_score=50)
        assert len(users) == 1
        assert users[0].username == "high_risk"

    def test_get_monitored_users(self, db_session: Session, sample_user_data: dict):
        """Test getting monitored users"""
        # Create non-monitored user
        user1 = copy.deepcopy(sample_user_data)
        user1["username"] = "user1"
        crud.create_user(db_session, user1)

        # Create monitored user
        user2 = copy.deepcopy(sample_user_data)
        user2["username"] = "user2"
        crud.create_user(db_session, user2)
        crud.update_user(db_session, "user2", {"is_monitored": True})

        monitored = crud.get_monitored_users(db_session)
        assert len(monitored) == 1
        assert monitored[0].username == "user2"

    def test_update_user(self, db_with_user: tuple[Session, User]):
        """Test updating a user"""
        db_session, user = db_with_user

        updated = crud.update_user(
            db_session,
            user.username,
            {"risk_score": 99, "is_monitored": True}
        )

        assert updated is not None
        assert updated.risk_score == 99
        assert updated.is_monitored is True

    def test_update_user_not_found(self, db_session: Session):
        """Test updating a non-existent user"""
        updated = crud.update_user(db_session, "nonexistent", {"risk_score": 50})
        assert updated is None

    def test_delete_user(self, db_with_user: tuple[Session, User]):
        """Test deleting a user"""
        db_session, user = db_with_user

        result = crud.delete_user(db_session, user.username)
        assert result is True

        # Verify deletion
        deleted = crud.get_user(db_session, user.username)
        assert deleted is None

    def test_delete_user_not_found(self, db_session: Session):
        """Test deleting a non-existent user"""
        result = crud.delete_user(db_session, "nonexistent")
        assert result is False


class TestAlertCRUD:
    """Tests for Alert CRUD operations"""

    def test_create_alert(self, db_with_user: tuple[Session, User]):
        """Test creating an alert"""
        db_session, user = db_with_user

        alert_data = {
            "username": user.username,
            "alert_type": "high_risk_post",
            "severity": "high",
            "risk_score": 80,
            "description": "User posted high-risk content",
            "details": {"post_id": "abc123"}
        }

        alert = crud.create_alert(db_session, alert_data)

        assert alert.id is not None
        assert alert.username == user.username
        assert alert.severity == "high"
        assert alert.status == "new"

    def test_get_alert(self, db_with_user: tuple[Session, User]):
        """Test getting an alert by ID"""
        db_session, user = db_with_user

        alert_data = {
            "username": user.username,
            "alert_type": "test",
            "severity": "low",
            "risk_score": 20,
            "description": "Test alert"
        }
        created = crud.create_alert(db_session, alert_data)

        alert = crud.get_alert(db_session, created.id)
        assert alert is not None
        assert alert.id == created.id

    def test_get_alerts_with_filters(self, db_with_user: tuple[Session, User]):
        """Test getting alerts with filters"""
        db_session, user = db_with_user

        # Create multiple alerts
        for severity in ["low", "high", "critical"]:
            alert_data = {
                "username": user.username,
                "alert_type": "test",
                "severity": severity,
                "risk_score": 50,
                "description": f"{severity} alert"
            }
            crud.create_alert(db_session, alert_data)

        # Filter by severity
        alerts = crud.get_alerts(db_session, severity="high")
        assert len(alerts) == 1
        assert alerts[0].severity == "high"

        # Filter by username
        alerts = crud.get_alerts(db_session, username=user.username)
        assert len(alerts) == 3

    def test_update_alert(self, db_with_user: tuple[Session, User]):
        """Test updating an alert"""
        db_session, user = db_with_user

        alert_data = {
            "username": user.username,
            "alert_type": "test",
            "severity": "high",
            "risk_score": 80,
            "description": "Test alert"
        }
        alert = crud.create_alert(db_session, alert_data)

        updated = crud.update_alert(
            db_session,
            alert.id,
            {"status": "reviewed", "reviewed_by": "admin"}
        )

        assert updated is not None
        assert updated.status == "reviewed"
        assert updated.reviewed_by == "admin"

    def test_delete_alert(self, db_with_user: tuple[Session, User]):
        """Test deleting an alert"""
        db_session, user = db_with_user

        alert_data = {
            "username": user.username,
            "alert_type": "test",
            "severity": "low",
            "risk_score": 20,
            "description": "Test alert"
        }
        alert = crud.create_alert(db_session, alert_data)

        result = crud.delete_alert(db_session, alert.id)
        assert result is True

        # Verify deletion
        deleted = crud.get_alert(db_session, alert.id)
        assert deleted is None


class TestMonitoringLogCRUD:
    """Tests for MonitoringLog CRUD operations"""

    def test_create_monitoring_log(self, db_with_user: tuple[Session, User]):
        """Test creating a monitoring log entry"""
        db_session, user = db_with_user

        log_data = {
            "username": user.username,
            "activity_type": "scan",
            "description": "Routine scan completed",
            "findings": {"posts_scanned": 10, "issues_found": 2}
        }

        log = crud.create_monitoring_log(db_session, log_data)

        assert log.id is not None
        assert log.username == user.username
        assert log.activity_type == "scan"

    def test_get_monitoring_logs(self, db_with_user: tuple[Session, User]):
        """Test getting monitoring logs"""
        db_session, user = db_with_user

        # Create multiple logs
        for activity in ["scan", "alert", "update"]:
            log_data = {
                "username": user.username,
                "activity_type": activity,
                "description": f"{activity} activity"
            }
            crud.create_monitoring_log(db_session, log_data)

        # Get all logs for user
        logs = crud.get_monitoring_logs(db_session, username=user.username)
        assert len(logs) == 3

        # Filter by activity_type
        logs = crud.get_monitoring_logs(db_session, activity_type="scan")
        assert len(logs) == 1
        assert logs[0].activity_type == "scan"


class TestStatistics:
    """Tests for statistics function"""

    def test_get_statistics_empty(self, db_session: Session):
        """Test statistics with empty database"""
        stats = crud.get_statistics(db_session)

        assert stats["total_posts"] == 0
        assert stats["total_users"] == 0
        assert stats["high_risk_posts"] == 0
        assert stats["high_risk_users"] == 0

    def test_get_statistics_with_data(
        self, db_with_user: tuple[Session, User], sample_post_data: dict
    ):
        """Test statistics with data"""
        db_session, user = db_with_user

        # Create some posts
        for i, risk_level in enumerate(["minimal", "medium", "high", "critical"]):
            post_data = copy.deepcopy(sample_post_data)
            post_data["id"] = f"post_{i}"
            post_data["risk_assessment"]["risk_level"] = risk_level
            post_data["risk_assessment"]["risk_score"] = i * 25
            crud.create_post(db_session, post_data)

        stats = crud.get_statistics(db_session)

        assert stats["total_posts"] == 4
        assert stats["total_users"] == 1
        assert "posts_by_risk" in stats
        assert "users_by_risk" in stats
        assert "timestamp" in stats
