from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import URL, Click, APIKey
from sqlalchemy.exc import IntegrityError
from app.schemas import (
    URLCreate,
    URLResponse,
    BulkURLCreate,
    BulkURLResponse,
    BulkURLItemResult,
)
from app.utils import (
    generate_unique_short_code,
    validate_custom_code,
    is_code_available,
)
from app.config import get_settings
from app.geolocation import get_location_from_ip, get_client_ip
from app.user_agent_parser import parse_user_agent
from app.auth import get_api_key_client

router = APIRouter(tags=["URLs"])
settings = get_settings()


@router.post("/shorten", response_model=URLResponse)
def shorten_url(
    url_data: URLCreate,
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(get_api_key_client),
):
    """
    Create a shortened URL

    - Accepts any valid URL
    - Returns a unique short code
    - Accepts a custom code
    """
    if url_data.custom_code:
        custom_code = url_data.custom_code.strip()

        is_valid, error_msg = validate_custom_code(custom_code)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)

        if not is_code_available(db, custom_code):
            raise HTTPException(
                status_code=409, detail=f"Short code '{custom_code}' is already taken"
            )

        short_code = custom_code
    else:
        short_code = generate_unique_short_code(db)

    db_url = URL(short_code=short_code, original_url=str(url_data.url))
    db.add(db_url)
    db.commit()
    db.refresh(db_url)

    return URLResponse(
        short_code=db_url.short_code,
        short_url=f"{settings.BASE_URL}/{db_url.short_code}",
        original_url=db_url.original_url,
        created_at=db_url.created_at,
    )


@router.post("/shorten/bulk", response_model=BulkURLResponse)
def shorten_urls_bulk(
    payload: BulkURLCreate,
    db: Session = Depends(get_db),
    api_key: APIKey = Depends(get_api_key_client),
):
    if not payload.items:
        raise HTTPException(status_code=400, detail="items cannot be empty")
    if len(payload.items) > 50:
        raise HTTPException(status_code=400, detail="Max 50 URLs per request")

    results: list[BulkURLItemResult] = []
    success_count = 0

    for idx, item in enumerate(payload.items):
        try:
            if item.custom_code:
                custom_code = item.custom_code.strip()
                is_valid, error_msg = validate_custom_code(custom_code)
                if not is_valid:
                    raise ValueError(error_msg)
                if not is_code_available(db, custom_code):
                    raise ValueError(f"Short code '{custom_code}' is already taken")
                short_code = custom_code
            else:
                short_code = generate_unique_short_code(db)

            db_url = URL(
                short_code=short_code,
                original_url=str(item.url),
            )
            db.add(db_url)
            db.commit()
            db.refresh(db_url)

            results.append(
                BulkURLItemResult(
                    index=idx,
                    original_url=str(item.url),
                    success=True,
                    short_code=db_url.short_code,
                    short_url=f"{settings.BASE_URL}/{db_url.short_code}",
                )
            )
            success_count += 1

        except IntegrityError:
            db.rollback()
            results.append(
                BulkURLItemResult(
                    index=idx,
                    original_url=str(item.url),
                    success=False,
                    error="Database conflict (likely duplicate short code)",
                )
            )
        except ValueError as exc:
            db.rollback()
            results.append(
                BulkURLItemResult(
                    index=idx,
                    original_url=str(item.url),
                    success=False,
                    error=str(exc),
                )
            )
        except Exception:
            db.rollback()
            results.append(
                BulkURLItemResult(
                    index=idx,
                    original_url=str(item.url),
                    success=False,
                    error="Unexpected error while shortening URL",
                )
            )

    total = len(payload.items)
    return BulkURLResponse(
        total=total,
        success_count=success_count,
        failure_count=total - success_count,
        results=results,
    )


@router.get("/{short_code}")
async def redirect_to_url(
    short_code: str, request: Request, db: Session = Depends(get_db)
):
    """
    Redirect to the original URL

    - Looks up the short code
    - Increments click count
    - Tracks user with their data
    - Redirects to original URL
    """
    db_url = db.query(URL).filter(URL.short_code == short_code).first()

    if not db_url:
        raise HTTPException(status_code=404, detail="Short URL not found")

    client_ip = get_client_ip(request)
    user_agent = request.headers.get("User-Agent", "")

    ua_info = parse_user_agent(user_agent)

    geo_info = await get_location_from_ip(client_ip)
    referer = request.headers.get("referer")
    utm_source = request.query_params.get("utm_source")
    utm_medium = request.query_params.get("utm_medium")
    utm_campaign = request.query_params.get("utm_campaign")

    click = Click(
        url_id=db_url.id,
        ip_address=client_ip,
        country=geo_info.get("country", "Unknown"),
        city=geo_info.get("city", "Unknown"),
        device=ua_info.get("device", "Unknown"),
        browser=ua_info.get("browser", "Unknown"),
        os=ua_info.get("os", "Unknown"),
        referer=referer,
        utm_source=utm_source,
        utm_medium=utm_medium,
        utm_campaign=utm_campaign,
    )
    db.add(click)
    db_url.click_count += 1
    db.commit()

    return RedirectResponse(url=db_url.original_url, status_code=307)
