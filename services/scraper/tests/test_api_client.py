"""Tests for APIClient"""
import pytest
import responses
from unittest.mock import patch, MagicMock

from src.api_client import APIClient, BulkResult, SendAllResult


class TestBulkResult:
    """Tests for BulkResult class"""

    def test_bulk_result_defaults(self):
        """Test BulkResult default values"""
        result = BulkResult()
        assert result.created == 0
        assert result.skipped == 0
        assert result.errors == 0

    def test_bulk_result_custom_values(self):
        """Test BulkResult with custom values"""
        result = BulkResult(created=5, skipped=2, errors=1)
        assert result.created == 5
        assert result.skipped == 2
        assert result.errors == 1


class TestSendAllResult:
    """Tests for SendAllResult class"""

    def test_send_all_result(self):
        """Test SendAllResult initialization"""
        posts_result = BulkResult(created=10, skipped=2)
        users_result = BulkResult(created=5, skipped=1)

        result = SendAllResult(posts=posts_result, users=users_result)

        assert result.posts.created == 10
        assert result.users.created == 5


class TestAPIClientInit:
    """Tests for APIClient initialization"""

    def test_init_default_url(self):
        """Test default API URL from settings"""
        with patch("src.api_client.settings") as mock_settings:
            mock_settings.api_url = "http://localhost:8000"
            mock_settings.api_timeout = 30

            client = APIClient()
            assert client.base_url == "http://localhost:8000"

    def test_init_custom_url(self):
        """Test custom API URL"""
        with patch("src.api_client.settings") as mock_settings:
            mock_settings.api_timeout = 30

            client = APIClient(base_url="http://custom:9000")
            assert client.base_url == "http://custom:9000"


class TestHealthCheck:
    """Tests for health_check method"""

    @responses.activate
    def test_health_check_success(self):
        """Test successful health check"""
        responses.add(
            responses.GET,
            "http://test-api:8000/health",
            json={"status": "healthy"},
            status=200,
        )

        with patch("src.api_client.settings") as mock_settings:
            mock_settings.api_timeout = 30

            client = APIClient(base_url="http://test-api:8000")
            assert client.health_check() is True

    @responses.activate
    def test_health_check_failure(self):
        """Test failed health check"""
        responses.add(
            responses.GET,
            "http://test-api:8000/health",
            status=500,
        )

        with patch("src.api_client.settings") as mock_settings:
            mock_settings.api_timeout = 30

            client = APIClient(base_url="http://test-api:8000")
            assert client.health_check() is False

    def test_health_check_connection_error(self):
        """Test health check with connection error"""
        with patch("src.api_client.settings") as mock_settings:
            mock_settings.api_timeout = 30

            client = APIClient(base_url="http://nonexistent-host:9999")
            # This should return False due to connection error
            assert client.health_check() is False


class TestPreparePost:
    """Tests for _prepare_post method"""

    def test_prepare_post_basic(self, sample_scored_post):
        """Test basic post preparation"""
        with patch("src.api_client.settings") as mock_settings:
            mock_settings.api_timeout = 30

            client = APIClient(base_url="http://test")
            prepared = client._prepare_post(sample_scored_post)

            assert prepared["id"] == sample_scored_post["id"]
            assert prepared["title"] == sample_scored_post["title"]
            assert prepared["risk_assessment"]["risk_score"] == 15
            assert prepared["risk_assessment"]["risk_level"] == "low"

    def test_prepare_post_missing_fields(self):
        """Test post preparation with missing fields"""
        with patch("src.api_client.settings") as mock_settings:
            mock_settings.api_timeout = 30

            client = APIClient(base_url="http://test")
            minimal_post = {"id": "test"}
            prepared = client._prepare_post(minimal_post)

            assert prepared["id"] == "test"
            assert prepared["title"] == ""
            assert prepared["risk_assessment"]["risk_score"] == 0

    def test_prepare_post_converts_scores_to_int(self):
        """Test that float scores are converted to int"""
        with patch("src.api_client.settings") as mock_settings:
            mock_settings.api_timeout = 30

            client = APIClient(base_url="http://test")
            post = {
                "id": "test",
                "risk_assessment": {
                    "risk_score": 15.5,
                    "hate_score": 10.3,
                    "violence_score": 5.2,
                },
            }
            prepared = client._prepare_post(post)

            assert prepared["risk_assessment"]["risk_score"] == 15
            assert prepared["risk_assessment"]["hate_score"] == 10
            assert prepared["risk_assessment"]["violence_score"] == 5


class TestPrepareUser:
    """Tests for _prepare_user method"""

    def test_prepare_user_basic(self, sample_scored_user):
        """Test basic user preparation"""
        with patch("src.api_client.settings") as mock_settings:
            mock_settings.api_timeout = 30

            client = APIClient(base_url="http://test")
            prepared = client._prepare_user(sample_scored_user)

            assert prepared["username"] == sample_scored_user["username"]
            assert prepared["risk_assessment"]["risk_score"] == 25
            assert prepared["risk_assessment"]["risk_level"] == "low"

    def test_prepare_user_maps_field_names(self):
        """Test that scorer field names are mapped correctly"""
        with patch("src.api_client.settings") as mock_settings:
            mock_settings.api_timeout = 30

            client = APIClient(base_url="http://test")
            user = {
                "username": "test",
                "risk_assessment": {
                    "overall_risk_score": 50,
                    "average_hate_score": 30,
                    "average_violence_score": 20,
                    "risk_level": "high",
                },
            }
            prepared = client._prepare_user(user)

            assert prepared["risk_assessment"]["risk_score"] == 50
            assert prepared["risk_assessment"]["hate_score"] == 30
            assert prepared["risk_assessment"]["violence_score"] == 20

    def test_prepare_user_missing_fields(self):
        """Test user preparation with missing fields"""
        with patch("src.api_client.settings") as mock_settings:
            mock_settings.api_timeout = 30

            client = APIClient(base_url="http://test")
            minimal_user = {"username": "test"}
            prepared = client._prepare_user(minimal_user)

            assert prepared["username"] == "test"
            assert prepared["risk_assessment"]["risk_score"] == 0
            assert prepared["statistics"]["total_posts_analyzed"] == 0


class TestSendPosts:
    """Tests for send_posts method"""

    @responses.activate
    def test_send_posts_success(self, sample_scored_post, mock_api_response):
        """Test successful post sending"""
        responses.add(
            responses.POST,
            "http://test-api:8000/bulk/posts",
            json=mock_api_response,
            status=200,
        )

        with patch("src.api_client.settings") as mock_settings:
            mock_settings.api_timeout = 30

            client = APIClient(base_url="http://test-api:8000")
            result = client.send_posts([sample_scored_post])

            assert result.created == 5
            assert result.skipped == 2
            assert result.errors == 0

    @responses.activate
    def test_send_posts_empty_list(self):
        """Test sending empty list of posts"""
        with patch("src.api_client.settings") as mock_settings:
            mock_settings.api_timeout = 30

            client = APIClient(base_url="http://test-api:8000")
            result = client.send_posts([])

            assert result.created == 0
            assert result.skipped == 0
            assert result.errors == 0

    @responses.activate
    def test_send_posts_api_error(self, sample_scored_post):
        """Test handling of API errors"""
        responses.add(
            responses.POST,
            "http://test-api:8000/bulk/posts",
            status=500,
        )

        with patch("src.api_client.settings") as mock_settings:
            mock_settings.api_timeout = 30

            client = APIClient(base_url="http://test-api:8000")

            with pytest.raises(Exception):
                client.send_posts([sample_scored_post])


class TestSendUsers:
    """Tests for send_users method"""

    @responses.activate
    def test_send_users_success(self, sample_scored_user, mock_api_response):
        """Test successful user sending"""
        responses.add(
            responses.POST,
            "http://test-api:8000/bulk/users",
            json=mock_api_response,
            status=200,
        )

        with patch("src.api_client.settings") as mock_settings:
            mock_settings.api_timeout = 30

            client = APIClient(base_url="http://test-api:8000")
            result = client.send_users([sample_scored_user])

            assert result.created == 5
            assert result.skipped == 2

    @responses.activate
    def test_send_users_empty_list(self):
        """Test sending empty list of users"""
        with patch("src.api_client.settings") as mock_settings:
            mock_settings.api_timeout = 30

            client = APIClient(base_url="http://test-api:8000")
            result = client.send_users([])

            assert result.created == 0
            assert result.skipped == 0

    @responses.activate
    def test_send_users_validation_error(self, sample_scored_user):
        """Test handling of validation errors"""
        responses.add(
            responses.POST,
            "http://test-api:8000/bulk/users",
            json={"detail": "Validation error"},
            status=422,
        )

        with patch("src.api_client.settings") as mock_settings:
            mock_settings.api_timeout = 30

            client = APIClient(base_url="http://test-api:8000")

            with pytest.raises(Exception):
                client.send_users([sample_scored_user])


class TestSendAll:
    """Tests for send_all method"""

    @responses.activate
    def test_send_all_success(
        self, sample_scored_post, sample_scored_user, mock_api_response
    ):
        """Test sending both posts and users"""
        responses.add(
            responses.POST,
            "http://test-api:8000/bulk/posts",
            json=mock_api_response,
            status=200,
        )
        responses.add(
            responses.POST,
            "http://test-api:8000/bulk/users",
            json={"created": 3, "skipped": 1, "errors": []},
            status=200,
        )

        with patch("src.api_client.settings") as mock_settings:
            mock_settings.api_timeout = 30

            client = APIClient(base_url="http://test-api:8000")
            result = client.send_all([sample_scored_post], [sample_scored_user])

            assert result.posts.created == 5
            assert result.users.created == 3

    @responses.activate
    def test_send_all_empty_lists(self):
        """Test sending empty lists"""
        with patch("src.api_client.settings") as mock_settings:
            mock_settings.api_timeout = 30

            client = APIClient(base_url="http://test-api:8000")
            result = client.send_all([], [])

            assert result.posts.created == 0
            assert result.users.created == 0
