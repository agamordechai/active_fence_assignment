"""Pydantic schemas for API request/response models"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ==================== Post Schemas ====================

class RiskAssessmentBase(BaseModel):
    """Base schema for risk assessment"""
    risk_score: int = 0
    risk_level: str = "minimal"
    hate_score: int = 0
    violence_score: int = 0
    explanation: str = ""
    flags: List[str] = []


class PostBase(BaseModel):
    """Base schema for posts"""
    id: str
    title: str
    selftext: str = ""
    author: str
    subreddit: str
    created_utc: float
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


class PostCreate(PostBase):
    """Schema for creating a post"""
    risk_assessment: Optional[RiskAssessmentBase] = None
    scored_at: Optional[datetime] = None


class PostUpdate(BaseModel):
    """Schema for updating a post"""
    risk_score: Optional[int] = None
    risk_level: Optional[str] = None
    risk_explanation: Optional[str] = None
    risk_flags: Optional[List[str]] = None


class PostResponse(PostBase):
    """Schema for post responses"""
    risk_score: int
    risk_level: str
    hate_score: int
    violence_score: int
    risk_explanation: Optional[str]
    risk_flags: Optional[List[str]]
    scored_at: Optional[datetime]
    collected_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== User Schemas ====================

class UserStatisticsBase(BaseModel):
    """Base schema for user statistics"""
    total_posts_analyzed: int = 0
    flagged_posts_count: int = 0
    flagged_comments_count: int = 0
    avg_post_risk_score: float = 0.0
    avg_comment_risk_score: float = 0.0
    max_risk_score_seen: int = 0


class UserBase(BaseModel):
    """Base schema for users"""
    username: str
    account_created_utc: Optional[float] = None
    account_created_date: Optional[datetime] = None
    link_karma: int = 0
    comment_karma: int = 0
    is_gold: bool = False
    is_mod: bool = False
    has_verified_email: bool = False


class UserCreate(UserBase):
    """Schema for creating a user"""
    risk_assessment: Optional[RiskAssessmentBase] = None
    statistics: Optional[UserStatisticsBase] = None
    scored_at: Optional[datetime] = None


class UserUpdate(BaseModel):
    """Schema for updating a user"""
    risk_score: Optional[int] = None
    risk_level: Optional[str] = None
    risk_explanation: Optional[str] = None
    risk_factors: Optional[List[Dict[str, Any]]] = None
    is_monitored: Optional[bool] = None
    last_monitored_at: Optional[datetime] = None


class UserResponse(UserBase):
    """Schema for user responses"""
    risk_score: int
    risk_level: str
    hate_score: int
    violence_score: int
    risk_explanation: Optional[str]
    risk_factors: Optional[List[Dict[str, Any]]]
    total_posts_analyzed: int
    flagged_posts_count: int
    flagged_comments_count: int
    avg_post_risk_score: float
    avg_comment_risk_score: float
    max_risk_score_seen: int
    is_monitored: bool
    last_monitored_at: Optional[datetime]
    alert_count: int
    scored_at: Optional[datetime]
    collected_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Alert Schemas ====================

class AlertBase(BaseModel):
    """Base schema for alerts"""
    username: str
    post_id: Optional[str] = None
    alert_type: str
    severity: str
    risk_score: int
    description: str
    details: Optional[Dict[str, Any]] = None


class AlertCreate(AlertBase):
    """Schema for creating an alert"""
    pass


class AlertUpdate(BaseModel):
    """Schema for updating an alert"""
    status: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    resolution_notes: Optional[str] = None


class AlertResponse(AlertBase):
    """Schema for alert responses"""
    id: int
    status: str
    reviewed_at: Optional[datetime]
    reviewed_by: Optional[str]
    resolution_notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== Monitoring Log Schemas ====================

class MonitoringLogBase(BaseModel):
    """Base schema for monitoring logs"""
    username: str
    activity_type: str
    description: Optional[str] = None
    findings: Optional[Dict[str, Any]] = None


class MonitoringLogCreate(MonitoringLogBase):
    """Schema for creating a monitoring log"""
    pass


class MonitoringLogResponse(MonitoringLogBase):
    """Schema for monitoring log responses"""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Statistics Schema ====================

class StatisticsResponse(BaseModel):
    """Schema for statistics responses"""
    total_posts: int
    total_users: int
    high_risk_posts: int
    high_risk_users: int
    posts_by_risk: dict  # {"critical": int, "high": int, "medium": int}
    users_by_risk: dict  # {"critical": int, "high": int, "medium": int}
    monitored_users: int
    timestamp: str


# ==================== Query Parameter Schemas ====================

class PostQuery(BaseModel):
    """Schema for post query parameters"""
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)
    subreddit: Optional[str] = None
    author: Optional[str] = None
    min_risk_score: Optional[int] = None
    risk_level: Optional[str] = None
    order_by: str = Field("created_date", pattern="^(created_date|risk_score)$")


class UserQuery(BaseModel):
    """Schema for user query parameters"""
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)
    min_risk_score: Optional[int] = None
    risk_level: Optional[str] = None
    is_monitored: Optional[bool] = None
    order_by: str = Field("risk_score", pattern="^(risk_score|updated_at)$")


class AlertQuery(BaseModel):
    """Schema for alert query parameters"""
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)
    username: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None
    days_back: Optional[int] = None

