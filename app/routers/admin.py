from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth import (
    create_access_token,
    generate_api_key,
    get_current_admin,
    get_password_hash,
    verify_password,
)
from app.database import get_db
from app.models import APIKey, Admin, Click, URL
from app.schemas import (
    APIKeyCreate,
    APIKeyCreated,
    APIKeyListItem,
    AdminCreate,
    AdminLogin,
    Token,
)

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.post("/register", response_model=dict)
def register_admin(admin_data: AdminCreate, db: Session = Depends(get_db)):
    existing = db.query(Admin).filter(Admin.username == admin_data.username).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )

    admin = Admin(
        username=admin_data.username,
        hashed_password=get_password_hash(admin_data.password),
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    return {"message": "Admin registered successfully", "username": admin.username}


@router.post("/login", response_model=Token)
def login_admin(login_data: AdminLogin, db: Session = Depends(get_db)):
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
    return {"username": admin.username, "message": "You are authenticated"}


@router.get("/urls", response_model=list[dict])
def get_all_urls(
    skip: int = 0,
    limit: int = 50,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    urls = db.query(URL).order_by(URL.created_at.desc()).offset(skip).limit(limit).all()
    return [
        {
            "id": url.id,
            "short_code": url.short_code,
            "original_url": url.original_url,
            "click_count": url.click_count,
            "created_at": url.created_at.isoformat() if url.created_at else None,
        }
        for url in urls
    ]


@router.get("/urls/{short_code}/stats")
def get_url_stats(
    short_code: str,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    url = db.query(URL).filter(URL.short_code == short_code).first()
    if not url:
        raise HTTPException(status_code=404, detail="URL not found")

    clicks = (
        db.query(Click)
        .filter(Click.url_id == url.id)
        .order_by(Click.timestamp.desc())
        .limit(100)
        .all()
    )

    country_stats = (
        db.query(Click.country, func.count(Click.id).label("count"))
        .filter(Click.url_id == url.id)
        .group_by(Click.country)
        .order_by(func.count(Click.id).desc())
        .limit(10)
        .all()
    )
    browser_stats = (
        db.query(Click.browser, func.count(Click.id).label("count"))
        .filter(Click.url_id == url.id)
        .group_by(Click.browser)
        .order_by(func.count(Click.id).desc())
        .limit(10)
        .all()
    )
    device_stats = (
        db.query(Click.device, func.count(Click.id).label("count"))
        .filter(Click.url_id == url.id)
        .group_by(Click.device)
        .order_by(func.count(Click.id).desc())
        .all()
    )
    referrer_stats = (
        db.query(Click.referer, func.count(Click.id).label("count"))
        .filter(Click.url_id == url.id, Click.referer.isnot(None), Click.referer != "")
        .group_by(Click.referer)
        .order_by(func.count(Click.id).desc())
        .limit(10)
        .all()
    )
    utm_source_stats = (
        db.query(Click.utm_source, func.count(Click.id).label("count"))
        .filter(
            Click.url_id == url.id, Click.utm_source.isnot(None), Click.utm_source != ""
        )
        .group_by(Click.utm_source)
        .order_by(func.count(Click.id).desc())
        .limit(10)
        .all()
    )
    utm_medium_stats = (
        db.query(Click.utm_medium, func.count(Click.id).label("count"))
        .filter(
            Click.url_id == url.id, Click.utm_medium.isnot(None), Click.utm_medium != ""
        )
        .group_by(Click.utm_medium)
        .order_by(func.count(Click.id).desc())
        .limit(10)
        .all()
    )
    utm_campaign_stats = (
        db.query(Click.utm_campaign, func.count(Click.id).label("count"))
        .filter(
            Click.url_id == url.id,
            Click.utm_campaign.isnot(None),
            Click.utm_campaign != "",
        )
        .group_by(Click.utm_campaign)
        .order_by(func.count(Click.id).desc())
        .limit(10)
        .all()
    )

    return {
        "short_code": url.short_code,
        "original_url": url.original_url,
        "click_count": url.click_count,
        "created_at": url.created_at.isoformat() if url.created_at else None,
        "top_countries": [{"country": c[0], "clicks": c[1]} for c in country_stats],
        "top_browsers": [{"browser": b[0], "clicks": b[1]} for b in browser_stats],
        "top_devices": [{"device": d[0], "clicks": d[1]} for d in device_stats],
        "top_referrers": [{"referer": r[0], "clicks": r[1]} for r in referrer_stats],
        "top_utm_sources": [
            {"utm_source": s[0], "clicks": s[1]} for s in utm_source_stats
        ],
        "top_utm_mediums": [
            {"utm_medium": m[0], "clicks": m[1]} for m in utm_medium_stats
        ],
        "top_utm_campaigns": [
            {"utm_campaign": c[0], "clicks": c[1]} for c in utm_campaign_stats
        ],
        "recent_clicks": [
            {
                "ip_address": click.ip_address,
                "country": click.country,
                "city": click.city,
                "device": click.device,
                "browser": click.browser,
                "os": click.os,
                "referer": click.referer,
                "utm_source": click.utm_source,
                "utm_medium": click.utm_medium,
                "utm_campaign": click.utm_campaign,
                "timestamp": click.timestamp.isoformat() if click.timestamp else None,
            }
            for click in clicks
        ],
    }


@router.get("/analytics")
def get_overall_analytics(
    admin: Admin = Depends(get_current_admin), db: Session = Depends(get_db)
):
    total_urls = db.query(func.count(URL.id)).scalar() or 0
    total_clicks = db.query(func.count(Click.id)).scalar() or 0

    top_countries = (
        db.query(Click.country, func.count(Click.id).label("count"))
        .group_by(Click.country)
        .order_by(func.count(Click.id).desc())
        .limit(10)
        .all()
    )
    top_browsers = (
        db.query(Click.browser, func.count(Click.id).label("count"))
        .group_by(Click.browser)
        .order_by(func.count(Click.id).desc())
        .limit(10)
        .all()
    )
    top_devices = (
        db.query(Click.device, func.count(Click.id).label("count"))
        .group_by(Click.device)
        .order_by(func.count(Click.id).desc())
        .all()
    )
    top_referrers = (
        db.query(Click.referer, func.count(Click.id).label("count"))
        .filter(Click.referer.isnot(None), Click.referer != "")
        .group_by(Click.referer)
        .order_by(func.count(Click.id).desc())
        .limit(10)
        .all()
    )
    top_utm_sources = (
        db.query(Click.utm_source, func.count(Click.id).label("count"))
        .filter(Click.utm_source.isnot(None), Click.utm_source != "")
        .group_by(Click.utm_source)
        .order_by(func.count(Click.id).desc())
        .limit(10)
        .all()
    )
    top_utm_mediums = (
        db.query(Click.utm_medium, func.count(Click.id).label("count"))
        .filter(Click.utm_medium.isnot(None), Click.utm_medium != "")
        .group_by(Click.utm_medium)
        .order_by(func.count(Click.id).desc())
        .limit(10)
        .all()
    )
    top_utm_campaigns = (
        db.query(Click.utm_campaign, func.count(Click.id).label("count"))
        .filter(Click.utm_campaign.isnot(None), Click.utm_campaign != "")
        .group_by(Click.utm_campaign)
        .order_by(func.count(Click.id).desc())
        .limit(10)
        .all()
    )
    top_urls = db.query(URL).order_by(URL.click_count.desc()).limit(10).all()

    return {
        "total_urls": total_urls,
        "total_clicks": total_clicks,
        "top_countries": [{"country": c[0], "clicks": c[1]} for c in top_countries],
        "top_browsers": [{"browser": b[0], "clicks": b[1]} for b in top_browsers],
        "top_devices": [{"device": d[0], "clicks": d[1]} for d in top_devices],
        "top_referrers": [{"referer": r[0], "clicks": r[1]} for r in top_referrers],
        "top_utm_sources": [
            {"utm_source": s[0], "clicks": s[1]} for s in top_utm_sources
        ],
        "top_utm_mediums": [
            {"utm_medium": m[0], "clicks": m[1]} for m in top_utm_mediums
        ],
        "top_utm_campaigns": [
            {"utm_campaign": c[0], "clicks": c[1]} for c in top_utm_campaigns
        ],
        "top_urls": [
            {
                "short_code": url.short_code,
                "original_url": url.original_url,
                "clicks": url.click_count,
            }
            for url in top_urls
        ],
    }


@router.delete("/urls/{short_code}")
def delete_url(
    short_code: str,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    url = db.query(URL).filter(URL.short_code == short_code).first()
    if not url:
        raise HTTPException(status_code=404, detail="URL not found")
    db.delete(url)
    db.commit()
    return {"message": f"URL '{short_code}' deleted successfully"}


@router.post("/api-keys", response_model=APIKeyCreated)
def create_api_key(
    payload: APIKeyCreate,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    raw_key, key_hash, key_prefix = generate_api_key()
    row = APIKey(name=payload.name, key_hash=key_hash, key_prefix=key_prefix)
    db.add(row)
    db.commit()
    db.refresh(row)
    return APIKeyCreated(
        id=row.id,
        name=row.name,
        api_key=raw_key,
        key_prefix=row.key_prefix,
        is_active=row.is_active,
        created_at=row.created_at,
    )


@router.get("/api-keys", response_model=list[APIKeyListItem])
def list_api_keys(
    admin: Admin = Depends(get_current_admin), db: Session = Depends(get_db)
):
    return db.query(APIKey).order_by(APIKey.created_at.desc()).all()


@router.delete("/api-keys/{key_id}")
def revoke_api_key(
    key_id: int,
    admin: Admin = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    row = db.query(APIKey).filter(APIKey.id == key_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="API key not found")
    row.is_active = False
    db.commit()
    return {"message": "API key revoked"}
