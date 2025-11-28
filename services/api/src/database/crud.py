"""CRUD operations for database models"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from src.database.models import Post, User, Alert, MonitoringLog


# ==================== Post CRUD ====================

def create_post(db: Session, post_data: Dict[str, Any]) -> Post:
    """Create a new post"""
    # Extract risk assessment if present
    risk_assessment = post_data.pop('risk_assessment', {})

    # Handle scored_at conversion before using post_data
    scored_at_value = post_data.get('scored_at')
    if scored_at_value and isinstance(scored_at_value, str):
        post_data['scored_at'] = datetime.fromisoformat(scored_at_value)
    elif scored_at_value is None:
        post_data.pop('scored_at', None)  # Remove if None

    db_post = Post(
        **post_data,
        risk_score=risk_assessment.get('risk_score', 0),
        risk_level=risk_assessment.get('risk_level', 'minimal'),
        hate_score=risk_assessment.get('hate_score', 0),
        violence_score=risk_assessment.get('violence_score', 0),
        risk_explanation=risk_assessment.get('explanation', ''),
        risk_flags=risk_assessment.get('flags', [])
    )

    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post


def get_post(db: Session, post_id: str) -> Optional[Post]:
    """Get a post by ID"""
    return db.query(Post).filter(Post.id == post_id).first()


def get_posts(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    subreddit: Optional[str] = None,
    author: Optional[str] = None,
    min_risk_score: Optional[int] = None,
    risk_level: Optional[str] = None,
    order_by: str = "created_date"
) -> List[Post]:
    """Get posts with optional filtering"""
    query = db.query(Post)

    if subreddit:
        query = query.filter(Post.subreddit == subreddit)
    if author:
        query = query.filter(Post.author == author)
    if min_risk_score is not None:
        query = query.filter(Post.risk_score >= min_risk_score)
    if risk_level:
        query = query.filter(Post.risk_level == risk_level)

    # Order by
    if order_by == "risk_score":
        query = query.order_by(desc(Post.risk_score))
    elif order_by == "created_date":
        query = query.order_by(desc(Post.created_date))

    return query.offset(skip).limit(limit).all()


def get_high_risk_posts(db: Session, min_score: int = 5, limit: int = 100) -> List[Post]:
    """Get high-risk posts"""
    return db.query(Post)\
        .filter(Post.risk_score >= min_score)\
        .order_by(desc(Post.risk_score))\
        .limit(limit)\
        .all()


def update_post(db: Session, post_id: str, update_data: Dict[str, Any]) -> Optional[Post]:
    """Update a post"""
    db_post = get_post(db, post_id)
    if db_post:
        for key, value in update_data.items():
            setattr(db_post, key, value)
        db.commit()
        db.refresh(db_post)
    return db_post


def delete_post(db: Session, post_id: str) -> bool:
    """Delete a post"""
    db_post = get_post(db, post_id)
    if db_post:
        db.delete(db_post)
        db.commit()
        return True
    return False


# ==================== User CRUD ====================

def create_user(db: Session, user_data: Dict[str, Any]) -> User:
    """Create a new user"""
    # Extract risk assessment if present
    risk_assessment = user_data.pop('risk_assessment', {})
    statistics = user_data.pop('statistics', {})

    # Handle scored_at conversion before using user_data
    scored_at_value = user_data.get('scored_at')
    if scored_at_value and isinstance(scored_at_value, str):
        user_data['scored_at'] = datetime.fromisoformat(scored_at_value)
    elif scored_at_value is None:
        user_data.pop('scored_at', None)  # Remove if None

    db_user = User(
        **user_data,
        risk_score=risk_assessment.get('risk_score', 0),
        risk_level=risk_assessment.get('risk_level', 'minimal'),
        hate_score=risk_assessment.get('hate_score', 0),
        violence_score=risk_assessment.get('violence_score', 0),
        risk_explanation=risk_assessment.get('explanation', ''),
        risk_factors=risk_assessment.get('risk_factors', []),
        total_posts_analyzed=statistics.get('total_posts_analyzed', 0),
        flagged_posts_count=statistics.get('flagged_posts_count', 0),
        flagged_comments_count=statistics.get('flagged_comments_count', 0),
        avg_post_risk_score=statistics.get('avg_post_risk_score', 0.0),
        avg_comment_risk_score=statistics.get('avg_comment_risk_score', 0.0),
        max_risk_score_seen=statistics.get('max_risk_score_seen', 0)
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user(db: Session, username: str) -> Optional[User]:
    """Get a user by username"""
    return db.query(User).filter(User.username == username).first()


def get_users(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    min_risk_score: Optional[int] = None,
    risk_level: Optional[str] = None,
    is_monitored: Optional[bool] = None,
    order_by: str = "risk_score"
) -> List[User]:
    """Get users with optional filtering"""
    query = db.query(User)

    if min_risk_score is not None:
        query = query.filter(User.risk_score >= min_risk_score)
    if risk_level:
        query = query.filter(User.risk_level == risk_level)
    if is_monitored is not None:
        query = query.filter(User.is_monitored == is_monitored)

    # Order by
    if order_by == "risk_score":
        query = query.order_by(desc(User.risk_score))
    elif order_by == "updated_at":
        query = query.order_by(desc(User.updated_at))

    return query.offset(skip).limit(limit).all()


def get_high_risk_users(db: Session, min_score: int = 5, limit: int = 100) -> List[User]:
    """Get high-risk users"""
    return db.query(User)\
        .filter(User.risk_score >= min_score)\
        .order_by(desc(User.risk_score))\
        .limit(limit)\
        .all()


def get_monitored_users(db: Session) -> List[User]:
    """Get all monitored users"""
    return db.query(User).filter(User.is_monitored == True).all()


def update_user(db: Session, username: str, update_data: Dict[str, Any]) -> Optional[User]:
    """Update a user"""
    db_user = get_user(db, username)
    if db_user:
        for key, value in update_data.items():
            setattr(db_user, key, value)
        db.commit()
        db.refresh(db_user)
    return db_user


def delete_user(db: Session, username: str) -> bool:
    """Delete a user"""
    db_user = get_user(db, username)
    if db_user:
        db.delete(db_user)
        db.commit()
        return True
    return False


# ==================== Alert CRUD ====================

def create_alert(db: Session, alert_data: Dict[str, Any]) -> Alert:
    """Create a new alert"""
    db_alert = Alert(**alert_data)
    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)
    return db_alert


def get_alert(db: Session, alert_id: int) -> Optional[Alert]:
    """Get an alert by ID"""
    return db.query(Alert).filter(Alert.id == alert_id).first()


def get_alerts(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    username: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    days_back: Optional[int] = None
) -> List[Alert]:
    """Get alerts with optional filtering"""
    query = db.query(Alert)

    if username:
        query = query.filter(Alert.username == username)
    if severity:
        query = query.filter(Alert.severity == severity)
    if status:
        query = query.filter(Alert.status == status)
    if days_back:
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        query = query.filter(Alert.created_at >= cutoff_date)

    return query.order_by(desc(Alert.created_at)).offset(skip).limit(limit).all()


def update_alert(db: Session, alert_id: int, update_data: Dict[str, Any]) -> Optional[Alert]:
    """Update an alert"""
    db_alert = get_alert(db, alert_id)
    if db_alert:
        for key, value in update_data.items():
            setattr(db_alert, key, value)
        db.commit()
        db.refresh(db_alert)
    return db_alert


def delete_alert(db: Session, alert_id: int) -> bool:
    """Delete an alert"""
    db_alert = get_alert(db, alert_id)
    if db_alert:
        db.delete(db_alert)
        db.commit()
        return True
    return False


# ==================== Monitoring Log CRUD ====================

def create_monitoring_log(db: Session, log_data: Dict[str, Any]) -> MonitoringLog:
    """Create a monitoring log entry"""
    db_log = MonitoringLog(**log_data)
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log


def get_monitoring_logs(
    db: Session,
    username: Optional[str] = None,
    activity_type: Optional[str] = None,
    days_back: Optional[int] = 7,
    skip: int = 0,
    limit: int = 100
) -> List[MonitoringLog]:
    """Get monitoring logs with optional filtering"""
    query = db.query(MonitoringLog)

    if username:
        query = query.filter(MonitoringLog.username == username)
    if activity_type:
        query = query.filter(MonitoringLog.activity_type == activity_type)
    if days_back:
        cutoff_date = datetime.utcnow() - timedelta(days=days_back)
        query = query.filter(MonitoringLog.created_at >= cutoff_date)

    return query.order_by(desc(MonitoringLog.created_at)).offset(skip).limit(limit).all()


# ==================== Statistics ====================

def get_statistics(db: Session) -> Dict[str, Any]:
    """Get overall system statistics"""
    total_posts = db.query(func.count(Post.id)).scalar()
    total_users = db.query(func.count(User.username)).scalar()

    # Use HIGH_RISK_THRESHOLD (50) for consistency
    high_risk_posts = db.query(func.count(Post.id)).filter(Post.risk_score >= 50).scalar()
    high_risk_users = db.query(func.count(User.username)).filter(User.risk_score >= 50).scalar()

    # Risk level distribution for posts
    critical_posts = db.query(func.count(Post.id)).filter(Post.risk_level == 'critical').scalar()
    high_posts = db.query(func.count(Post.id)).filter(Post.risk_level == 'high').scalar()
    medium_posts = db.query(func.count(Post.id)).filter(Post.risk_level == 'medium').scalar()

    # Risk level distribution for users
    critical_users = db.query(func.count(User.username)).filter(User.risk_level == 'critical').scalar()
    high_users = db.query(func.count(User.username)).filter(User.risk_level == 'high').scalar()
    medium_users = db.query(func.count(User.username)).filter(User.risk_level == 'medium').scalar()

    monitored_users = db.query(func.count(User.username)).filter(User.is_monitored == True).scalar()

    return {
        "total_posts": total_posts,
        "total_users": total_users,
        "high_risk_posts": high_risk_posts,
        "high_risk_users": high_risk_users,
        "posts_by_risk": {
            "critical": critical_posts,
            "high": high_posts,
            "medium": medium_posts
        },
        "users_by_risk": {
            "critical": critical_users,
            "high": high_users,
            "medium": medium_users
        },
        "monitored_users": monitored_users,
        "timestamp": datetime.utcnow().isoformat()
    }
