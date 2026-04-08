from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import Admin, URL, Click
from app.schemas import AdminCreate, AdminLogin, Token, URLStats, AnalyticsSummary, ClickInfo
from app.auth import get_password_hash, verify_password, create_access_token, get_current_admin

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post("/register", response_model=dict)
def register_admin(admin_data: AdminCreate, db: Session = Depends(get_db)):
    """
    Register a new admin account.
    
    In production, this will be disable after first admin is created.
    """
    existing = db.query(Admin).filter(Admin.username == admin_data.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    hashed_password = get_password_hash(admin_data.password)
    admin = Admin(
        username=admin_data.username,
        hashed_password=hashed_password
    )
    
    db.add(admin)
    db.commit()
    db.refresh(admin)
    
    return {"message": "Admin registered successfully", "username": admin.username}


@router.post("/login", response_model=Token)
def login_admin(login_data: AdminLogin, db: Session = Depends(get_db)):
    """
    Login and get a JWT access token.
    """
    admin = db.query(Admin).filter(Admin.username == login_data.username).first()
    
    if not admin or not verify_password(login_data.password, admin.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": admin.username})
    
    return Token(access_token=access_token, token_type="bearer")


@router.get("/me")
def get_current_admin_info(admin: Admin = Depends(get_current_admin)):
    """
    Get current admin info (protected route - tests auth).
    """
    return {"username": admin.username, "message": "You have authenticated!"}

@router.get("/urls", response_model=list[dict])
def get_all_urls(
    skip: int = 0,
    limit: int = 50,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get all shortened URLs with their stats.
    Requires authentication.
    """
    urls = db.query(URL).order_by(URL.created_at.desc()).offset(skip).limit(limit).all()
    
    return [
        {
            "id": url.id,
            "short_code": url.short_code,
            "original_url": url.original_url,
            "click_count": url.click_count,
            "created_at": url.created_at.isoformat() if url.created_at else None
        }
        for url in urls
    ]


@router.get("/urls/{short_code}/stats")
def get_url_stats(
    short_code: str,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get detailed stats for a specific short URL.
    Includes recent clicks with geolocation data.
    """
    url = db.query(URL).filter(URL.short_code == short_code).first()
    
    if not url:
        raise HTTPException(status_code=404, detail="URL not found")
    
    clicks = db.query(Click).filter(Click.url_id == url.id)\
        .order_by(Click.timestamp.desc())\
        .limit(100)\
        .all()
    
    country_stats = db.query(
        Click.country,
        func.count(Click.id).label("count")
    ).filter(Click.url_id == url.id)\
        .group_by(Click.country)\
        .order_by(func.count(Click.id).desc())\
        .limit(10)\
        .all()
    
    browser_stats = db.query(
        Click.browser,
        func.count(Click.id).label("count")
    ).filter(Click.url_id == url.id)\
        .group_by(Click.browser)\
        .order_by(func.count(Click.id).desc())\
        .limit(10)\
        .all()
    
    device_stats = db.query(
        Click.device,
        func.count(Click.id).label("count")
    ).filter(Click.url_id == url.id)\
        .group_by(Click.device)\
        .order_by(func.count(Click.id).desc())\
        .all()
    
    return {
        "short_code": url.short_code,
        "original_url": url.original_url,
        "click_count": url.click_count,
        "created_at": url.created_at.isoformat() if url.created_at else None,
        "top_countries": [{"country": c[0], "clicks": c[1]} for c in country_stats],
        "top_browsers": [{"browser": b[0], "clicks": b[1]} for b in browser_stats],
        "devices": [{"device": d[0], "clicks": d[1]} for d in device_stats],
        "recent_clicks": [
            {
                "ip_address": click.ip_address,
                "country": click.country,
                "city": click.city,
                "device": click.device,
                "browser": click.browser,
                "os": click.os,
                "timestamp": click.timestamp.isoformat() if click.timestamp else None
            }
            for click in clicks
        ]
    }


@router.get("/analytics")
def get_overall_analytics(
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Get overall analytics across all URLs.
    """
    # Total counts
    total_urls = db.query(func.count(URL.id)).scalar()
    total_clicks = db.query(func.count(Click.id)).scalar()
    
    top_countries = db.query(
        Click.country,
        func.count(Click.id).label("count")
    ).group_by(Click.country)\
        .order_by(func.count(Click.id).desc())\
        .limit(10)\
        .all()
    
    top_browsers = db.query(
        Click.browser,
        func.count(Click.id).label("count")
    ).group_by(Click.browser)\
        .order_by(func.count(Click.id).desc())\
        .limit(10)\
        .all()
    
    device_breakdown = db.query(
        Click.device,
        func.count(Click.id).label("count")
    ).group_by(Click.device)\
        .order_by(func.count(Click.id).desc())\
        .all()
    
    top_urls = db.query(URL)\
        .order_by(URL.click_count.desc())\
        .limit(10)\
        .all()
    
    return {
        "total_urls": total_urls or 0,
        "total_clicks": total_clicks or 0,
        "top_countries": [{"country": c[0], "clicks": c[1]} for c in top_countries],
        "top_browsers": [{"browser": b[0], "clicks": b[1]} for b in top_browsers],
        "device_breakdown": [{"device": d[0], "clicks": d[1]} for d in device_breakdown],
        "top_urls": [
            {
                "short_code": url.short_code,
                "original_url": url.original_url,
                "clicks": url.click_count
            }
            for url in top_urls
        ]
    }


@router.delete("/urls/{short_code}")
def delete_url(
    short_code: str,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """
    Delete a shortened URL and all its click data.
    """
    url = db.query(URL).filter(URL.short_code == short_code).first()
    
    if not url:
        raise HTTPException(status_code=404, detail="URL not found")
    
    db.delete(url)
    db.commit()
    
    return {"message": f"URL '{short_code}' deleted successfully"}
