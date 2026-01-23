"""
Creates meme images from concepts using Pillow.
"""
import os
import random
import requests
from io import BytesIO
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from config import TEMPLATES_DIR, OUTPUT_DIR


# Popular meme templates with URLs (using imgflip's popular templates)
MEME_TEMPLATES = {
    # Classic memes
    "drake": "https://i.imgflip.com/30b1gx.jpg",
    "distracted_boyfriend": "https://i.imgflip.com/1ur9b0.jpg",
    "expanding_brain": "https://i.imgflip.com/1jwhww.jpg",
    "change_my_mind": "https://i.imgflip.com/24y43o.jpg",
    "two_buttons": "https://i.imgflip.com/1g8my4.jpg",
    "is_this_a": "https://i.imgflip.com/1o00in.jpg",
    "waiting_skeleton": "https://i.imgflip.com/2fm6x.jpg",
    "success_kid": "https://i.imgflip.com/1bhk.jpg",
    "disaster_girl": "https://i.imgflip.com/23ls.jpg",
    "one_does_not_simply": "https://i.imgflip.com/1bij.jpg",
    "roll_safe": "https://i.imgflip.com/1h7in3.jpg",
    "stonks": "https://i.imgflip.com/2xnzgr.jpg",
    # Additional popular templates
    "batman_slapping": "https://i.imgflip.com/9ehk.jpg",
    "hide_the_pain_harold": "https://i.imgflip.com/gk5el.jpg",
    "ancient_aliens": "https://i.imgflip.com/26am.jpg",
    "futurama_fry": "https://i.imgflip.com/1bgw.jpg",
    "woman_yelling_at_cat": "https://i.imgflip.com/345v97.jpg",
    "always_has_been": "https://i.imgflip.com/46e43q.jpg",
    "bernie_mittens": "https://i.imgflip.com/4ecbya.jpg",
    "trade_offer": "https://i.imgflip.com/54hjww.jpg",
    "they_dont_know": "https://i.imgflip.com/4pn1an.jpg",
    "giga_chad": "https://i.imgflip.com/5j6x75.jpg",
    "anakin_padme": "https://i.imgflip.com/5c7lwq.jpg",
    "buff_doge_cheems": "https://i.imgflip.com/43a45p.jpg",
    "think_mark": "https://i.imgflip.com/5a3ng3.jpg",
    "monkey_puppet": "https://i.imgflip.com/2gnnjh.jpg",
    "panik_kalm": "https://i.imgflip.com/3qqcim.jpg",
    "surprised_pikachu": "https://i.imgflip.com/2kbn1e.jpg",
    "this_is_fine": "https://i.imgflip.com/wxica.jpg",
    "sad_pablo_escobar": "https://i.imgflip.com/21kgqs.jpg",
    "tuxedo_winnie": "https://i.imgflip.com/2ybua0.jpg",
    "uno_draw_25": "https://i.imgflip.com/3lmzyx.jpg",
    "epic_handshake": "https://i.imgflip.com/28j0te.jpg",
    "left_exit_12": "https://i.imgflip.com/22bdq6.jpg",
    "boardroom_meeting": "https://i.imgflip.com/m78d.jpg",
    "clown_makeup": "https://i.imgflip.com/38el31.jpg",
    "running_away_balloon": "https://i.imgflip.com/2w6fal.jpg",
}


def get_font(size: int = 40) -> ImageFont.FreeTypeFont:
    """Get a font for meme text. Falls back to default if Impact not available."""
    font_paths = [
        "/System/Library/Fonts/Supplemental/Impact.ttf",  # macOS
        "/usr/share/fonts/truetype/msttcorefonts/Impact.ttf",  # Linux with msttcorefonts
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",  # Linux fallback
        "C:\\Windows\\Fonts\\impact.ttf",  # Windows
    ]

    for font_path in font_paths:
        if os.path.exists(font_path):
            return ImageFont.truetype(font_path, size)

    # Ultimate fallback - use default
    return ImageFont.load_default()


def add_text_with_outline(draw: ImageDraw, position: tuple, text: str, font: ImageFont,
                          fill: str = "white", outline: str = "black", outline_width: int = 2):
    """Add text with an outline for better visibility."""
    x, y = position

    # Draw outline
    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx != 0 or dy != 0:
                draw.text((x + dx, y + dy), text, font=font, fill=outline)

    # Draw main text
    draw.text(position, text, font=font, fill=fill)


def wrap_text(text: str, font: ImageFont, max_width: int, draw: ImageDraw) -> list:
    """Wrap text to fit within a given width."""
    words = text.split()
    lines = []
    current_line = []

    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        width = bbox[2] - bbox[0]

        if width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]

    if current_line:
        lines.append(' '.join(current_line))

    return lines


def download_template(template_name: str) -> Image.Image:
    """Download a meme template image."""
    if template_name in MEME_TEMPLATES:
        url = MEME_TEMPLATES[template_name]
        response = requests.get(url)
        return Image.open(BytesIO(response.content))

    # Check local templates folder
    local_path = TEMPLATES_DIR / f"{template_name}.jpg"
    if local_path.exists():
        return Image.open(local_path)

    local_path = TEMPLATES_DIR / f"{template_name}.png"
    if local_path.exists():
        return Image.open(local_path)

    raise ValueError(f"Template '{template_name}' not found")


# Templates that need special text positioning (text goes to the right side)
SIDE_TEXT_TEMPLATES = {
    "drake": {"top_zone": (0.5, 0, 1.0, 0.5), "bottom_zone": (0.5, 0.5, 1.0, 1.0)},  # Right side, top and bottom halves
    "tuxedo_winnie": {"top_zone": (0.4, 0, 1.0, 0.5), "bottom_zone": (0.4, 0.5, 1.0, 1.0)},
    "buff_doge_cheems": {"top_zone": (0, 0, 0.5, 1.0), "bottom_zone": (0.5, 0, 1.0, 1.0)},  # Left and right halves
}


def create_classic_meme(template_name: str, top_text: str, bottom_text: str) -> Image.Image:
    """Create a classic top/bottom text meme."""
    # Try to get template
    try:
        img = download_template(template_name)
    except:
        # Create a placeholder if template not found
        img = Image.new('RGB', (800, 600), color='gray')

    img = img.convert('RGB')
    draw = ImageDraw.Draw(img)

    width, height = img.size

    # Check if this template needs special side-text positioning
    if template_name in SIDE_TEXT_TEMPLATES:
        return create_side_text_meme(img, template_name, top_text, bottom_text)

    # Standard top/bottom text positioning
    font_size = int(width / 12)
    font = get_font(font_size)

    padding = 20
    max_text_width = width - (padding * 2)

    # Add top text
    if top_text:
        top_text = top_text.upper()
        lines = wrap_text(top_text, font, max_text_width, draw)
        y_offset = padding
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) // 2
            add_text_with_outline(draw, (x, y_offset), line, font)
            y_offset += bbox[3] - bbox[1] + 5

    # Add bottom text
    if bottom_text:
        bottom_text = bottom_text.upper()
        lines = wrap_text(bottom_text, font, max_text_width, draw)

        # Calculate total height of bottom text
        total_height = sum(draw.textbbox((0, 0), line, font=font)[3] - draw.textbbox((0, 0), line, font=font)[1] + 5 for line in lines)
        y_offset = height - total_height - padding

        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) // 2
            add_text_with_outline(draw, (x, y_offset), line, font)
            y_offset += bbox[3] - bbox[1] + 5

    return img


def create_side_text_meme(img: Image.Image, template_name: str, top_text: str, bottom_text: str) -> Image.Image:
    """Create a meme with text positioned in specific zones (like Drake template)."""
    draw = ImageDraw.Draw(img)
    width, height = img.size

    zones = SIDE_TEXT_TEMPLATES[template_name]

    # Calculate font size based on zone width
    top_zone = zones["top_zone"]
    zone_width = int(width * (top_zone[2] - top_zone[0]))
    font_size = int(zone_width / 8)
    font = get_font(font_size)

    padding = 15

    # Add top text in top zone
    if top_text:
        top_text = top_text.upper()
        zone_x = int(width * top_zone[0])
        zone_y = int(height * top_zone[1])
        zone_w = int(width * (top_zone[2] - top_zone[0]))
        zone_h = int(height * (top_zone[3] - top_zone[1]))

        max_text_width = zone_w - (padding * 2)
        lines = wrap_text(top_text, font, max_text_width, draw)

        # Center text vertically in zone
        total_text_height = sum(draw.textbbox((0, 0), line, font=font)[3] - draw.textbbox((0, 0), line, font=font)[1] + 5 for line in lines)
        y_offset = zone_y + (zone_h - total_text_height) // 2

        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = zone_x + (zone_w - text_width) // 2
            add_text_with_outline(draw, (x, y_offset), line, font)
            y_offset += bbox[3] - bbox[1] + 5

    # Add bottom text in bottom zone
    if bottom_text:
        bottom_text = bottom_text.upper()
        bottom_zone = zones["bottom_zone"]
        zone_x = int(width * bottom_zone[0])
        zone_y = int(height * bottom_zone[1])
        zone_w = int(width * (bottom_zone[2] - bottom_zone[0]))
        zone_h = int(height * (bottom_zone[3] - bottom_zone[1]))

        max_text_width = zone_w - (padding * 2)
        lines = wrap_text(bottom_text, font, max_text_width, draw)

        # Center text vertically in zone
        total_text_height = sum(draw.textbbox((0, 0), line, font=font)[3] - draw.textbbox((0, 0), line, font=font)[1] + 5 for line in lines)
        y_offset = zone_y + (zone_h - total_text_height) // 2

        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = zone_x + (zone_w - text_width) // 2
            add_text_with_outline(draw, (x, y_offset), line, font)
            y_offset += bbox[3] - bbox[1] + 5

    return img


def create_caption_meme(template_name: str, caption: str) -> Image.Image:
    """Create a modern meme with caption above the image."""
    # Try to get template
    try:
        img = download_template(template_name)
    except:
        img = Image.new('RGB', (800, 600), color='gray')

    img = img.convert('RGB')
    img_width, img_height = img.size

    # Create caption area
    font_size = int(img_width / 20)
    font = get_font(font_size)

    # Create a temporary image to calculate text dimensions
    temp_img = Image.new('RGB', (1, 1))
    temp_draw = ImageDraw.Draw(temp_img)

    padding = 20
    max_text_width = img_width - (padding * 2)
    lines = wrap_text(caption, font, max_text_width, temp_draw)

    # Calculate caption height
    line_height = font_size + 5
    caption_height = len(lines) * line_height + (padding * 2)

    # Create new image with caption area
    new_img = Image.new('RGB', (img_width, img_height + caption_height), color='white')
    new_img.paste(img, (0, caption_height))

    draw = ImageDraw.Draw(new_img)

    # Draw caption
    y_offset = padding
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        x = (img_width - text_width) // 2
        draw.text((x, y_offset), line, font=font, fill='black')
        y_offset += line_height

    return new_img


def create_twitter_style_meme(username: str, tweet_text: str, profile_pic_color: str = None) -> Image.Image:
    """Create a fake tweet style meme."""
    width, height = 600, 200
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)

    # Draw profile picture (colored circle)
    pp_color = profile_pic_color or random.choice(['#1DA1F2', '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4'])
    draw.ellipse([20, 20, 70, 70], fill=pp_color)

    # Username
    font_bold = get_font(18)
    font_regular = get_font(16)

    draw.text((85, 20), f"@{username}", font=font_bold, fill='black')
    draw.text((85, 45), "HairDAO Community", font=font_regular, fill='gray')

    # Tweet text
    padding = 20
    max_text_width = width - (padding * 2)
    lines = wrap_text(tweet_text, font_regular, max_text_width, draw)

    y_offset = 90
    for line in lines:
        draw.text((padding, y_offset), line, font=font_regular, fill='black')
        y_offset += 22

    # Add border
    draw.rectangle([0, 0, width-1, height-1], outline='#E1E8ED', width=1)

    return img


def create_discord_style_meme(username: str, message: str, role_color: str = None) -> Image.Image:
    """Create a fake Discord message style meme."""
    width = 600

    font_regular = get_font(16)
    temp_img = Image.new('RGB', (1, 1))
    temp_draw = ImageDraw.Draw(temp_img)

    padding = 15
    max_text_width = width - 80
    lines = wrap_text(message, font_regular, max_text_width, temp_draw)

    height = max(80, 50 + len(lines) * 22)

    img = Image.new('RGB', (width, height), color='#36393F')
    draw = ImageDraw.Draw(img)

    # Profile picture
    pp_color = role_color or random.choice(['#5865F2', '#57F287', '#FEE75C', '#EB459E', '#ED4245'])
    draw.ellipse([15, 15, 55, 55], fill=pp_color)

    # Username with role color
    font_bold = get_font(16)
    draw.text((65, 15), username, font=font_bold, fill=pp_color)

    # Timestamp
    draw.text((65 + len(username) * 10, 18), "Today at 4:20 PM", font=get_font(12), fill='#72767D')

    # Message
    y_offset = 40
    for line in lines:
        draw.text((65, y_offset), line, font=font_regular, fill='#DCDDDE')
        y_offset += 22

    return img


def create_meme_from_concept(concept: dict) -> Image.Image:
    """Create a meme image from a generated concept."""
    style = concept.get("style", "classic_top_bottom")
    template = concept.get("template_suggestion", "custom")

    # Map template suggestions to actual templates
    template_map = {
        "drake": "drake",
        "distracted boyfriend": "distracted_boyfriend",
        "expanding brain": "expanding_brain",
        "change my mind": "change_my_mind",
        "two buttons": "two_buttons",
        "is this a pigeon": "is_this_a",
        "waiting skeleton": "waiting_skeleton",
        "success kid": "success_kid",
        "disaster girl": "disaster_girl",
        "one does not simply": "one_does_not_simply",
        "roll safe": "roll_safe",
        "stonks": "stonks",
    }

    # Try to find matching template
    template_key = None
    for key in template_map:
        if key in template.lower():
            template_key = template_map[key]
            break

    if not template_key:
        template_key = random.choice(list(MEME_TEMPLATES.keys()))

    if style == "classic_top_bottom":
        return create_classic_meme(
            template_key,
            concept.get("top_text", ""),
            concept.get("bottom_text", "")
        )
    elif style == "modern_caption":
        caption = concept.get("caption") or concept.get("top_text") or "WAGMI"
        return create_caption_meme(template_key, caption)
    elif style == "twitter_screenshot":
        username = concept.get("community_member_referenced") or "HairDAO_Chad"
        caption = concept.get("caption") or concept.get("top_text") or "WAGMI #HairDAO"
        return create_twitter_style_meme(username, caption)
    elif style == "discord_message":
        username = concept.get("community_member_referenced") or "hairdao_enjoyer"
        caption = concept.get("caption") or concept.get("top_text") or "gm kings"
        return create_discord_style_meme(username, caption)
    elif style == "ai_generated":
        # Use DALL-E for custom image generation
        from ai_image_generator import generate_ai_meme_image
        return generate_ai_meme_image(concept, add_text=True)
    else:
        # Default to classic
        return create_classic_meme(
            template_key,
            concept.get("top_text", ""),
            concept.get("bottom_text", "")
        )


def save_meme(img: Image.Image, concept: dict = None) -> Path:
    """Save a meme image to the output folder."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    style = concept.get("style", "meme") if concept else "meme"
    filename = f"{style}_{timestamp}.png"
    output_path = OUTPUT_DIR / filename

    img.save(output_path, "PNG")
    print(f"Saved meme to {output_path}")

    return output_path


if __name__ == "__main__":
    # Test meme creation
    print("Testing classic meme...")
    img = create_classic_meme("drake", "Buying hair products", "Buying $HAIR tokens")
    save_meme(img, {"style": "test_classic"})

    print("Testing Twitter style...")
    img = create_twitter_style_meme("hairdao_chad", "Just aped into Anagen. If I'm gonna be bald, at least I'll be rich and bald.")
    save_meme(img, {"style": "test_twitter"})

    print("Testing Discord style...")
    img = create_discord_style_meme("CryptoFollicle", "gm kings, how are we feeling about the Anagen launch? bullish af")
    save_meme(img, {"style": "test_discord"})
