"""Pydantic models for API data structures"""
from enum import StrEnum
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


class RiskLevel(StrEnum):
    """Risk level classification"""
    NONE = "none"
    MINIMAL = "minimal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskAssessment(BaseModel):
    """Risk assessment data for posts and users"""
    risk_score: float = 0
    risk_level: RiskLevel = RiskLevel.MINIMAL
    hate_score: float = 0
    violence_score: float = 0
    explanation: str = ""
    flags: List[str] = Field(default_factory=list)


class ScoredPost(BaseModel):
    """A Reddit post with risk scoring"""
    id: str
    title: str = ""
    selftext: str = ""
    author: str = ""
    subreddit: str = ""
    created_utc: int = 0
    created_date: datetime
    score: int = 0
    upvote_ratio: float = 0.0
    num_comments: int = 0
    permalink: Optional[str] = None
    url: Optional[str] = None
    is_self: bool = False
    over_18: bool = False
    spoiler: bool = False
    locked: bool = False
    link_flair_text: Optional[str] = None
    risk_assessment: RiskAssessment
    scored_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: dict) -> "ScoredPost":
        """Create ScoredPost from raw dictionary data"""
        risk = data.get('risk_assessment', {})

        # Handle created_date
        created_date = data.get('created_date')
        if isinstance(created_date, str):
            created_date = datetime.fromisoformat(created_date.replace('Z', '+00:00'))
        elif not isinstance(created_date, datetime):
            created_date = datetime.utcnow()

        # Handle scored_at
        scored_at = data.get('scored_at')
        if isinstance(scored_at, str):
            scored_at = datetime.fromisoformat(scored_at.replace('Z', '+00:00'))

        return cls(
            id=data.get('id', ''),
            title=data.get('title', ''),
            selftext=data.get('selftext', ''),
            author=data.get('author', ''),
            subreddit=data.get('subreddit', ''),
            created_utc=data.get('created_utc', 0),
            created_date=created_date,
            score=data.get('score', 0),
            upvote_ratio=data.get('upvote_ratio', 0.0),
            num_comments=data.get('num_comments', 0),
            permalink=data.get('permalink'),
            url=data.get('url'),
            is_self=data.get('is_self', False),
            over_18=data.get('over_18', False),
            spoiler=data.get('spoiler', False),
            locked=data.get('locked', False),
            link_flair_text=data.get('link_flair_text'),
            risk_assessment=RiskAssessment(
                risk_score=risk.get('risk_score', 0),
                risk_level=risk.get('risk_level', 'minimal'),
                hate_score=risk.get('hate_score', 0),
                violence_score=risk.get('violence_score', 0),
                explanation=risk.get('explanation', ''),
                flags=risk.get('flags', [])
            ),
            scored_at=scored_at
        )


class UserStatistics(BaseModel):
    """Statistics about a user's content"""
    total_posts_analyzed: int = 0
    flagged_posts_count: int = 0
    flagged_comments_count: int = 0
    avg_post_risk_score: float = 0.0
    avg_comment_risk_score: float = 0.0
    max_risk_score_seen: int = 0


class ScoredUser(BaseModel):
    """A Reddit user with risk scoring"""
    username: str
    account_created_utc: Optional[int] = None
    account_created_date: Optional[datetime] = None
    link_karma: int = 0
    comment_karma: int = 0
    is_gold: bool = False
    is_mod: bool = False
    has_verified_email: bool = False
    risk_assessment: RiskAssessment
    statistics: UserStatistics
    scored_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: dict) -> "ScoredUser":
        """Create ScoredUser from raw dictionary data"""
        risk = data.get('risk_assessment', {})

        # Handle account_created_date
        account_created_date = data.get('account_created_date')
        if isinstance(account_created_date, str):
            account_created_date = datetime.fromisoformat(
                account_created_date.replace('Z', '+00:00')
            )

        # Handle scored_at - can be in risk_assessment or at top level
        scored_at = risk.get('scored_at') or data.get('scored_at')
        if isinstance(scored_at, str):
            scored_at = datetime.fromisoformat(scored_at.replace('Z', '+00:00'))

        # Map scorer field names to API schema field names
        # Scorer uses: average_hate_score, average_violence_score, overall_risk_score
        hate_score = risk.get('average_hate_score', risk.get('hate_score', 0))
        violence_score = risk.get('average_violence_score', risk.get('violence_score', 0))
        risk_score = risk.get('overall_risk_score', risk.get('risk_score', 0))

        return cls(
            username=data.get('username', ''),
            account_created_utc=data.get('account_created_utc'),
            account_created_date=account_created_date,
            link_karma=data.get('link_karma', 0),
            comment_karma=data.get('comment_karma', 0),
            is_gold=data.get('is_gold', False),
            is_mod=data.get('is_mod', False),
            has_verified_email=data.get('has_verified_email', False),
            risk_assessment=RiskAssessment(
                risk_score=int(risk_score) if risk_score else 0,
                risk_level=risk.get('risk_level', 'minimal'),
                hate_score=int(hate_score) if hate_score else 0,
                violence_score=int(violence_score) if violence_score else 0,
                explanation=risk.get('explanation', ''),
                flags=risk.get('flags', [])
            ),
            statistics=UserStatistics(
                total_posts_analyzed=risk.get(
                    'total_content_analyzed', data.get('total_posts_analyzed', 0)
                ),
                flagged_posts_count=risk.get(
                    'high_risk_content_count', data.get('flagged_posts_count', 0)
                ),
                flagged_comments_count=data.get('flagged_comments_count', 0),
                avg_post_risk_score=float(risk_score) if risk_score else 0.0,
                avg_comment_risk_score=data.get('avg_comment_risk_score', 0.0),
                max_risk_score_seen=int(risk_score) if risk_score else 0
            ),
            scored_at=scored_at
        )


class BulkResult(BaseModel):
    """Result from bulk API operations"""
    created: int = 0
    skipped: int = 0
    errors: int = 0


class SendAllResult(BaseModel):
    """Result from sending both posts and users"""
    posts: BulkResult
    users: BulkResult
