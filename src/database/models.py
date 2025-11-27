"""Database models for the application"""
from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text,
    ForeignKey, JSON, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Post(Base):
    """Model for Reddit posts"""
    __tablename__ = "posts"

    id = Column(String(50), primary_key=True)
    title = Column(Text, nullable=False)
    selftext = Column(Text, default="")
    author = Column(String(100), ForeignKey("users.username"), nullable=False, index=True)
    subreddit = Column(String(100), nullable=False, index=True)
    created_utc = Column(Float, nullable=False)
    created_date = Column(DateTime, nullable=False, index=True)
    score = Column(Integer, default=0)
    upvote_ratio = Column(Float, default=0.0)
    num_comments = Column(Integer, default=0)
    permalink = Column(String(500))
    url = Column(Text)
    is_self = Column(Boolean, default=False)
    over_18 = Column(Boolean, default=False)
    spoiler = Column(Boolean, default=False)
    locked = Column(Boolean, default=False)
    link_flair_text = Column(String(200))

    # Risk assessment fields
    risk_score = Column(Integer, default=0, index=True)
    risk_level = Column(String(50), default="minimal", index=True)
    hate_score = Column(Integer, default=0)
    violence_score = Column(Integer, default=0)
    risk_explanation = Column(Text)
    risk_flags = Column(JSON)  # Store flags as JSON array

    # Metadata
    scored_at = Column(DateTime)
    collected_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="posts")

    # Indexes for common queries
    __table_args__ = (
        Index('idx_risk_level_score', 'risk_level', 'risk_score'),
        Index('idx_subreddit_date', 'subreddit', 'created_date'),
        Index('idx_author_date', 'author', 'created_date'),
    )

    def __repr__(self):
        return f"<Post(id={self.id}, author={self.author}, risk_level={self.risk_level})>"


class User(Base):
    """Model for Reddit users"""
    __tablename__ = "users"

    username = Column(String(100), primary_key=True)
    account_created_utc = Column(Float)
    account_created_date = Column(DateTime)
    link_karma = Column(Integer, default=0)
    comment_karma = Column(Integer, default=0)
    is_gold = Column(Boolean, default=False)
    is_mod = Column(Boolean, default=False)
    has_verified_email = Column(Boolean, default=False)

    # Risk assessment fields
    risk_score = Column(Integer, default=0, index=True)
    risk_level = Column(String(50), default="minimal", index=True)
    hate_score = Column(Integer, default=0)
    violence_score = Column(Integer, default=0)
    risk_explanation = Column(Text)
    risk_factors = Column(JSON)  # Store risk factors as JSON

    # User statistics
    total_posts_analyzed = Column(Integer, default=0)
    flagged_posts_count = Column(Integer, default=0)
    flagged_comments_count = Column(Integer, default=0)
    avg_post_risk_score = Column(Float, default=0.0)
    avg_comment_risk_score = Column(Float, default=0.0)
    max_risk_score_seen = Column(Integer, default=0)

    # Monitoring
    is_monitored = Column(Boolean, default=False, index=True)
    last_monitored_at = Column(DateTime)
    alert_count = Column(Integer, default=0)

    # Metadata
    scored_at = Column(DateTime)
    collected_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    posts = relationship("Post", back_populates="user")
    alerts = relationship("Alert", back_populates="user")

    # Indexes for common queries
    __table_args__ = (
        Index('idx_risk_level_score_user', 'risk_level', 'risk_score'),
        Index('idx_monitored_updated', 'is_monitored', 'updated_at'),
    )

    def __repr__(self):
        return f"<User(username={self.username}, risk_level={self.risk_level})>"


class Alert(Base):
    """Model for high-risk content alerts"""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), ForeignKey("users.username"), nullable=False, index=True)
    post_id = Column(String(50), ForeignKey("posts.id"))
    alert_type = Column(String(50), nullable=False, index=True)  # 'post', 'comment', 'pattern', etc.
    severity = Column(String(20), nullable=False, index=True)  # 'low', 'medium', 'high', 'critical'
    risk_score = Column(Integer, nullable=False)
    description = Column(Text, nullable=False)
    details = Column(JSON)  # Additional alert details as JSON

    # Status tracking
    status = Column(String(20), default="new", index=True)  # 'new', 'reviewed', 'dismissed', 'escalated'
    reviewed_at = Column(DateTime)
    reviewed_by = Column(String(100))
    resolution_notes = Column(Text)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="alerts")
    post = relationship("Post")

    # Indexes
    __table_args__ = (
        Index('idx_severity_status', 'severity', 'status'),
        Index('idx_created_severity', 'created_at', 'severity'),
    )

    def __repr__(self):
        return f"<Alert(id={self.id}, username={self.username}, severity={self.severity})>"


class MonitoringLog(Base):
    """Model for tracking monitoring activities"""
    __tablename__ = "monitoring_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), nullable=False, index=True)
    activity_type = Column(String(50), nullable=False)  # 'scan', 'alert', 'update', etc.
    description = Column(Text)
    findings = Column(JSON)  # Store findings as JSON

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index('idx_username_date', 'username', 'created_at'),
    )

    def __repr__(self):
        return f"<MonitoringLog(id={self.id}, username={self.username}, type={self.activity_type})>"

