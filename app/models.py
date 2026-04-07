from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class URL(Base):
    __tablename__  = "urls"

    id = Column(Integer, primary_key=True, index=True)
    short_code =  Column(String(10), unique=True, index=True, nullable=False)
    original_url = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    click_count = Column(Integer, default=0)

    clicks = relationship("Click", back_populates="url", cascade="all, delete-orphan")

class Click(Base):
    __tablename__ = "clicks"

    id = Column(Integer, primary_key=True, index=True)
    url_id = Column(Integer, ForeignKey("urls.id"), nullable=False)
    ip_address = Column(String(45))
    country = Column(String(100))
    city = Column(String(100))
    device = Column(String(50))
    browser = Column(String(50))
    os = Column(String(50))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    url = relationship("URL", back_populates="clicks")

class Admin(Base)
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

