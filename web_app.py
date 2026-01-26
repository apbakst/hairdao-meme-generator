"""
HairDAO Meme Generator - Web UI
FastAPI + Jinja2 web interface for generating and browsing memes.
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from config import OUTPUT_DIR, DATA_DIR, MEME_STYLES
from meme_generator import generate_meme_concept
from image_creator import create_meme_from_concept, save_meme
from trend_analyzer import get_fresh_trending_memes, load_trending_memes
from scraper import load_website_content
from discord_scanner import load_discord_content

# Initialize FastAPI app
app = FastAPI(
    title="HairDAO Meme Generator",
    description="AI-powered meme generation for the HairDAO community",
    version="1.0.0"
)

# Setup templates
TEMPLATES_DIR = Path(__file__).parent / "templates"
TEMPLATES_DIR.mkdir(exist_ok=True)
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Serve static files (output memes)
OUTPUT_DIR.mkdir(exist_ok=True)
app.mount("/memes", StaticFiles(directory=str(OUTPUT_DIR)), name="memes")

# Serve static assets
STATIC_DIR = Path(__file__).parent / "static"
STATIC_DIR.mkdir(exist_ok=True)
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


def get_recent_memes(limit: int = 20) -> list:
    """Get recently generated memes from output directory."""
    memes = []
    if OUTPUT_DIR.exists():
        files = sorted(OUTPUT_DIR.glob("*.png"), key=os.path.getmtime, reverse=True)
        files += sorted(OUTPUT_DIR.glob("*.jpg"), key=os.path.getmtime, reverse=True)
        files = sorted(files, key=os.path.getmtime, reverse=True)[:limit]
        
        for f in files:
            memes.append({
                "filename": f.name,
                "url": f"/memes/{f.name}",
                "created": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
                "size_kb": round(f.stat().st_size / 1024, 1)
            })
    return memes


def get_trending_topics() -> list:
    """Get cached trending topics with meme potential."""
    memes = load_trending_memes()
    topics = []
    
    for meme in memes[:10]:
        source_trend = meme.get("source_trend", {})
        topics.append({
            "topic": source_trend.get("topic", meme.get("trend_reference", "Unknown")),
            "relevance": source_trend.get("relevance_score", 5),
            "meme_angle": source_trend.get("meme_angle", ""),
            "suggested_caption": meme.get("caption", source_trend.get("suggested_caption", ""))
        })
    
    return topics


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Homepage with trending topics and recent memes."""
    trending = get_trending_topics()
    recent_memes = get_recent_memes(limit=8)
    
    return templates.TemplateResponse("home.html", {
        "request": request,
        "trending_topics": trending,
        "recent_memes": recent_memes,
        "page_title": "HairDAO Meme Generator"
    })


@app.get("/generate", response_class=HTMLResponse)
async def generate_page(request: Request):
    """Meme generation page."""
    return templates.TemplateResponse("generate.html", {
        "request": request,
        "styles": MEME_STYLES,
        "page_title": "Generate Meme"
    })


@app.post("/generate", response_class=HTMLResponse)
async def generate_meme(
    request: Request,
    topic: str = Form(None),
    style: str = Form("modern_caption")
):
    """Generate a new meme based on topic and style."""
    try:
        # Load context data
        website_data = load_website_content()
        discord_data = load_discord_content()
        
        # If topic provided, inject it into the context
        if topic:
            # Add custom topic to the context
            if "hairdao" not in website_data:
                website_data["hairdao"] = {}
            website_data["hairdao"]["custom_topic"] = topic
            website_data["hairdao"]["taglines"] = website_data.get("hairdao", {}).get("taglines", []) + [topic]
        
        # Generate concept
        concept = generate_meme_concept(website_data, discord_data, style)
        
        # If topic was provided, try to incorporate it
        if topic and concept.get("caption"):
            # The AI should have incorporated it, but let's ensure
            pass
        
        # Create image
        img = create_meme_from_concept(concept)
        
        # Save meme
        output_path = save_meme(img, concept)
        filename = Path(output_path).name
        
        return templates.TemplateResponse("generate.html", {
            "request": request,
            "styles": MEME_STYLES,
            "page_title": "Generate Meme",
            "generated_meme": {
                "url": f"/memes/{filename}",
                "filename": filename,
                "concept": concept
            },
            "selected_style": style,
            "topic": topic
        })
        
    except Exception as e:
        return templates.TemplateResponse("generate.html", {
            "request": request,
            "styles": MEME_STYLES,
            "page_title": "Generate Meme",
            "error": str(e),
            "selected_style": style,
            "topic": topic
        })


@app.get("/gallery", response_class=HTMLResponse)
async def gallery(request: Request, page: int = 1, per_page: int = 20):
    """Browse all generated memes."""
    all_memes = get_recent_memes(limit=1000)
    
    # Pagination
    total = len(all_memes)
    total_pages = (total + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    memes = all_memes[start:end]
    
    return templates.TemplateResponse("gallery.html", {
        "request": request,
        "memes": memes,
        "page": page,
        "total_pages": total_pages,
        "total_memes": total,
        "page_title": "Meme Gallery"
    })


@app.get("/api/trending")
async def api_trending():
    """API endpoint for trending topics."""
    return get_trending_topics()


@app.get("/api/memes")
async def api_memes(limit: int = 20):
    """API endpoint for recent memes."""
    return get_recent_memes(limit=limit)


@app.post("/api/generate")
async def api_generate(topic: Optional[str] = None, style: str = "modern_caption"):
    """API endpoint to generate a meme."""
    try:
        website_data = load_website_content()
        discord_data = load_discord_content()
        
        if topic:
            if "hairdao" not in website_data:
                website_data["hairdao"] = {}
            website_data["hairdao"]["taglines"] = website_data.get("hairdao", {}).get("taglines", []) + [topic]
        
        concept = generate_meme_concept(website_data, discord_data, style)
        img = create_meme_from_concept(concept)
        output_path = save_meme(img, concept)
        filename = Path(output_path).name
        
        return {
            "success": True,
            "meme_url": f"/memes/{filename}",
            "filename": filename,
            "concept": concept
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/refresh-trends")
async def api_refresh_trends():
    """API endpoint to refresh trending topics."""
    try:
        memes = get_fresh_trending_memes(force_refresh=True, count=5)
        return {
            "success": True,
            "count": len(memes),
            "topics": get_trending_topics()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/download/{filename}")
async def download_meme(filename: str):
    """Download a meme file."""
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Meme not found")
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="image/png"
    )


@app.delete("/api/memes/{filename}")
async def delete_meme(filename: str):
    """Delete a meme file."""
    file_path = OUTPUT_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Meme not found")
    
    file_path.unlink()
    return {"success": True, "message": f"Deleted {filename}"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
