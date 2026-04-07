from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import Optional

class URLCreate(BaseModel):
    url: HttpUrl

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
    click_count: str
    created_at: str
    recent_clicks: list[ClickInfo] = []

    class Config:
        from_attributes = True

class AnalyticsSummary(BaseModel):
    total_urls: int
    total_clicks: int
    total_countries: list[dict]
    total_browsers:  list[dict]
    top_devices: list[dict]