"""FastAPI application for Reddit Hate Speech Detection System API"""
from fastapi import FastAPI, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional

from src.config import setup_logging
from src.database.database import get_db, init_db
from src.database import crud, schemas

# Configure logging
logger = setup_logging()

# Create FastAPI app
app = FastAPI(
    title="Reddit Hate Speech Detection API",
    description="API for storing and querying Reddit posts and users with hate speech risk assessment",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


# ==================== Startup/Shutdown Events ====================

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    logger.info("Starting up API server...")
    init_db()
    logger.info("Database initialized")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down API server...")


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


# ==================== Statistics Endpoints ====================

@app.get("/statistics", response_model=schemas.StatisticsResponse, tags=["Statistics"])
async def get_statistics(db: Session = Depends(get_db)):
    """Get overall system statistics"""
    stats = crud.get_statistics(db)
    return stats


# ==================== Post Endpoints ====================

@app.post("/posts", response_model=schemas.PostResponse, status_code=status.HTTP_201_CREATED, tags=["Posts"])
async def create_post(post: schemas.PostCreate, db: Session = Depends(get_db)):
    """Create a new post"""
    existing_post = crud.get_post(db, post.id)
    if existing_post:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Post with id {post.id} already exists"
        )

    return crud.create_post(db, post.dict())


@app.get("/posts", response_model=List[schemas.PostResponse], tags=["Posts"])
async def get_posts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    subreddit: Optional[str] = None,
    author: Optional[str] = None,
    min_risk_score: Optional[int] = None,
    risk_level: Optional[str] = None,
    order_by: str = Query("created_date", regex="^(created_date|risk_score)$"),
    db: Session = Depends(get_db)
):
    """Get posts with optional filtering"""
    posts = crud.get_posts(
        db,
        skip=skip,
        limit=limit,
        subreddit=subreddit,
        author=author,
        min_risk_score=min_risk_score,
        risk_level=risk_level,
        order_by=order_by
    )
    return posts


@app.get("/posts/high-risk", response_model=List[schemas.PostResponse], tags=["Posts"])
async def get_high_risk_posts(
    min_score: int = Query(5, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get high-risk posts"""
    return crud.get_high_risk_posts(db, min_score=min_score, limit=limit)


@app.get("/posts/{post_id}", response_model=schemas.PostResponse, tags=["Posts"])
async def get_post(post_id: str, db: Session = Depends(get_db)):
    """Get a specific post by ID"""
    post = crud.get_post(db, post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post {post_id} not found"
        )
    return post


@app.patch("/posts/{post_id}", response_model=schemas.PostResponse, tags=["Posts"])
async def update_post(
    post_id: str,
    post_update: schemas.PostUpdate,
    db: Session = Depends(get_db)
):
    """Update a post"""
    updated_post = crud.update_post(db, post_id, post_update.dict(exclude_unset=True))
    if not updated_post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post {post_id} not found"
        )
    return updated_post


@app.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Posts"])
async def delete_post(post_id: str, db: Session = Depends(get_db)):
    """Delete a post"""
    success = crud.delete_post(db, post_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post {post_id} not found"
        )


# ==================== User Endpoints ====================

@app.post("/users", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED, tags=["Users"])
async def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """Create a new user"""
    existing_user = crud.get_user(db, user.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User {user.username} already exists"
        )

    return crud.create_user(db, user.dict())


@app.get("/users", response_model=List[schemas.UserResponse], tags=["Users"])
async def get_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    min_risk_score: Optional[int] = None,
    risk_level: Optional[str] = None,
    is_monitored: Optional[bool] = None,
    order_by: str = Query("risk_score", regex="^(risk_score|updated_at)$"),
    db: Session = Depends(get_db)
):
    """Get users with optional filtering"""
    users = crud.get_users(
        db,
        skip=skip,
        limit=limit,
        min_risk_score=min_risk_score,
        risk_level=risk_level,
        is_monitored=is_monitored,
        order_by=order_by
    )
    return users


@app.get("/users/high-risk", response_model=List[schemas.UserResponse], tags=["Users"])
async def get_high_risk_users(
    min_score: int = Query(50, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get high-risk users (default threshold: 50)"""
    return crud.get_high_risk_users(db, min_score=min_score, limit=limit)


@app.get("/users/monitored", response_model=List[schemas.UserResponse], tags=["Users"])
async def get_monitored_users(db: Session = Depends(get_db)):
    """Get all monitored users"""
    return crud.get_monitored_users(db)


@app.get("/users/{username}", response_model=schemas.UserResponse, tags=["Users"])
async def get_user(username: str, db: Session = Depends(get_db)):
    """Get a specific user by username"""
    user = crud.get_user(db, username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {username} not found"
        )
    return user


@app.patch("/users/{username}", response_model=schemas.UserResponse, tags=["Users"])
async def update_user(
    username: str,
    user_update: schemas.UserUpdate,
    db: Session = Depends(get_db)
):
    """Update a user"""
    updated_user = crud.update_user(db, username, user_update.dict(exclude_unset=True))
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {username} not found"
        )
    return updated_user


@app.delete("/users/{username}", status_code=status.HTTP_204_NO_CONTENT, tags=["Users"])
async def delete_user(username: str, db: Session = Depends(get_db)):
    """Delete a user"""
    success = crud.delete_user(db, username)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {username} not found"
        )


# ==================== Bulk Import Endpoints ====================

@app.post("/bulk/posts", status_code=status.HTTP_201_CREATED, tags=["Bulk Import"])
async def bulk_create_posts(posts: List[schemas.PostCreate], db: Session = Depends(get_db)):
    """Bulk create posts"""
    created_count = 0
    skipped_count = 0
    errors = []

    for post in posts:
        try:
            existing_post = crud.get_post(db, post.id)
            if not existing_post:
                crud.create_post(db, post.model_dump())
                created_count += 1
            else:
                skipped_count += 1
        except Exception as e:
            errors.append({"post_id": post.id, "error": str(e)})

    return {
        "created": created_count,
        "skipped": skipped_count,
        "errors": errors
    }


@app.post("/bulk/users", status_code=status.HTTP_201_CREATED, tags=["Bulk Import"])
async def bulk_create_users(users: List[schemas.UserCreate], db: Session = Depends(get_db)):
    """Bulk create users"""
    created_count = 0
    skipped_count = 0
    errors = []

    for user in users:
        try:
            existing_user = crud.get_user(db, user.username)
            if not existing_user:
                crud.create_user(db, user.model_dump())
                created_count += 1
            else:
                skipped_count += 1
        except Exception as e:
            errors.append({"username": user.username, "error": str(e)})

    return {
        "created": created_count,
        "skipped": skipped_count,
        "errors": errors
    }


# ==================== Alert Endpoints ====================

@app.post("/alerts", response_model=schemas.AlertResponse, status_code=status.HTTP_201_CREATED, tags=["Alerts"])
async def create_alert(alert: schemas.AlertCreate, db: Session = Depends(get_db)):
    """Create a new alert"""
    return crud.create_alert(db, alert.model_dump())


@app.get("/alerts", response_model=List[schemas.AlertResponse], tags=["Alerts"])
async def get_alerts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    username: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    days_back: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get alerts with optional filtering"""
    return crud.get_alerts(
        db,
        skip=skip,
        limit=limit,
        username=username,
        severity=severity,
        status=status,
        days_back=days_back
    )


@app.get("/alerts/{alert_id}", response_model=schemas.AlertResponse, tags=["Alerts"])
async def get_alert(alert_id: int, db: Session = Depends(get_db)):
    """Get a specific alert by ID"""
    alert = crud.get_alert(db, alert_id)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert {alert_id} not found"
        )
    return alert


@app.patch("/alerts/{alert_id}", response_model=schemas.AlertResponse, tags=["Alerts"])
async def update_alert(
    alert_id: int,
    alert_update: schemas.AlertUpdate,
    db: Session = Depends(get_db)
):
    """Update an alert"""
    updated_alert = crud.update_alert(db, alert_id, alert_update.model_dump(exclude_unset=True))
    if not updated_alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert {alert_id} not found"
        )
    return updated_alert


@app.delete("/alerts/{alert_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Alerts"])
async def delete_alert(alert_id: int, db: Session = Depends(get_db)):
    """Delete an alert"""
    success = crud.delete_alert(db, alert_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert {alert_id} not found"
        )


# ==================== Monitoring Log Endpoints ====================

@app.post("/monitoring-logs", response_model=schemas.MonitoringLogResponse, status_code=status.HTTP_201_CREATED, tags=["Monitoring"])
async def create_monitoring_log(log: schemas.MonitoringLogCreate, db: Session = Depends(get_db)):
    """Create a new monitoring log entry"""
    return crud.create_monitoring_log(db, log.model_dump())


@app.get("/monitoring-logs", response_model=List[schemas.MonitoringLogResponse], tags=["Monitoring"])
async def get_monitoring_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    username: Optional[str] = None,
    activity_type: Optional[str] = None,
    days_back: Optional[int] = Query(7, ge=1),
    db: Session = Depends(get_db)
):
    """Get monitoring logs with optional filtering"""
    return crud.get_monitoring_logs(
        db,
        username=username,
        activity_type=activity_type,
        days_back=days_back,
        skip=skip,
        limit=limit
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)