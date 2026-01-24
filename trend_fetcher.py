"""
Fetches trending topics from multiple sources: X/Twitter, News APIs, Reddit.
"""
import os
import json
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from config import DATA_DIR

TRENDS_CACHE_FILE = DATA_DIR / "trends_cache.json"
TRENDS_CACHE_DURATION = 30  # minutes


def get_twitter_trends(api_key: str = None, api_secret: str = None, bearer_token: str = None) -> List[Dict]:
    """
    Fetch trending topics from X/Twitter.
    Requires Twitter API v2 bearer token.
    """
    bearer_token = bearer_token or os.getenv("TWITTER_BEARER_TOKEN")
    if not bearer_token:
        return []

    try:
        # Get trends for US (WOEID 23424977)
        url = "https://api.twitter.com/2/trends/by/woeid/23424977"
        headers = {"Authorization": f"Bearer {bearer_token}"}

        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"Twitter API error: {response.status_code}")
            return []

        data = response.json()
        trends = []
        for trend in data.get("data", [])[:20]:
            trends.append({
                "source": "twitter",
                "topic": trend.get("trend_name", ""),
                "volume": trend.get("tweet_count", 0),
                "url": trend.get("url", ""),
                "timestamp": datetime.now().isoformat()
            })
        return trends
    except Exception as e:
        print(f"Twitter trends error: {e}")
        return []


def get_news_trends(api_key: str = None) -> List[Dict]:
    """
    Fetch trending news from NewsAPI.
    Free tier: 100 requests/day.
    """
    api_key = api_key or os.getenv("NEWS_API_KEY")
    if not api_key:
        # Try Google News RSS as fallback (no API key needed)
        return get_google_news_fallback()

    try:
        url = "https://newsapi.org/v2/top-headlines"
        params = {
            "apiKey": api_key,
            "country": "us",
            "pageSize": 20
        }

        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            return get_google_news_fallback()

        data = response.json()
        trends = []
        for article in data.get("articles", []):
            trends.append({
                "source": "news",
                "topic": article.get("title", ""),
                "description": article.get("description", ""),
                "url": article.get("url", ""),
                "image": article.get("urlToImage", ""),
                "timestamp": article.get("publishedAt", datetime.now().isoformat())
            })
        return trends
    except Exception as e:
        print(f"News API error: {e}")
        return get_google_news_fallback()


def get_google_news_fallback() -> List[Dict]:
    """
    Fallback: scrape Google News RSS feed (no API key needed).
    """
    try:
        import xml.etree.ElementTree as ET

        url = "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en"
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            return []

        root = ET.fromstring(response.content)
        trends = []

        for item in root.findall(".//item")[:20]:
            title = item.find("title")
            link = item.find("link")
            pub_date = item.find("pubDate")

            trends.append({
                "source": "google_news",
                "topic": title.text if title is not None else "",
                "description": "",
                "url": link.text if link is not None else "",
                "timestamp": pub_date.text if pub_date is not None else datetime.now().isoformat()
            })

        return trends
    except Exception as e:
        print(f"Google News fallback error: {e}")
        return []


def get_reddit_trends(client_id: str = None, client_secret: str = None) -> List[Dict]:
    """
    Fetch trending posts from relevant subreddits.
    """
    client_id = client_id or os.getenv("REDDIT_CLIENT_ID")
    client_secret = client_secret or os.getenv("REDDIT_CLIENT_SECRET")

    # Subreddits relevant to HairDAO
    subreddits = [
        "cryptocurrency",
        "CryptoMoonShots",
        "defi",
        "tressless",  # hair loss
        "HairTransplants",
        "memes",
        "dankmemes"
    ]

    trends = []

    # Try authenticated request first, fall back to unauthenticated
    headers = {"User-Agent": "HairDAO-MemeBot/1.0"}

    if client_id and client_secret:
        try:
            # Get OAuth token
            auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
            token_response = requests.post(
                "https://www.reddit.com/api/v1/access_token",
                auth=auth,
                data={"grant_type": "client_credentials"},
                headers=headers,
                timeout=10
            )
            if token_response.status_code == 200:
                token = token_response.json().get("access_token")
                headers["Authorization"] = f"Bearer {token}"
        except Exception as e:
            print(f"Reddit auth error: {e}")

    for subreddit in subreddits:
        try:
            url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit=5"
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code != 200:
                continue

            data = response.json()
            for post in data.get("data", {}).get("children", []):
                post_data = post.get("data", {})
                trends.append({
                    "source": "reddit",
                    "subreddit": subreddit,
                    "topic": post_data.get("title", ""),
                    "score": post_data.get("score", 0),
                    "url": f"https://reddit.com{post_data.get('permalink', '')}",
                    "image": post_data.get("url", "") if post_data.get("url", "").endswith(('.jpg', '.png', '.gif')) else "",
                    "timestamp": datetime.fromtimestamp(post_data.get("created_utc", 0)).isoformat()
                })
        except Exception as e:
            print(f"Reddit error for r/{subreddit}: {e}")
            continue

    # Sort by score
    trends.sort(key=lambda x: x.get("score", 0), reverse=True)
    return trends[:20]


def fetch_all_trends(use_cache: bool = True) -> Dict[str, List[Dict]]:
    """
    Fetch trends from all sources.
    Uses cache to avoid hitting rate limits.
    """
    # Check cache
    if use_cache and TRENDS_CACHE_FILE.exists():
        try:
            with open(TRENDS_CACHE_FILE, "r") as f:
                cache = json.load(f)

            cache_time = datetime.fromisoformat(cache.get("timestamp", "2000-01-01"))
            if datetime.now() - cache_time < timedelta(minutes=TRENDS_CACHE_DURATION):
                print("Using cached trends")
                return cache.get("trends", {})
        except Exception as e:
            print(f"Cache read error: {e}")

    print("Fetching fresh trends...")

    trends = {
        "twitter": get_twitter_trends(),
        "news": get_news_trends(),
        "reddit": get_reddit_trends(),
        "timestamp": datetime.now().isoformat()
    }

    # Save to cache
    try:
        cache_data = {
            "timestamp": datetime.now().isoformat(),
            "trends": trends
        }
        with open(TRENDS_CACHE_FILE, "w") as f:
            json.dump(cache_data, f, indent=2)
    except Exception as e:
        print(f"Cache write error: {e}")

    return trends


def get_combined_trends(limit: int = 30) -> List[Dict]:
    """
    Get all trends combined and sorted by relevance/recency.
    """
    all_trends = fetch_all_trends()

    combined = []
    for source, trends in all_trends.items():
        if source == "timestamp":
            continue
        if isinstance(trends, list):
            combined.extend(trends)

    # Remove duplicates based on similar topics
    seen_topics = set()
    unique_trends = []
    for trend in combined:
        topic_lower = trend.get("topic", "").lower()[:50]
        if topic_lower and topic_lower not in seen_topics:
            seen_topics.add(topic_lower)
            unique_trends.append(trend)

    return unique_trends[:limit]


if __name__ == "__main__":
    print("Fetching trends...")
    trends = fetch_all_trends(use_cache=False)

    print(f"\nTwitter trends: {len(trends.get('twitter', []))}")
    for t in trends.get("twitter", [])[:3]:
        print(f"  - {t.get('topic')}")

    print(f"\nNews trends: {len(trends.get('news', []))}")
    for t in trends.get("news", [])[:3]:
        print(f"  - {t.get('topic')[:60]}...")

    print(f"\nReddit trends: {len(trends.get('reddit', []))}")
    for t in trends.get("reddit", [])[:3]:
        print(f"  - [{t.get('subreddit')}] {t.get('topic')[:50]}...")
