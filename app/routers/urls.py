from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import URL
from app.schemas import URLCreate, URLResponse
from app.utils import generate_unique_short_code
from app.config import get_settings

router = APIRouter(tags=["URLs"])
settings = get_settings()

@router.post("/shorten", response_model=URLResponse)
def shorten_url(url_data: URLCreate, db: Session = Depends(get_db)):
    """
    Create a shortened URL

    - Accepts any valid URL
    - Returns a unique short code
    """

    short_code = generate_unique_short_code(db)

    db_url = URL(
        short_code=short_code,
        original_url=str(url_data.url)
    )

    db.add(db_url)
    db.commit()
    db.refresh(db_url)

    return URLResponse(
        short_code=db_url.short_code,
        short_url=f"{settings.BASE_URL}/{db_url.short_code}",
        original_url=db_url.original_url,
        created_at=db_url.created_at
    )

@router.get("/{short_code}")
def redirect_to_url(short_code: str, db: Session = Depends(get_db)):
    """
    Redirect to the original URL

    - Looks up the short code
    - Increments click count
    - Redirects to original URL
    """
    db_url = db.query(URL).filter(URL.short_code == short_code).first()

    if not db_url:
        raise HTTPException(status_code=404, detail="Short URL not found")
    
    db_url.click_count += 1
    db.commit()

    return RedirectResponse(url=db_url.original_url, status_code=307)


