"""
FastAPI application entry point for Bharat Bazaar AI.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db
from app.seed import seed_database
from app.api.commerce import router as commerce_router
from app.api.discovery import router as discovery_router

app = FastAPI(
    title="Bharat Bazaar AI - Commerce API",
    description=(
        "Agent-readable commerce API that makes a merchant's catalog "
        "discoverable and transactable by AI shopping agents. "
        "Discover tools at /.well-known/ai-commerce.json"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS for Streamlit and other frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(commerce_router)
app.include_router(discovery_router)


@app.on_event("startup")
def on_startup():
    """Initialize database and seed demo data on startup."""
    init_db()
    seed_database()


@app.get("/", tags=["Health"])
def root():
    return {
        "service": "Bharat Bazaar AI - Commerce API",
        "status": "running",
        "merchant": settings.MERCHANT_NAME,
        "discovery": "/.well-known/ai-commerce.json",
        "docs": "/docs",
        "razorpay_enabled": settings.razorpay_enabled,
        "llm_enabled": settings.llm_enabled,
    }


@app.get("/health", tags=["Health"])
def health():
    return {"status": "healthy"}
