from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.database import engine, Base
from app.config import get_settings
from app.routers import urls, admin

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    print("Data tables made")
    yield
    print("Shutting down")


app = FastAPI(
    title="Link Shortener API",
    description="A Link Shortener with click and geolocation tracking",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(urls.router)
app.include_router(admin.router)


@app.get("/")
def root():
    return {"status": "online", "message": "L-S-API is up!", "docs": "/docs"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
