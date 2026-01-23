"""
Uses OpenAI GPT-4o-mini to generate meme concepts based on HairDAO/Anagen context.
"""
import json
import random
from openai import OpenAI
from config import OPENAI_API_KEY, MEME_STYLES
from scraper import load_website_content
from discord_scanner import load_discord_content


def create_meme_prompt(website_data: dict, discord_data: dict, style: str = None) -> str:
    """Create a prompt to generate a meme concept."""

    style = style or random.choice(MEME_STYLES)

    # Build context about the company
    hairdao_info = website_data.get("hairdao", {})
    anagen_info = website_data.get("anagen", {})

    # Get Discord community info
    active_users = discord_data.get("active_users", [])[:10]
    catchphrases = discord_data.get("catchphrases", [])[:5]
    memorable = discord_data.get("memorable_messages", [])[:5]
    frequent_words = discord_data.get("frequent_words", [])[:15]

    prompt = f"""You are a meme creator for HairDAO, a crypto/web3 company focused on hair loss solutions and research. Their main product is Anagen.

COMPANY CONTEXT:
- HairDAO website headlines: {hairdao_info.get('headings', [])}
- HairDAO taglines: {hairdao_info.get('taglines', [])}
- Anagen website headlines: {anagen_info.get('headings', [])}
- Anagen taglines: {anagen_info.get('taglines', [])}

DISCORD COMMUNITY CONTEXT:
- Active community members to potentially reference: {active_users}
- Community catchphrases/repeated sayings: {catchphrases}
- Frequently used words: {frequent_words}
- Popular messages: {[m.get('content', '')[:100] for m in memorable]}

MEME STYLE: {style}

Generate a meme concept that:
1. Is funny and relatable to the crypto/hair loss community
2. References HairDAO or Anagen naturally
3. Optionally includes a community member reference (use their name naturally, don't force it)
4. Works as a {style} format meme
5. Is appropriate for social media (no offensive content)

The meme should tap into common themes like:
- The struggle of hair loss
- Crypto/DeFi culture and terminology
- "Wagmi" / "ngmi" culture
- Diamond hands / holding
- The hope that comes with new treatments
- Community solidarity
- Web3 humor

{"NOTE: For ai_generated style, focus on creating a vivid, detailed image_description that can be used to generate a custom AI image. Describe the scene, characters, expressions, and setting in detail." if style == "ai_generated" else ""}

Return your response as JSON with this format:
{{
    "style": "{style}",
    "template_suggestion": "name of a popular meme template that would work, or 'custom' for ai_generated",
    "top_text": "top text for classic memes (or null if not applicable)",
    "bottom_text": "bottom text for classic memes (or null if not applicable)",
    "caption": "caption for modern style memes (or null if not applicable)",
    "description": "brief description of the meme visual",
    "image_description": "detailed scene description for AI image generation (required for ai_generated style)",
    "community_member_referenced": "username if referenced, or null",
    "humor_explanation": "brief explanation of why this is funny"
}}

Be creative and actually funny! Crypto twitter loves self-deprecating humor and inside jokes."""

    return prompt


def generate_meme_concept(website_data: dict = None, discord_data: dict = None, style: str = None) -> dict:
    """Generate a meme concept using GPT-4o-mini."""

    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not set. Please set this environment variable.")

    # Load data if not provided
    website_data = website_data or load_website_content()
    discord_data = discord_data or load_discord_content()

    client = OpenAI(api_key=OPENAI_API_KEY)

    prompt = create_meme_prompt(website_data, discord_data, style)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=1024,
        messages=[
            {"role": "user", "content": prompt}
        ],
        response_format={"type": "json_object"}
    )

    # Parse the response
    response_text = response.choices[0].message.content

    # Try to extract JSON from the response
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass

    # Try to find JSON in response if direct parse failed
    try:
        start = response_text.find('{')
        end = response_text.rfind('}') + 1
        if start != -1 and end > start:
            json_str = response_text[start:end]
            return json.loads(json_str)
    except json.JSONDecodeError:
        pass

    # Fallback if JSON parsing fails
    return {
        "style": style or "classic_top_bottom",
        "template_suggestion": "custom",
        "top_text": "When HairDAO",
        "bottom_text": "Actually delivers",
        "caption": response_text[:200] if response_text else "HairDAO to the moon",
        "description": "Generated meme",
        "community_member_referenced": None,
        "humor_explanation": "Fallback meme"
    }


def generate_multiple_concepts(count: int = 5) -> list:
    """Generate multiple meme concepts."""
    website_data = load_website_content()
    discord_data = load_discord_content()

    concepts = []
    for i in range(count):
        print(f"Generating concept {i+1}/{count}...")
        style = MEME_STYLES[i % len(MEME_STYLES)]
        concept = generate_meme_concept(website_data, discord_data, style)
        concepts.append(concept)

    return concepts


if __name__ == "__main__":
    print("Testing meme generation...")
    concept = generate_meme_concept()
    print(json.dumps(concept, indent=2))
