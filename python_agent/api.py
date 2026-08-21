"""
PriceBD Automation Agent – FastAPI wrapper
Ready for Vercel / local / any free host
"""

import os
import logging
from typing import Optional, Literal
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

from main import run_agent, get_brand_info

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PriceBD-API")

app = FastAPI(
    title="PriceBD Zero-Cost Automation Agent",
    description="SEO • Content • Social • Reply automation for https://pricebd.lovable.app",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GoalType = Literal["full_daily_run", "seo_only", "content_only", "social_only", "reply_only"]

class RunRequest(BaseModel):
    goal: GoalType = Field(default="full_daily_run", description="Which agents to run")

class RunResponse(BaseModel):
    success: bool
    report: str
    seo_insights: dict
    content_ideas: list
    social_posts: list
    reply_suggestions: list
    actions_taken: list
    brand: dict
    error: Optional[str] = None

@app.get("/")
def root():
    brand = get_brand_info()
    return {
        "status": "online",
        "service": "PriceBD Automation Agent",
        "brand": brand["name"],
        "url": brand["url"],
        "version": "2.0.0",
        "docs": "/docs",
        "endpoints": {
            "POST /run": "Run the full or partial agent",
            "GET /health": "Health check",
            "GET /goals": "List available goals",
            "GET /brand": "Current brand config"
        }
    }

@app.get("/health")
def health():
    from datetime import datetime
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

@app.get("/brand")
def brand_info():
    return get_brand_info()

@app.get("/goals")
def list_goals():
    return {
        "goals": [
            {"id": "full_daily_run", "description": "SEO → Content → Social → Reply → Report"},
            {"id": "seo_only", "description": "Only SEO analysis"},
            {"id": "content_only", "description": "Only content generation"},
            {"id": "social_only", "description": "Only social post refinement"},
            {"id": "reply_only", "description": "Only reply templates"}
        ]
    }

@app.post("/run", response_model=RunResponse)
def run(request: RunRequest):
    logger.info(f"Received run request | goal={request.goal}")
    try:
        result = run_agent(goal=request.goal)
        return RunResponse(
            success=result.get("success", False),
            report=result.get("report", ""),
            seo_insights=result.get("seo_insights", {}),
            content_ideas=result.get("content_ideas", []),
            social_posts=result.get("social_posts", []),
            reply_suggestions=result.get("reply_suggestions", []),
            actions_taken=result.get("actions_taken", []),
            brand=result.get("brand", {}),
            error=result.get("error")
        )
    except Exception as e:
        logger.exception("API /run failed")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/run")
def run_alias(request: RunRequest):
    return run(request)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("api:app", host="0.0.0.0", port=port, reload=True)
