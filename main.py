from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, HttpUrl
from website_analyzer import WebsiteAnalyzer
import asyncio
from typing import Dict, Optional
import os
import logging
import aiohttp
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Website Analyzer API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins since we're serving everything from the same server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

class AnalysisRequest(BaseModel):
    url: HttpUrl
    use_ai: bool = True

class AnalysisResponse(BaseModel):
    url: str
    ux_analysis: Dict
    seo_analysis: Dict
    performance_analysis: Dict
    error: Optional[str] = None

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error: {str(exc)}")
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc)},
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unexpected error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )

@app.get("/")
async def read_root():
    return FileResponse("static/index.html")

async def fetch_website_content(url: str) -> tuple[str, bool]:
    """Fetch website content and return (content, is_blocked)"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(str(url), timeout=30) as response:
                if response.status != 200:
                    return None, True
                
                content = await response.text()
                logger.info(f"Fetched content length: {len(content)} bytes")
                
                # Check for common bot protection indicators
                soup = BeautifulSoup(content, 'html.parser')
                if any(indicator in content.lower() for indicator in [
                    'captcha', 'cloudflare', 'security check', 'bot protection',
                    'please wait', 'verifying you are human'
                ]):
                    logger.warning("Bot protection detected")
                    return None, True
                
                return content, False
    except Exception as e:
        logger.error(f"Error fetching website: {str(e)}")
        return None, True

@app.post("/analyze")
async def analyze_website(request: AnalysisRequest):
    try:
        # Fetch website content
        content, is_blocked = await fetch_website_content(request.url)
        
        if is_blocked or not content:
            return AnalysisResponse(
                url=str(request.url),
                ux_analysis={"error": "This site cannot be analyzed due to dynamic content or bot protection."},
                seo_analysis={"error": "This site cannot be analyzed due to dynamic content or bot protection."},
                performance_analysis={"error": "This site cannot be analyzed due to dynamic content or bot protection."},
                error="Site blocked or inaccessible"
            )
        
        # Create analyzer instance with required arguments
        analyzer = WebsiteAnalyzer(str(request.url), use_ai=request.use_ai)
        
        # Run analysis
        logger.info("Starting website analysis...")
        results = analyzer.run_analysis()
        logger.info(f"Analysis results: {results}")
        
        # Ensure all required keys are present
        required_keys = ["url", "ux_analysis", "seo_analysis", "performance_analysis"]
        for key in required_keys:
            if key not in results or results[key] is None:
                results[key] = {"error": "Analysis failed or incomplete."} if key != "url" else str(request.url)
        
        logger.info(f"Final response: {results}")
        return AnalysisResponse(**results)
        
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"} 