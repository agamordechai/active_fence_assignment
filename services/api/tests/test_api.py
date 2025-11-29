"""Tests for API endpoints"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.database.models import User, Post, Alert, MonitoringLog


class TestHealthEndpoint:
    """Tests for the health check endpoint"""

    def test_health_check(self, client: TestClient):
        """Test health check returns healthy status"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestStatisticsEndpoint:
    """Tests for the statistics endpoint"""

    def test_get_statistics_empty_db(self, client: TestClient):
        """Test statistics with empty database"""
        response = client.get("/statistics")
        assert response.status_code == 200
        data = response.json()
        assert data["total_posts"] == 0
        assert data["total_users"] == 0
        assert data["high_risk_posts"] == 0
        assert data["high_risk_users"] == 0
        assert "timestamp" in data

    def test_get_statistics_with_data(
        self, client: TestClient, db_with_post: tuple[Session, Post]
    ):
        """Test statistics with data in database"""
        response = client.get("/statistics")
        assert response.status_code == 200
        data = response.json()
        assert data["total_posts"] == 1
        assert data["total_users"] == 1


class TestPostEndpoints:
    """Tests for post-related endpoints"""

    def test_create_post(
        self, client: TestClient, db_with_user: tuple[Session, User], sample_post_data_api: dict
    ):
        """Test creating a new post"""
        response = client.post("/posts", json=sample_post_data_api)
        assert response.status_code == 201
        data = response.json()
        assert data["id"] == sample_post_data_api["id"]
        assert data["title"] == sample_post_data_api["title"]
        assert data["author"] == sample_post_data_api["author"]
        assert data["risk_score"] == sample_post_data_api["risk_assessment"]["risk_score"]

    def test_create_post_duplicate(
        self, client: TestClient, db_with_post: tuple[Session, Post], sample_post_data_api: dict
    ):
        """Test creating a duplicate post returns error"""
        response = client.post("/posts", json=sample_post_data_api)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_get_posts_empty(self, client: TestClient):
        """Test getting posts when database is empty"""
        response = client.get("/posts")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_posts_with_data(self, client: TestClient, db_with_post: tuple[Session, Post]):
        """Test getting posts with data"""
        response = client.get("/posts")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "abc123"

    def test_get_posts_with_filters(
        self, client: TestClient, db_with_post: tuple[Session, Post]
    ):
        """Test getting posts with various filters"""
        # Filter by subreddit
        response = client.get("/posts", params={"subreddit": "test_subreddit"})
        assert response.status_code == 200
        assert len(response.json()) == 1

        # Filter by non-existent subreddit
        response = client.get("/posts", params={"subreddit": "nonexistent"})
        assert response.status_code == 200
        assert len(response.json()) == 0

        # Filter by author
        response = client.get("/posts", params={"author": "test_user"})
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_get_posts_pagination(
        self, client: TestClient, db_with_post: tuple[Session, Post]
    ):
        """Test posts pagination"""
        response = client.get("/posts", params={"skip": 0, "limit": 10})
        assert response.status_code == 200

        response = client.get("/posts", params={"skip": 100, "limit": 10})
        assert response.status_code == 200
        assert len(response.json()) == 0

    def test_get_post_by_id(self, client: TestClient, db_with_post: tuple[Session, Post]):
        """Test getting a specific post by ID"""
        response = client.get("/posts/abc123")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "abc123"
        assert data["title"] == "Test Post Title"

    def test_get_post_not_found(self, client: TestClient):
        """Test getting a non-existent post"""
        response = client.get("/posts/nonexistent")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_update_post(self, client: TestClient, db_with_post: tuple[Session, Post]):
        """Test updating a post"""
        update_data = {"risk_score": 50, "risk_level": "medium"}
        response = client.patch("/posts/abc123", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["risk_score"] == 50
        assert data["risk_level"] == "medium"

    def test_update_post_not_found(self, client: TestClient):
        """Test updating a non-existent post"""
        update_data = {"risk_score": 50}
        response = client.patch("/posts/nonexistent", json=update_data)
        assert response.status_code == 404

    def test_delete_post(self, client: TestClient, db_with_post: tuple[Session, Post]):
        """Test deleting a post"""
        response = client.delete("/posts/abc123")
        assert response.status_code == 204

        # Verify post is deleted
        response = client.get("/posts/abc123")
        assert response.status_code == 404

    def test_delete_post_not_found(self, client: TestClient):
        """Test deleting a non-existent post"""
        response = client.delete("/posts/nonexistent")
        assert response.status_code == 404

    def test_get_high_risk_posts(
        self,
        client: TestClient,
        db_with_user: tuple[Session, User],
        sample_high_risk_post_data_api: dict,
    ):
        """Test getting high-risk posts"""
        # Create a high-risk post
        response = client.post("/posts", json=sample_high_risk_post_data_api)
        assert response.status_code == 201

        # Get high-risk posts
        response = client.get("/posts/high-risk", params={"min_score": 50})
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert all(post["risk_score"] >= 50 for post in data)


class TestUserEndpoints:
    """Tests for user-related endpoints"""

    def test_create_user(self, client: TestClient, sample_user_data_api: dict):
        """Test creating a new user"""
        response = client.post("/users", json=sample_user_data_api)
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == sample_user_data_api["username"]
        assert data["risk_score"] == sample_user_data_api["risk_assessment"]["risk_score"]

    def test_create_user_duplicate(
        self, client: TestClient, db_with_user: tuple[Session, User], sample_user_data_api: dict
    ):
        """Test creating a duplicate user returns error"""
        response = client.post("/users", json=sample_user_data_api)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    def test_get_users_empty(self, client: TestClient):
        """Test getting users when database is empty"""
        response = client.get("/users")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_users_with_data(self, client: TestClient, db_with_user: tuple[Session, User]):
        """Test getting users with data"""
        response = client.get("/users")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["username"] == "test_user"

    def test_get_users_with_filters(self, client: TestClient, db_with_user: tuple[Session, User]):
        """Test getting users with various filters"""
        # Filter by min_risk_score
        response = client.get("/users", params={"min_risk_score": 20})
        assert response.status_code == 200
        assert len(response.json()) == 1

        # Filter by higher min_risk_score
        response = client.get("/users", params={"min_risk_score": 100})
        assert response.status_code == 200
        assert len(response.json()) == 0

        # Filter by risk_level
        response = client.get("/users", params={"risk_level": "low"})
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_get_user_by_username(self, client: TestClient, db_with_user: tuple[Session, User]):
        """Test getting a specific user by username"""
        response = client.get("/users/test_user")
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "test_user"

    def test_get_user_not_found(self, client: TestClient):
        """Test getting a non-existent user"""
        response = client.get("/users/nonexistent")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_update_user(self, client: TestClient, db_with_user: tuple[Session, User]):
        """Test updating a user"""
        update_data = {"risk_score": 75, "risk_level": "high", "is_monitored": True}
        response = client.patch("/users/test_user", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["risk_score"] == 75
        assert data["risk_level"] == "high"
        assert data["is_monitored"] is True

    def test_update_user_not_found(self, client: TestClient):
        """Test updating a non-existent user"""
        update_data = {"risk_score": 50}
        response = client.patch("/users/nonexistent", json=update_data)
        assert response.status_code == 404

    def test_delete_user(self, client: TestClient, db_with_user: tuple[Session, User]):
        """Test deleting a user"""
        response = client.delete("/users/test_user")
        assert response.status_code == 204

        # Verify user is deleted
        response = client.get("/users/test_user")
        assert response.status_code == 404

    def test_delete_user_not_found(self, client: TestClient):
        """Test deleting a non-existent user"""
        response = client.delete("/users/nonexistent")
        assert response.status_code == 404

    def test_get_high_risk_users(
        self, client: TestClient, sample_high_risk_user_data_api: dict
    ):
        """Test getting high-risk users"""
        # Create a high-risk user
        response = client.post("/users", json=sample_high_risk_user_data_api)
        assert response.status_code == 201

        # Get high-risk users
        response = client.get("/users/high-risk", params={"min_score": 50})
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert all(user["risk_score"] >= 50 for user in data)

    def test_get_monitored_users_empty(self, client: TestClient):
        """Test getting monitored users when none exist"""
        response = client.get("/users/monitored")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_monitored_users(self, client: TestClient, db_with_user: tuple[Session, User]):
        """Test getting monitored users"""
        # First, set user as monitored
        update_data = {"is_monitored": True}
        client.patch("/users/test_user", json=update_data)

        # Get monitored users
        response = client.get("/users/monitored")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["username"] == "test_user"
        assert data[0]["is_monitored"] is True


class TestBulkEndpoints:
    """Tests for bulk import endpoints"""

    def test_bulk_create_posts(
        self, client: TestClient, db_with_user: tuple[Session, User], sample_post_data_api: dict
    ):
        """Test bulk creating posts"""
        post1 = sample_post_data_api.copy()
        post2 = sample_post_data_api.copy()
        post2["id"] = "post_2"
        post2["title"] = "Second Post"

        response = client.post("/bulk/posts", json=[post1, post2])
        assert response.status_code == 201
        data = response.json()
        assert data["created"] == 2
        assert data["skipped"] == 0
        assert data["errors"] == []

    def test_bulk_create_posts_with_duplicates(
        self, client: TestClient, db_with_post: tuple[Session, Post], sample_post_data_api: dict
    ):
        """Test bulk creating posts with duplicates"""
        post1 = sample_post_data_api.copy()  # Already exists
        post2 = sample_post_data_api.copy()
        post2["id"] = "new_post"
        post2["title"] = "New Post"

        response = client.post("/bulk/posts", json=[post1, post2])
        assert response.status_code == 201
        data = response.json()
        assert data["created"] == 1
        assert data["skipped"] == 1

    def test_bulk_create_users(self, client: TestClient, sample_user_data_api: dict):
        """Test bulk creating users"""
        user1 = sample_user_data_api.copy()
        user2 = sample_user_data_api.copy()
        user2["username"] = "user_2"

        response = client.post("/bulk/users", json=[user1, user2])
        assert response.status_code == 201
        data = response.json()
        assert data["created"] == 2
        assert data["skipped"] == 0
        assert data["errors"] == []

    def test_bulk_create_users_with_duplicates(
        self, client: TestClient, db_with_user: tuple[Session, User], sample_user_data_api: dict
    ):
        """Test bulk creating users with duplicates"""
        user1 = sample_user_data_api.copy()  # Already exists
        user2 = sample_user_data_api.copy()
        user2["username"] = "new_user"

        response = client.post("/bulk/users", json=[user1, user2])
        assert response.status_code == 201
        data = response.json()
        assert data["created"] == 1
        assert data["skipped"] == 1

    def test_bulk_create_posts_empty_list(
        self, client: TestClient, db_with_user: tuple[Session, User]
    ):
        """Test bulk creating with empty list"""
        response = client.post("/bulk/posts", json=[])
        assert response.status_code == 201
        data = response.json()
        assert data["created"] == 0
        assert data["skipped"] == 0

    def test_bulk_create_users_empty_list(self, client: TestClient):
        """Test bulk creating users with empty list"""
        response = client.post("/bulk/users", json=[])
        assert response.status_code == 201
        data = response.json()
        assert data["created"] == 0
        assert data["skipped"] == 0


class TestAlertEndpoints:
    """Tests for alert-related endpoints"""

    def test_create_alert(
        self, client: TestClient, db_with_user: tuple[Session, User], sample_alert_data_api: dict
    ):
        """Test creating a new alert"""
        response = client.post("/alerts", json=sample_alert_data_api)
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == sample_alert_data_api["username"]
        assert data["alert_type"] == sample_alert_data_api["alert_type"]
        assert data["severity"] == sample_alert_data_api["severity"]
        assert data["risk_score"] == sample_alert_data_api["risk_score"]
        assert data["description"] == sample_alert_data_api["description"]
        assert data["status"] == "new"
        assert "id" in data
        assert "created_at" in data

    def test_create_alert_minimal_data(self, client: TestClient, db_with_user: tuple[Session, User]):
        """Test creating an alert with minimal required data"""
        minimal_alert = {
            "username": "test_user",
            "alert_type": "risk_threshold",
            "severity": "medium",
            "risk_score": 50,
            "description": "User exceeded risk threshold"
        }
        response = client.post("/alerts", json=minimal_alert)
        assert response.status_code == 201
        data = response.json()
        assert data["post_id"] is None
        assert data["details"] is None

    def test_get_alerts_empty(self, client: TestClient):
        """Test getting alerts when database is empty"""
        response = client.get("/alerts")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_alerts_with_data(
        self, client: TestClient, db_with_alert: tuple[Session, Alert]
    ):
        """Test getting alerts with data"""
        response = client.get("/alerts")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["username"] == "test_user"
        assert data[0]["severity"] == "high"

    def test_get_alerts_with_filters(
        self, client: TestClient, db_with_alert: tuple[Session, Alert]
    ):
        """Test getting alerts with various filters"""
        # Filter by username
        response = client.get("/alerts", params={"username": "test_user"})
        assert response.status_code == 200
        assert len(response.json()) == 1

        # Filter by non-existent username
        response = client.get("/alerts", params={"username": "nonexistent"})
        assert response.status_code == 200
        assert len(response.json()) == 0

        # Filter by severity
        response = client.get("/alerts", params={"severity": "high"})
        assert response.status_code == 200
        assert len(response.json()) == 1

        # Filter by status
        response = client.get("/alerts", params={"status": "new"})
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_get_alerts_pagination(
        self, client: TestClient, db_with_alert: tuple[Session, Alert]
    ):
        """Test alerts pagination"""
        response = client.get("/alerts", params={"skip": 0, "limit": 10})
        assert response.status_code == 200

        response = client.get("/alerts", params={"skip": 100, "limit": 10})
        assert response.status_code == 200
        assert len(response.json()) == 0

    def test_get_alert_by_id(
        self, client: TestClient, db_with_alert: tuple[Session, Alert]
    ):
        """Test getting a specific alert by ID"""
        _, alert = db_with_alert
        response = client.get(f"/alerts/{alert.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == alert.id
        assert data["username"] == "test_user"

    def test_get_alert_not_found(self, client: TestClient):
        """Test getting a non-existent alert"""
        response = client.get("/alerts/99999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_update_alert(
        self, client: TestClient, db_with_alert: tuple[Session, Alert]
    ):
        """Test updating an alert"""
        _, alert = db_with_alert
        update_data = {
            "status": "reviewed",
            "reviewed_by": "admin_user",
            "resolution_notes": "Reviewed and confirmed as valid alert"
        }
        response = client.patch(f"/alerts/{alert.id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "reviewed"
        assert data["reviewed_by"] == "admin_user"
        assert data["resolution_notes"] == "Reviewed and confirmed as valid alert"

    def test_update_alert_not_found(self, client: TestClient):
        """Test updating a non-existent alert"""
        update_data = {"status": "reviewed"}
        response = client.patch("/alerts/99999", json=update_data)
        assert response.status_code == 404

    def test_delete_alert(
        self, client: TestClient, db_with_alert: tuple[Session, Alert]
    ):
        """Test deleting an alert"""
        _, alert = db_with_alert
        response = client.delete(f"/alerts/{alert.id}")
        assert response.status_code == 204

        # Verify alert is deleted
        response = client.get(f"/alerts/{alert.id}")
        assert response.status_code == 404

    def test_delete_alert_not_found(self, client: TestClient):
        """Test deleting a non-existent alert"""
        response = client.delete("/alerts/99999")
        assert response.status_code == 404


class TestMonitoringLogEndpoints:
    """Tests for monitoring log endpoints"""

    def test_create_monitoring_log(
        self, client: TestClient, db_with_user: tuple[Session, User], sample_monitoring_log_data_api: dict
    ):
        """Test creating a new monitoring log"""
        response = client.post("/monitoring-logs", json=sample_monitoring_log_data_api)
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == sample_monitoring_log_data_api["username"]
        assert data["activity_type"] == sample_monitoring_log_data_api["activity_type"]
        assert data["description"] == sample_monitoring_log_data_api["description"]
        assert data["findings"] == sample_monitoring_log_data_api["findings"]
        assert "id" in data
        assert "created_at" in data

    def test_create_monitoring_log_minimal_data(
        self, client: TestClient, db_with_user: tuple[Session, User]
    ):
        """Test creating a monitoring log with minimal required data"""
        minimal_log = {
            "username": "test_user",
            "activity_type": "scheduled_check"
        }
        response = client.post("/monitoring-logs", json=minimal_log)
        assert response.status_code == 201
        data = response.json()
        assert data["description"] is None
        assert data["findings"] is None

    def test_get_monitoring_logs_empty(self, client: TestClient):
        """Test getting monitoring logs when database is empty"""
        response = client.get("/monitoring-logs")
        assert response.status_code == 200
        assert response.json() == []

    def test_get_monitoring_logs_with_data(
        self, client: TestClient, db_with_monitoring_log: tuple[Session, MonitoringLog]
    ):
        """Test getting monitoring logs with data"""
        response = client.get("/monitoring-logs")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["username"] == "test_user"
        assert data[0]["activity_type"] == "post_review"

    def test_get_monitoring_logs_with_filters(
        self, client: TestClient, db_with_monitoring_log: tuple[Session, MonitoringLog]
    ):
        """Test getting monitoring logs with various filters"""
        # Filter by username
        response = client.get("/monitoring-logs", params={"username": "test_user"})
        assert response.status_code == 200
        assert len(response.json()) == 1

        # Filter by non-existent username
        response = client.get("/monitoring-logs", params={"username": "nonexistent"})
        assert response.status_code == 200
        assert len(response.json()) == 0

        # Filter by activity_type
        response = client.get("/monitoring-logs", params={"activity_type": "post_review"})
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_get_monitoring_logs_pagination(
        self, client: TestClient, db_with_monitoring_log: tuple[Session, MonitoringLog]
    ):
        """Test monitoring logs pagination"""
        response = client.get("/monitoring-logs", params={"skip": 0, "limit": 10})
        assert response.status_code == 200

        response = client.get("/monitoring-logs", params={"skip": 100, "limit": 10})
        assert response.status_code == 200
        assert len(response.json()) == 0

    def test_get_monitoring_logs_days_back(
        self, client: TestClient, db_with_monitoring_log: tuple[Session, MonitoringLog]
    ):
        """Test filtering monitoring logs by days_back"""
        # Recent logs (within 7 days - default)
        response = client.get("/monitoring-logs", params={"days_back": 7})
        assert response.status_code == 200
        assert len(response.json()) == 1

        # Very old logs filter (logs from last 1 day should still include recent)
        response = client.get("/monitoring-logs", params={"days_back": 1})
        assert response.status_code == 200
        # Log was just created, should be included
