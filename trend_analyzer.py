"""
Analyzes trends and generates relevant meme concepts for HairDAO.
"""
import json
from datetime import datetime
from typing import List, Dict, Optional
from openai import OpenAI
from config import OPENAI_API_KEY, DATA_DIR, MEME_STYLES
from trend_fetcher import get_combined_trends, fetch_all_trends

GENERATED_MEMES_FILE = DATA_DIR / "trending_memes.json"


def analyze_trend_relevance(trends: List[Dict]) -> List[Dict]:
    """
    Use GPT to analyze which trends are most relevant/memeable for HairDAO.
    """
    if not OPENAI_API_KEY or not trends:
        return trends

    client = OpenAI(api_key=OPENAI_API_KEY)

    # Prepare trends summary
    trends_text = "\n".join([
        f"- [{t.get('source', 'unknown')}] {t.get('topic', '')[:100]}"
        for t in trends[:30]
    ])

    prompt = f"""You are a social media manager for HairDAO, a crypto/web3 company focused on hair loss solutions.

Analyze these trending topics and rate each one's meme potential for HairDAO (1-10):

{trends_text}

Consider:
1. Can it be connected to hair loss, baldness, or hair growth?
2. Can it be connected to crypto, DeFi, web3, or investing?
3. Is it currently viral/trending enough to ride the wave?
4. Can it be made funny without being offensive?

Return a JSON array with the top 10 most memeable trends:
[
  {{
    "topic": "original topic text",
    "relevance_score": 8,
    "meme_angle": "how to connect this to HairDAO",
    "suggested_caption": "a funny caption idea"
  }}
]

Focus on trends that can naturally connect to hair loss OR crypto themes."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)

        # Handle both array and object responses
        if isinstance(result, dict):
            analyzed = result.get("trends", result.get("results", []))
        else:
            analyzed = result

        return analyzed if isinstance(analyzed, list) else []

    except Exception as e:
        print(f"Trend analysis error: {e}")
        return []


def generate_meme_from_trend(trend: Dict, style: str = None) -> Dict:
    """
    Generate a full meme concept from a trending topic.
    """
    if not OPENAI_API_KEY:
        return {}

    client = OpenAI(api_key=OPENAI_API_KEY)
    style = style or "modern_caption"

    topic = trend.get("topic", "")
    meme_angle = trend.get("meme_angle", "")
    suggested_caption = trend.get("suggested_caption", "")

    prompt = f"""Create a meme concept for HairDAO based on this trending topic:

TREND: {topic}
ANGLE: {meme_angle}
SUGGESTED CAPTION: {suggested_caption}

HairDAO is a crypto/web3 company focused on hair loss solutions. Their community uses terms like "wagmi", "ngmi", "diamond hands", etc.

Create a {style} meme that:
1. Capitalizes on the trending topic
2. Connects to either hair loss/baldness OR crypto culture
3. Is funny and shareable
4. Would work well on Twitter/X

Return JSON:
{{
    "style": "{style}",
    "template_suggestion": "name of a popular meme template OR 'custom' for AI image",
    "top_text": "top text for classic memes (or null)",
    "bottom_text": "bottom text (or null)",
    "caption": "caption for modern style",
    "description": "brief visual description",
    "image_description": "detailed scene description for AI image generation",
    "trend_reference": "the trending topic this references",
    "hashtags": ["relevant", "hashtags"],
    "humor_explanation": "why this is funny and timely"
}}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )

        concept = json.loads(response.choices[0].message.content)
        concept["source_trend"] = trend
        concept["generated_at"] = datetime.now().isoformat()

        return concept

    except Exception as e:
        print(f"Meme generation error: {e}")
        return {}


def generate_trending_memes(count: int = 5) -> List[Dict]:
    """
    Fetch trends, analyze them, and generate meme concepts.
    """
    print("Fetching trends...")
    trends = get_combined_trends(limit=30)

    if not trends:
        print("No trends found")
        return []

    print(f"Found {len(trends)} trends, analyzing relevance...")
    analyzed = analyze_trend_relevance(trends)

    if not analyzed:
        print("Could not analyze trends")
        return []

    print(f"Generating {count} meme concepts from top trends...")
    memes = []

    # Cycle through different styles
    styles = ["modern_caption", "classic_top_bottom", "ai_generated"]

    for i, trend in enumerate(analyzed[:count]):
        style = styles[i % len(styles)]
        print(f"  Generating meme {i+1}/{count}: {trend.get('topic', '')[:40]}...")

        meme = generate_meme_from_trend(trend, style)
        if meme:
            memes.append(meme)

    # Save generated memes
    save_trending_memes(memes)

    return memes


def save_trending_memes(memes: List[Dict]):
    """Save generated memes to file."""
    try:
        existing = load_trending_memes()
        # Add new memes at the beginning
        all_memes = memes + existing
        # Keep only last 50
        all_memes = all_memes[:50]

        with open(GENERATED_MEMES_FILE, "w") as f:
            json.dump({
                "updated_at": datetime.now().isoformat(),
                "memes": all_memes
            }, f, indent=2)

        print(f"Saved {len(memes)} new trending memes")
    except Exception as e:
        print(f"Error saving memes: {e}")


def load_trending_memes() -> List[Dict]:
    """Load previously generated trending memes."""
    try:
        if GENERATED_MEMES_FILE.exists():
            with open(GENERATED_MEMES_FILE, "r") as f:
                data = json.load(f)
                return data.get("memes", [])
    except Exception as e:
        print(f"Error loading memes: {e}")
    return []


def get_fresh_trending_memes(force_refresh: bool = False, count: int = 5) -> List[Dict]:
    """
    Get trending memes, generating new ones if needed.
    """
    if force_refresh:
        return generate_trending_memes(count)

    existing = load_trending_memes()

    # Check if we have recent memes (less than 1 hour old)
    if existing:
        try:
            if GENERATED_MEMES_FILE.exists():
                with open(GENERATED_MEMES_FILE, "r") as f:
                    data = json.load(f)
                    updated = datetime.fromisoformat(data.get("updated_at", "2000-01-01"))
                    age_minutes = (datetime.now() - updated).total_seconds() / 60

                    if age_minutes < 60:  # Less than 1 hour old
                        print(f"Using cached trending memes ({int(age_minutes)} min old)")
                        return existing
        except Exception:
            pass

    # Generate fresh memes
    return generate_trending_memes(count)


if __name__ == "__main__":
    print("=" * 50)
    print("Trending Meme Generator")
    print("=" * 50)

    memes = generate_trending_memes(count=3)

    print(f"\nGenerated {len(memes)} trending memes:\n")
    for i, meme in enumerate(memes, 1):
        print(f"{i}. {meme.get('caption', meme.get('top_text', 'No caption'))}")
        print(f"   Trend: {meme.get('trend_reference', 'Unknown')}")
        print(f"   Style: {meme.get('style', 'Unknown')}")
        print(f"   Template: {meme.get('template_suggestion', 'custom')}")
        print()
