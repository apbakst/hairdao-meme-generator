#!/usr/bin/env python3
"""
Generate placeholder meme template images for HairDAO.
Run this script to create base template images.
"""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

TEMPLATES_DIR = Path(__file__).parent / "templates" / "memes"
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

# Load template config
with open(TEMPLATES_DIR / "templates.json", "r") as f:
    config = json.load(f)

# Color palette for placeholders
COLORS = {
    "bald_wojak": "#3B82F6",  # Blue
    "hair_diamond_hands": "#8B5CF6",  # Purple
    "regrowth_gigachad": "#10B981",  # Green
    "minoxidil_vs_hairdao": "#F59E0B",  # Amber
    "norwood_reaper": "#1F2937",  # Dark gray
    "anagen_phase": "#06B6D4",  # Cyan
    "wagmi_hair": "#7C3AED",  # Violet
    "before_after": "#EC4899",  # Pink
    "hair_pepe": "#22C55E",  # Green
    "expanding_brain_hair": "#6366F1",  # Indigo
}


def get_font(size: int):
    """Get a font, fallback to default if not available."""
    fonts_to_try = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "Arial Bold",
        "arial.ttf",
    ]
    
    for font_path in fonts_to_try:
        try:
            return ImageFont.truetype(font_path, size)
        except (IOError, OSError):
            continue
    
    return ImageFont.load_default()


def create_placeholder_template(template: dict) -> Image.Image:
    """Create a placeholder template image."""
    template_id = template["id"]
    name = template["name"]
    description = template["description"]
    
    # Get color for this template
    bg_color = COLORS.get(template_id, "#4B5563")
    
    # Create image
    width, height = 800, 800
    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)
    
    # Add grid pattern
    for x in range(0, width, 50):
        draw.line([(x, 0), (x, height)], fill="#FFFFFF20", width=1)
    for y in range(0, height, 50):
        draw.line([(0, y), (width, y)], fill="#FFFFFF20", width=1)
    
    # Add border
    draw.rectangle([(10, 10), (width-10, height-10)], outline="#FFFFFF", width=3)
    
    # Add template name
    title_font = get_font(48)
    desc_font = get_font(24)
    small_font = get_font(18)
    
    # Title
    title_bbox = draw.textbbox((0, 0), name, font=title_font)
    title_x = (width - (title_bbox[2] - title_bbox[0])) // 2
    draw.text((title_x, height // 3), name, font=title_font, fill="#FFFFFF")
    
    # Description
    # Wrap description text
    words = description.split()
    lines = []
    current_line = []
    for word in words:
        test_line = " ".join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=desc_font)
        if bbox[2] - bbox[0] < width - 60:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
    if current_line:
        lines.append(" ".join(current_line))
    
    y = height // 2
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=desc_font)
        x = (width - (bbox[2] - bbox[0])) // 2
        draw.text((x, y), line, font=desc_font, fill="#FFFFFFCC")
        y += 35
    
    # Add placeholder note
    note = "[PLACEHOLDER - Replace with actual template]"
    bbox = draw.textbbox((0, 0), note, font=small_font)
    x = (width - (bbox[2] - bbox[0])) // 2
    draw.text((x, height - 80), note, font=small_font, fill="#FFFFFF80")
    
    # Add HairDAO branding
    brand = "🧬 HairDAO Meme Generator"
    bbox = draw.textbbox((0, 0), brand, font=small_font)
    x = (width - (bbox[2] - bbox[0])) // 2
    draw.text((x, height - 50), brand, font=small_font, fill="#FFFFFF80")
    
    return img


def create_all_templates():
    """Create all placeholder template images."""
    print("Creating HairDAO meme templates...")
    
    for template in config["templates"]:
        template_id = template["id"]
        filename = template["filename"]
        
        print(f"  Creating {template_id}...")
        
        img = create_placeholder_template(template)
        output_path = TEMPLATES_DIR / filename
        img.save(output_path, "PNG")
        
        print(f"    Saved to {output_path}")
    
    print(f"\nCreated {len(config['templates'])} template images!")
    print(f"Location: {TEMPLATES_DIR}")
    print("\nNote: These are placeholder images. Replace them with actual meme templates.")


if __name__ == "__main__":
    create_all_templates()
