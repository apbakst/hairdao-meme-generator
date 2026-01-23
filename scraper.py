"""
Scrapes content from HairDAO and Anagen websites for meme context.
"""
import json
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from config import HAIRDAO_URL, ANAGEN_URL, DATA_DIR


def scrape_website(url: str) -> dict:
    """Scrape text content from a website."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Remove script and style elements
        for element in soup(['script', 'style', 'nav', 'footer']):
            element.decompose()

        # Extract text content
        text = soup.get_text(separator=' ', strip=True)

        # Extract headings for key topics
        headings = [h.get_text(strip=True) for h in soup.find_all(['h1', 'h2', 'h3'])]

        # Extract any taglines or key phrases (often in specific classes)
        taglines = []
        for tag in soup.find_all(class_=lambda x: x and any(
            word in str(x).lower() for word in ['hero', 'tagline', 'headline', 'title', 'slogan']
        )):
            taglines.append(tag.get_text(strip=True))

        return {
            "url": url,
            "text": text[:5000],  # Limit to avoid too much data
            "headings": headings[:20],
            "taglines": taglines[:10]
        }
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return {"url": url, "text": "", "headings": [], "taglines": [], "error": str(e)}


def scrape_all() -> dict:
    """Scrape all relevant websites and save to data file."""
    print("Scraping HairDAO and Anagen websites...")

    data = {
        "hairdao": scrape_website(HAIRDAO_URL),
        "anagen": scrape_website(ANAGEN_URL),
    }

    # Save to file for caching
    output_file = DATA_DIR / "website_content.json"
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"Saved website content to {output_file}")
    return data


def load_website_content() -> dict:
    """Load cached website content or scrape if not available."""
    cache_file = DATA_DIR / "website_content.json"

    if cache_file.exists():
        with open(cache_file, 'r') as f:
            return json.load(f)

    return scrape_all()


if __name__ == "__main__":
    data = scrape_all()
    print("\nHairDAO headings:", data["hairdao"]["headings"])
    print("\nAnagen headings:", data["anagen"]["headings"])
