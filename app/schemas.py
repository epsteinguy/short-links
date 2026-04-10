from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class URLCreate(BaseModel):
    url: HttpUrl
    custom_code: Optional[str] = None
    
class URLResponse(BaseModel):
    short_code: str
    short_url: str 
    original_url: str
    created_at: datetime

    class Config: 
        from_attributes = True

class ClickInfo(BaseModel):
    ip_address: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    device: Optional[str] = None
    browser: Optional[str] = None
    os: Optional[str] = None
    referer: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    timestamp: datetime

    class Config:
        from_attributes = True

class AdminCreate(BaseModel):
    username: str
    password: str

class AdminLogin(BaseModel):
    username: str
    password: str

class URLStats(BaseModel):
    short_code: str
    original_url: str
    click_count: int
    created_at: datetime
    recent_clicks: list[ClickInfo] = []

    class Config:
        from_attributes = True

class AnalyticsSummary(BaseModel):
    total_urls: int
    total_clicks: int
    top_countries: list[dict]
    top_browsers:  list[dict]
    top_devices: list[dict]
    top_referrers: list[dict]
    top_utm_sources: list[dict]
    top_utm_mediums: list[dict]
    top_utm_campaigns: list[dict]

class BulkURLItem(BaseModel):
    url: HttpUrl
    custom_code: Optional[str] = None


class BulkURLCreate(BaseModel):
    items: list[BulkURLItem]


class BulkURLItemResult(BaseModel):
    index: int
    original_url: str
    success: bool
    short_code: Optional[str] = None
    short_url: Optional[str] = None
    error: Optional[str] = None


class BulkURLResponse(BaseModel):
    total: int
    success_count: int
    failure_count: int
    results: list[BulkURLItemResult]

class APIKeyCreate(BaseModel):
    name: str

class APIKeyCreated(BaseModel):
    id: int
    name: str
    api_key: str
    key_prefix: str
    is_active: bool
    created_at: datetime

class APIKeyListItem(BaseModel):
    id: int
    name: str
    key_prefix: str
    is_active: bool
    request_count: int
    created_at: datetime
    last_used_at: Optional[datetime] = None

    class Config:
        from_attributes = True
