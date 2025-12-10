from fastapi import FastAPI, HTTPException, Depends, Security, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import logging
from app.api import trade, market, ai, auth
from app.core.nexus_core.market_intake import MarketIntake

# Initialize Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NexusCloudBackend")

app = FastAPI(
    title="Nexus AI Cloud Backend",
    description="High-performance trading backend powered by FastAPI and Google Cloud",
    version="2.0.0"
)

# CORS Configuration
origins = [
    "http://localhost:3000",
    "http://localhost:8000",
    "https://nexus-ai-frontend.web.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Core
market_intake = MarketIntake()

# Routes
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(market.router, prefix="/market", tags=["Market Data"])
app.include_router(trade.router, prefix="/trade", tags=["Trading"])
app.include_router(ai.router, prefix="/ai", tags=["AI Intelligence"])

@app.get("/")
def health_check():
    return {"status": "online", "version": "2.0.0", "backend": "FastAPI"}
