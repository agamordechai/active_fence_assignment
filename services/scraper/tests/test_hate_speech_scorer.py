"""Tests for HateSpeechScorer"""
import pytest
from unittest.mock import patch, MagicMock
import json

from src.scorers.hate_speech_scorer import HateSpeechScorer


class TestHateSpeechScorerInit:
    """Tests for HateSpeechScorer initialization"""

    def test_init_loads_lexicon(self, mock_lexicon):
        """Test that lexicon is loaded correctly"""
        scorer = HateSpeechScorer(lexicon_path=str(mock_lexicon))

        assert "extreme" in scorer.hate_keywords
        assert "extreme" in scorer.violence_keywords
        assert len(scorer.slur_patterns) > 0
        assert "discussion" in scorer.context_indicators

    def test_init_file_not_found(self, tmp_path):
        """Test error when lexicon file not found"""
        with pytest.raises(FileNotFoundError):
            HateSpeechScorer(lexicon_path=str(tmp_path / "nonexistent.json"))


class TestScoreText:
    """Tests for score_text method"""

    def test_score_text_empty(self, mock_lexicon):
        """Test scoring empty text"""
        scorer = HateSpeechScorer(lexicon_path=str(mock_lexicon))

        result = scorer.score_text("")
        assert result["risk_score"] == 0
        assert result["risk_level"] == "none"
        assert result["explanation"] == "No content to analyze"

    def test_score_text_none(self, mock_lexicon):
        """Test scoring None"""
        scorer = HateSpeechScorer(lexicon_path=str(mock_lexicon))

        result = scorer.score_text(None)
        assert result["risk_score"] == 0
        assert result["risk_level"] == "none"

    def test_score_text_clean(self, mock_lexicon):
        """Test scoring clean text"""
        scorer = HateSpeechScorer(lexicon_path=str(mock_lexicon))

        result = scorer.score_text("This is a completely normal and friendly message.")
        assert result["risk_score"] == 0
        assert result["risk_level"] == "minimal"
        assert result["hate_score"] == 0
        assert result["violence_score"] == 0

    def test_score_text_extreme_hate(self, mock_lexicon):
        """Test scoring text with extreme hate keywords"""
        scorer = HateSpeechScorer(lexicon_path=str(mock_lexicon))

        result = scorer.score_text("This contains hate_extreme_word in it")
        assert result["hate_score"] == 30
        assert "Extreme hate keyword" in result["flags"][0]

    def test_score_text_high_hate(self, mock_lexicon):
        """Test scoring text with high hate keywords"""
        scorer = HateSpeechScorer(lexicon_path=str(mock_lexicon))

        result = scorer.score_text("This contains hate_high_word")
        assert result["hate_score"] == 20
        assert "High hate keyword" in result["flags"][0]

    def test_score_text_medium_hate(self, mock_lexicon):
        """Test scoring text with medium hate keywords"""
        scorer = HateSpeechScorer(lexicon_path=str(mock_lexicon))

        result = scorer.score_text("This contains hate_medium_word")
        assert result["hate_score"] == 10

    def test_score_text_extreme_violence(self, mock_lexicon):
        """Test scoring text with extreme violence keywords"""
        scorer = HateSpeechScorer(lexicon_path=str(mock_lexicon))

        result = scorer.score_text("I will kill them")
        assert result["violence_score"] == 30
        assert "Extreme violence keyword" in result["flags"][0]

    def test_score_text_slur_pattern(self, mock_lexicon):
        """Test scoring text with slur patterns"""
        scorer = HateSpeechScorer(lexicon_path=str(mock_lexicon))

        result = scorer.score_text("test_slur_word")
        assert result["hate_score"] == 40
        assert "Slur or derogatory term detected" in result["flags"]

    def test_score_text_aggressive_tone_exclamation(self, mock_lexicon):
        """Test scoring text with excessive exclamation marks"""
        scorer = HateSpeechScorer(lexicon_path=str(mock_lexicon))

        result = scorer.score_text("This is so annoying!!!!")
        assert result["hate_score"] == 5
        assert "Aggressive tone (excessive exclamation)" in result["flags"]

    def test_score_text_aggressive_tone_caps(self, mock_lexicon):
        """Test scoring text with excessive caps"""
        scorer = HateSpeechScorer(lexicon_path=str(mock_lexicon))

        result = scorer.score_text("THIS IS ALL IN CAPS AND VERY LONG")
        assert result["hate_score"] == 5
        assert "Aggressive tone (excessive caps)" in result["flags"]

    def test_score_text_discussion_context_reduces_score(self, mock_lexicon):
        """Test that discussion context reduces score"""
        scorer = HateSpeechScorer(lexicon_path=str(mock_lexicon))

        # Without context
        result_no_context = scorer.score_text("kill is a word")
        # With discussion context
        result_with_context = scorer.score_text(
            "We were discussing the word kill in an article about crime"
        )

        # Context should reduce the score
        assert result_with_context["violence_score"] < result_no_context["violence_score"]
        assert "Discussion context detected" in result_with_context["flags"]

    def test_score_text_quotation_context_reduces_score(self, mock_lexicon):
        """Test that quotation context reduces score"""
        scorer = HateSpeechScorer(lexicon_path=str(mock_lexicon))

        result = scorer.score_text("He said kill in the movie")
        assert "Quotation context detected" in result["flags"]

    def test_score_text_negation_reduces_score(self, mock_lexicon):
        """Test that negation reduces score"""
        scorer = HateSpeechScorer(lexicon_path=str(mock_lexicon))

        result = scorer.score_text("I would never kill anyone")
        assert "Negation detected" in result["flags"]

    def test_score_text_combined_risk(self, mock_lexicon):
        """Test combined hate and violence risk"""
        scorer = HateSpeechScorer(lexicon_path=str(mock_lexicon))

        result = scorer.score_text("hate_extreme_word and kill them all")
        assert result["hate_score"] > 0
        assert result["violence_score"] > 0
        assert result["risk_score"] == result["hate_score"] + result["violence_score"]


class TestGetRiskLevel:
    """Tests for _get_risk_level method"""

    def test_risk_level_minimal(self, mock_lexicon):
        """Test minimal risk level"""
        scorer = HateSpeechScorer(lexicon_path=str(mock_lexicon))
        assert scorer._get_risk_level(5) == "minimal"

    def test_risk_level_low(self, mock_lexicon):
        """Test low risk level"""
        scorer = HateSpeechScorer(lexicon_path=str(mock_lexicon))
        assert scorer._get_risk_level(15) == "low"

    def test_risk_level_medium(self, mock_lexicon):
        """Test medium risk level"""
        scorer = HateSpeechScorer(lexicon_path=str(mock_lexicon))
        assert scorer._get_risk_level(40) == "medium"

    def test_risk_level_high(self, mock_lexicon):
        """Test high risk level"""
        scorer = HateSpeechScorer(lexicon_path=str(mock_lexicon))
        assert scorer._get_risk_level(60) == "high"

    def test_risk_level_critical(self, mock_lexicon):
        """Test critical risk level"""
        scorer = HateSpeechScorer(lexicon_path=str(mock_lexicon))
        assert scorer._get_risk_level(80) == "critical"


class TestScorePost:
    """Tests for score_post method"""

    def test_score_post_basic(self, mock_lexicon, sample_post):
        """Test basic post scoring"""
        scorer = HateSpeechScorer(lexicon_path=str(mock_lexicon))

        scored = scorer.score_post(sample_post)

        assert "risk_assessment" in scored
        assert "scored_at" in scored
        assert scored["id"] == sample_post["id"]
        assert scored["title"] == sample_post["title"]

    def test_score_post_combines_title_and_body(self, mock_lexicon):
        """Test that title and body are combined for scoring"""
        scorer = HateSpeechScorer(lexicon_path=str(mock_lexicon))

        post = {
            "id": "test",
            "title": "hate_extreme_word",
            "selftext": "kill someone",
        }

        scored = scorer.score_post(post)

        # Both hate and violence should be detected
        assert scored["risk_assessment"]["hate_score"] > 0
        assert scored["risk_assessment"]["violence_score"] > 0

    def test_score_post_empty_body(self, mock_lexicon):
        """Test scoring post with no body"""
        scorer = HateSpeechScorer(lexicon_path=str(mock_lexicon))

        post = {"id": "test", "title": "Just a title", "selftext": ""}

        scored = scorer.score_post(post)
        assert "risk_assessment" in scored

    def test_score_post_preserves_original_data(self, mock_lexicon, sample_post):
        """Test that original post data is preserved"""
        scorer = HateSpeechScorer(lexicon_path=str(mock_lexicon))

        scored = scorer.score_post(sample_post)

        assert scored["id"] == sample_post["id"]
        assert scored["author"] == sample_post["author"]
        assert scored["subreddit"] == sample_post["subreddit"]


class TestScoreUser:
    """Tests for score_user method"""

    def test_score_user_no_content(self, mock_lexicon):
        """Test scoring user with no content"""
        scorer = HateSpeechScorer(lexicon_path=str(mock_lexicon))

        user = {
            "username": "empty_user",
            "content": {"all_text": []},
        }

        scored = scorer.score_user(user)

        assert scored["risk_assessment"]["overall_risk_score"] == 0
        assert scored["risk_assessment"]["risk_level"] == "none"
        assert "No content available" in scored["risk_assessment"]["explanation"]

    def test_score_user_clean_content(self, mock_lexicon, sample_enriched_user_data):
        """Test scoring user with clean content"""
        scorer = HateSpeechScorer(lexicon_path=str(mock_lexicon))

        scored = scorer.score_user(sample_enriched_user_data)

        assert scored["risk_assessment"]["overall_risk_score"] == 0
        assert scored["risk_assessment"]["risk_level"] == "minimal"

    def test_score_user_risky_content(self, mock_lexicon):
        """Test scoring user with risky content"""
        scorer = HateSpeechScorer(lexicon_path=str(mock_lexicon))

        # Create user with content that matches multiple keywords to exceed 50 threshold
        # high_risk_content_count requires score >= 50 per item
        risky_user = {
            "username": "risky_user",
            "content": {
                "all_text": [
                    # This should score 30 (hate) + 30 (violence) = 60, exceeding 50
                    "hate_extreme_word and kill them all in the same sentence",
                    "Normal text here",
                ],
            },
        }

        scored = scorer.score_user(risky_user)

        assert scored["risk_assessment"]["overall_risk_score"] > 0
        assert scored["risk_assessment"]["high_risk_content_count"] >= 1

    def test_score_user_calculates_averages(self, mock_lexicon):
        """Test that averages are calculated correctly"""
        scorer = HateSpeechScorer(lexicon_path=str(mock_lexicon))

        user = {
            "username": "test_user",
            "content": {
                "all_text": ["Normal text", "Another normal text"],
            },
        }

        scored = scorer.score_user(user)

        assert "average_hate_score" in scored["risk_assessment"]
        assert "average_violence_score" in scored["risk_assessment"]
        assert "total_content_analyzed" in scored["risk_assessment"]
        assert scored["risk_assessment"]["total_content_analyzed"] == 2


class TestScoreMultiple:
    """Tests for score_multiple_posts and score_multiple_users"""

    def test_score_multiple_posts(self, mock_lexicon, sample_post):
        """Test scoring multiple posts"""
        scorer = HateSpeechScorer(lexicon_path=str(mock_lexicon))

        posts = [sample_post, sample_post.copy()]
        posts[1]["id"] = "different_id"

        scored = scorer.score_multiple_posts(posts)

        assert len(scored) == 2
        assert all("risk_assessment" in p for p in scored)

    def test_score_multiple_posts_empty(self, mock_lexicon):
        """Test scoring empty list of posts"""
        scorer = HateSpeechScorer(lexicon_path=str(mock_lexicon))

        scored = scorer.score_multiple_posts([])
        assert scored == []

    def test_score_multiple_users(self, mock_lexicon, sample_enriched_user_data):
        """Test scoring multiple users"""
        scorer = HateSpeechScorer(lexicon_path=str(mock_lexicon))

        users = [sample_enriched_user_data, sample_enriched_user_data.copy()]
        users[1]["username"] = "different_user"

        scored = scorer.score_multiple_users(users)

        assert len(scored) == 2
        assert all("risk_assessment" in u for u in scored)


class TestGenerateExplanation:
    """Tests for explanation generation"""

    def test_generate_explanation_no_risk(self, mock_lexicon):
        """Test explanation for no risk"""
        scorer = HateSpeechScorer(lexicon_path=str(mock_lexicon))

        explanation = scorer._generate_explanation(0, [])
        assert "No concerning content detected" in explanation

    def test_generate_explanation_with_flags(self, mock_lexicon):
        """Test explanation with flags"""
        scorer = HateSpeechScorer(lexicon_path=str(mock_lexicon))

        flags = ["Flag 1", "Flag 2", "Flag 3"]
        explanation = scorer._generate_explanation(50, flags)

        assert "HIGH" in explanation
        assert "50" in explanation
        assert "Flag 1" in explanation

    def test_generate_explanation_many_flags(self, mock_lexicon):
        """Test explanation with many flags (truncation)"""
        scorer = HateSpeechScorer(lexicon_path=str(mock_lexicon))

        flags = [f"Flag {i}" for i in range(10)]
        explanation = scorer._generate_explanation(50, flags)

        assert "and 5 more indicators" in explanation


class TestUserExplanation:
    """Tests for user explanation generation"""

    def test_user_explanation_critical(self, mock_lexicon):
        """Test user explanation for critical risk"""
        scorer = HateSpeechScorer(lexicon_path=str(mock_lexicon))

        explanation = scorer._generate_user_explanation(
            "test_user", 80.0, 5, 10, 40.0, 40.0
        )

        assert "CRITICAL" in explanation
        assert "test_user" in explanation
        assert "IMMEDIATE REVIEW RECOMMENDED" in explanation

    def test_user_explanation_high(self, mock_lexicon):
        """Test user explanation for high risk"""
        scorer = HateSpeechScorer(lexicon_path=str(mock_lexicon))

        explanation = scorer._generate_user_explanation(
            "test_user", 60.0, 3, 10, 30.0, 30.0
        )

        assert "HIGH" in explanation
        assert "monitored closely" in explanation

    def test_user_explanation_medium(self, mock_lexicon):
        """Test user explanation for medium risk"""
        scorer = HateSpeechScorer(lexicon_path=str(mock_lexicon))

        explanation = scorer._generate_user_explanation(
            "test_user", 35.0, 2, 10, 20.0, 15.0
        )

        assert "MEDIUM" in explanation
        assert "periodic monitoring" in explanation
