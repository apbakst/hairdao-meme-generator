"""
HairDAO Meme Generator - Imgflip-style Web UI
FastAPI backend with vanilla JS frontend for classic meme generation.
"""
import io
import os
import re
from pathlib import Path
from typing import Optional
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from PIL import Image, ImageDraw, ImageFont
import textwrap

# Initialize FastAPI app
app = FastAPI(
    title="HairDAO Meme Generator",
    description="Imgflip-style meme generator for HairDAO",
    version="2.0.0"
)

# Paths
BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
MEME_TEMPLATES_DIR = TEMPLATES_DIR / "memes"
OUTPUT_DIR = BASE_DIR / "output"
FONTS_DIR = BASE_DIR / "fonts"

# Create directories
TEMPLATES_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
FONTS_DIR.mkdir(exist_ok=True)

# Setup Jinja2 templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Mount static directories
app.mount("/meme-templates", StaticFiles(directory=str(MEME_TEMPLATES_DIR)), name="meme_templates")
app.mount("/output", StaticFiles(directory=str(OUTPUT_DIR)), name="output")

# Try to mount fonts if exists
if FONTS_DIR.exists():
    app.mount("/fonts", StaticFiles(directory=str(FONTS_DIR)), name="fonts")


def get_font(size: int) -> ImageFont.FreeTypeFont:
    """Get Impact font or fallback."""
    font_paths = [
        FONTS_DIR / "impact.ttf",
        FONTS_DIR / "Impact.ttf",
        "/usr/share/fonts/truetype/msttcorefonts/Impact.ttf",
        "/usr/share/fonts/TTF/impact.ttf",
        "/System/Library/Fonts/Supplemental/Impact.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Fallback
    ]
    
    for font_path in font_paths:
        if Path(font_path).exists():
            return ImageFont.truetype(str(font_path), size)
    
    # Fallback to default
    return ImageFont.load_default()


def draw_text_with_outline(
    draw: ImageDraw.ImageDraw,
    position: tuple,
    text: str,
    font: ImageFont.FreeTypeFont,
    fill_color: str = "white",
    outline_color: str = "black",
    outline_width: int = 3
):
    """Draw text with outline (classic meme style)."""
    x, y = position
    
    # Draw outline
    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx != 0 or dy != 0:
                draw.text((x + dx, y + dy), text, font=font, fill=outline_color)
    
    # Draw main text
    draw.text((x, y), text, font=font, fill=fill_color)


def calculate_font_size(image_width: int, text: str, max_width_ratio: float = 0.9) -> int:
    """Calculate optimal font size for text to fit image width."""
    target_width = int(image_width * max_width_ratio)
    
    # Start with a large size and decrease
    for size in range(80, 20, -2):
        font = get_font(size)
        # Get text bounding box
        bbox = font.getbbox(text)
        text_width = bbox[2] - bbox[0]
        if text_width <= target_width:
            return size
    
    return 24  # Minimum size


def wrap_text_for_image(text: str, image_width: int, font_size: int) -> list:
    """Wrap text to fit within image width."""
    font = get_font(font_size)
    max_width = int(image_width * 0.9)
    
    # Estimate characters per line
    avg_char_width = font_size * 0.6
    chars_per_line = max(10, int(max_width / avg_char_width))
    
    # Wrap text
    wrapped = textwrap.wrap(text.upper(), width=chars_per_line)
    return wrapped


def generate_meme_image(
    template_path: Path,
    top_text: str = "",
    bottom_text: str = ""
) -> Image.Image:
    """Generate a meme image with top and bottom text."""
    # Open template
    img = Image.open(template_path).convert("RGBA")
    draw = ImageDraw.Draw(img)
    
    width, height = img.size
    padding = 10
    
    # Process top text
    if top_text:
        top_text = top_text.upper()
        font_size = calculate_font_size(width, top_text)
        lines = wrap_text_for_image(top_text, width, font_size)
        font = get_font(font_size)
        
        y_offset = padding
        for line in lines:
            bbox = font.getbbox(line)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (width - text_width) // 2
            draw_text_with_outline(draw, (x, y_offset), line, font)
            y_offset += text_height + 5
    
    # Process bottom text
    if bottom_text:
        bottom_text = bottom_text.upper()
        font_size = calculate_font_size(width, bottom_text)
        lines = wrap_text_for_image(bottom_text, width, font_size)
        font = get_font(font_size)
        
        # Calculate total height of bottom text
        total_height = 0
        line_heights = []
        for line in lines:
            bbox = font.getbbox(line)
            h = bbox[3] - bbox[1]
            line_heights.append(h)
            total_height += h + 5
        
        y_offset = height - total_height - padding
        for i, line in enumerate(lines):
            bbox = font.getbbox(line)
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) // 2
            draw_text_with_outline(draw, (x, y_offset), line, font)
            y_offset += line_heights[i] + 5
    
    return img


def get_template_list() -> list:
    """Get list of all meme templates."""
    templates_list = []
    
    if MEME_TEMPLATES_DIR.exists():
        for f in sorted(MEME_TEMPLATES_DIR.iterdir()):
            if f.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
                # Create display name from filename
                name = f.stem.replace('_', ' ').replace('-', ' ').title()
                templates_list.append({
                    "filename": f.name,
                    "name": name,
                    "url": f"/meme-templates/{f.name}"
                })
    
    return templates_list


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Main page - imgflip-style meme generator."""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "page_title": "HairDAO Meme Generator"
    })


@app.get("/api/templates")
async def api_templates(search: Optional[str] = Query(None)):
    """Get list of meme templates, optionally filtered by search."""
    all_templates = get_template_list()
    
    if search:
        search_lower = search.lower()
        all_templates = [
            t for t in all_templates 
            if search_lower in t["name"].lower() or search_lower in t["filename"].lower()
        ]
    
    return {"templates": all_templates, "count": len(all_templates)}


@app.get("/api/generate")
async def api_generate_meme(
    template: str,
    top: str = "",
    bottom: str = ""
):
    """Generate a meme and return the image."""
    template_path = MEME_TEMPLATES_DIR / template
    
    if not template_path.exists():
        raise HTTPException(status_code=404, detail="Template not found")
    
    try:
        img = generate_meme_image(template_path, top, bottom)
        
        # Convert to bytes
        img_bytes = io.BytesIO()
        # Convert RGBA to RGB for JPEG compatibility
        if img.mode == 'RGBA':
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[3])
            rgb_img.save(img_bytes, format='PNG')
        else:
            img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        return StreamingResponse(
            img_bytes,
            media_type="image/png",
            headers={"Content-Disposition": f"inline; filename=meme.png"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/download")
async def api_download_meme(
    template: str,
    top: str = "",
    bottom: str = ""
):
    """Generate and download a meme."""
    template_path = MEME_TEMPLATES_DIR / template
    
    if not template_path.exists():
        raise HTTPException(status_code=404, detail="Template not found")
    
    try:
        img = generate_meme_image(template_path, top, bottom)
        
        # Save to output directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = re.sub(r'[^a-zA-Z0-9]', '_', template.rsplit('.', 1)[0])
        filename = f"{safe_name}_{timestamp}.png"
        output_path = OUTPUT_DIR / filename
        
        # Convert RGBA to RGB for saving
        if img.mode == 'RGBA':
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[3])
            rgb_img.save(output_path, format='PNG')
        else:
            img.save(output_path, format='PNG')
        
        return FileResponse(
            output_path,
            filename=filename,
            media_type="image/png"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/gallery", response_class=HTMLResponse)
async def gallery(request: Request):
    """Gallery of generated memes."""
    memes = []
    if OUTPUT_DIR.exists():
        files = sorted(OUTPUT_DIR.glob("*.png"), key=os.path.getmtime, reverse=True)
        for f in files[:50]:
            memes.append({
                "filename": f.name,
                "url": f"/output/{f.name}",
                "created": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            })
    
    return templates.TemplateResponse("gallery.html", {
        "request": request,
        "memes": memes,
        "page_title": "Meme Gallery"
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
