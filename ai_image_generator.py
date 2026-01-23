"""
AI Image Generation using DALL-E for custom meme images.
"""
import requests
from io import BytesIO
from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont
from config import OPENAI_API_KEY, OUTPUT_DIR
from image_creator import get_font, add_text_with_outline, wrap_text


def generate_dalle_image(prompt: str, size: str = "1024x1024", quality: str = "standard") -> Image.Image:
    """
    Generate an image using DALL-E 3.

    Args:
        prompt: Description of the image to generate
        size: Image size - "1024x1024", "1792x1024", or "1024x1792"
        quality: "standard" or "hd" (hd costs more)

    Returns:
        PIL Image object
    """
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not set")

    client = OpenAI(api_key=OPENAI_API_KEY)

    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size=size,
        quality=quality,
        n=1,
    )

    image_url = response.data[0].url

    # Download the image
    img_response = requests.get(image_url)
    img = Image.open(BytesIO(img_response.content))

    return img


def create_meme_prompt_for_dalle(concept: dict) -> str:
    """
    Create a DALL-E prompt from a meme concept.

    Args:
        concept: Meme concept dictionary with description, humor_explanation, etc.

    Returns:
        Optimized prompt for DALL-E
    """
    # Prefer image_description if provided (more detailed)
    image_description = concept.get("image_description", "")
    description = concept.get("description", "")
    top_text = concept.get("top_text", "")
    bottom_text = concept.get("bottom_text", "")
    caption = concept.get("caption", "")

    # Build context for the image - prioritize image_description
    if image_description:
        context = image_description
    else:
        context_parts = []
        if description:
            context_parts.append(description)
        if top_text and bottom_text:
            context_parts.append(f"Scene depicting: {top_text} vs {bottom_text}")
        elif caption:
            context_parts.append(f"Scene: {caption}")
        context = " ".join(context_parts) if context_parts else "A funny meme about hair loss and crypto"

    # Create a safe, meme-appropriate prompt
    prompt = f"""Create a funny, meme-style illustration for social media.
Style: Modern meme aesthetic, vibrant colors, expressive characters, slightly cartoonish.
Scene: {context}
Context: This is for HairDAO, a crypto/web3 company focused on hair loss solutions.
Important: No text in the image. Make it visually funny and shareable.
The image should work well with text overlay added later.
Keep it lighthearted and appropriate for all audiences."""

    return prompt


def generate_ai_meme_image(concept: dict, add_text: bool = True) -> Image.Image:
    """
    Generate a complete AI meme with DALL-E image and text overlay.

    Args:
        concept: Meme concept dictionary
        add_text: Whether to add text overlay to the image

    Returns:
        PIL Image with optional text overlay
    """
    # Generate the base image
    prompt = create_meme_prompt_for_dalle(concept)
    img = generate_dalle_image(prompt, size="1024x1024")

    if not add_text:
        return img

    # Add text overlay based on style
    style = concept.get("style", "modern_caption")

    if style == "classic_top_bottom":
        img = add_classic_text_overlay(img, concept)
    elif style == "modern_caption":
        img = add_caption_overlay(img, concept)
    else:
        # For twitter/discord styles, just add a simple caption
        img = add_caption_overlay(img, concept)

    return img


def add_classic_text_overlay(img: Image.Image, concept: dict) -> Image.Image:
    """Add classic top/bottom meme text to an image."""
    img = img.copy()
    draw = ImageDraw.Draw(img)

    width, height = img.size
    font_size = int(width / 14)
    font = get_font(font_size)

    padding = 30
    max_text_width = width - (padding * 2)

    top_text = concept.get("top_text") or ""
    bottom_text = concept.get("bottom_text") or ""

    # Add top text
    if top_text:
        top_text = top_text.upper()
        lines = wrap_text(top_text, font, max_text_width, draw)
        y_offset = padding
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) // 2
            add_text_with_outline(draw, (x, y_offset), line, font, outline_width=3)
            y_offset += bbox[3] - bbox[1] + 5

    # Add bottom text
    if bottom_text:
        bottom_text = bottom_text.upper()
        lines = wrap_text(bottom_text, font, max_text_width, draw)

        total_height = sum(
            draw.textbbox((0, 0), line, font=font)[3] - draw.textbbox((0, 0), line, font=font)[1] + 5
            for line in lines
        )
        y_offset = height - total_height - padding

        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) // 2
            add_text_with_outline(draw, (x, y_offset), line, font, outline_width=3)
            y_offset += bbox[3] - bbox[1] + 5

    return img


def add_caption_overlay(img: Image.Image, concept: dict) -> Image.Image:
    """Add a modern caption above the image."""
    width, height = img.size

    font_size = int(width / 20)
    font = get_font(font_size)

    caption = concept.get("caption") or concept.get("top_text") or "WAGMI"

    # Calculate caption dimensions
    temp_img = Image.new('RGB', (1, 1))
    temp_draw = ImageDraw.Draw(temp_img)

    padding = 25
    max_text_width = width - (padding * 2)
    lines = wrap_text(caption, font, max_text_width, temp_draw)

    line_height = font_size + 8
    caption_height = len(lines) * line_height + (padding * 2)

    # Create new image with caption area
    new_img = Image.new('RGB', (width, height + caption_height), color='white')
    new_img.paste(img, (0, caption_height))

    draw = ImageDraw.Draw(new_img)

    # Draw caption
    y_offset = padding
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) // 2
        draw.text((x, y_offset), line, font=font, fill='black')
        y_offset += line_height

    return new_img


def save_ai_meme(img: Image.Image, concept: dict = None) -> str:
    """Save an AI-generated meme to the output folder."""
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    style = concept.get("style", "ai") if concept else "ai"
    filename = f"dalle_{style}_{timestamp}.png"
    output_path = OUTPUT_DIR / filename

    img.save(output_path, "PNG")
    print(f"Saved AI meme to {output_path}")

    return str(output_path)


if __name__ == "__main__":
    # Test AI image generation
    print("Testing DALL-E meme generation...")

    test_concept = {
        "style": "modern_caption",
        "caption": "When you finally find a hair loss treatment that works",
        "description": "A happy person looking at their reflection, noticing new hair growth",
        "top_text": None,
        "bottom_text": None,
    }

    try:
        img = generate_ai_meme_image(test_concept)
        path = save_ai_meme(img, test_concept)
        print(f"Test meme saved to: {path}")
    except Exception as e:
        print(f"Error: {e}")
