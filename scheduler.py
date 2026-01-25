#!/usr/bin/env python3
"""
Automated meme generation and posting scheduler.
Generates memes on a schedule and optionally posts to Discord/Twitter.
"""
import os
import json
import time
import schedule
import asyncio
import aiohttp
from datetime import datetime
from pathlib import Path
from typing import Optional

from config import OUTPUT_DIR, DATA_DIR
from scraper import load_website_content
from discord_scanner import load_discord_content
from meme_generator import generate_meme_concept
from image_creator import create_meme_from_concept, save_meme

# Configuration
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_MEME_WEBHOOK")
TWITTER_ENABLED = os.getenv("TWITTER_ENABLED", "false").lower() == "true"

# Posting queue
QUEUE_FILE = DATA_DIR / "posting_queue.json"


def load_queue() -> list:
    """Load the posting queue."""
    if QUEUE_FILE.exists():
        with open(QUEUE_FILE, 'r') as f:
            return json.load(f)
    return []


def save_queue(queue: list):
    """Save the posting queue."""
    with open(QUEUE_FILE, 'w') as f:
        json.dump(queue, f, indent=2)


def add_to_queue(meme_path: str, concept: dict, scheduled_time: Optional[str] = None):
    """Add a meme to the posting queue."""
    queue = load_queue()
    queue.append({
        "path": meme_path,
        "concept": concept,
        "scheduled_time": scheduled_time,
        "created_at": datetime.now().isoformat(),
        "posted": False
    })
    save_queue(queue)


async def post_to_discord(meme_path: str, caption: str = None) -> bool:
    """Post a meme to Discord via webhook."""
    if not DISCORD_WEBHOOK_URL:
        print("Discord webhook not configured")
        return False
    
    try:
        with open(meme_path, 'rb') as f:
            data = aiohttp.FormData()
            data.add_field('file', f, filename=Path(meme_path).name)
            if caption:
                data.add_field('content', caption)
            
            async with aiohttp.ClientSession() as session:
                async with session.post(DISCORD_WEBHOOK_URL, data=data) as resp:
                    if resp.status == 200 or resp.status == 204:
                        print(f"Posted to Discord: {meme_path}")
                        return True
                    else:
                        print(f"Discord post failed: {resp.status}")
                        return False
    except Exception as e:
        print(f"Error posting to Discord: {e}")
        return False


def generate_and_queue(count: int = 1, style: str = None, auto_post: bool = False):
    """Generate memes and add them to the queue."""
    print(f"\nGenerating {count} meme(s)...")
    
    website_data = load_website_content()
    discord_data = load_discord_content()
    
    for i in range(count):
        try:
            print(f"  [{i+1}/{count}] Generating concept...")
            concept = generate_meme_concept(website_data, discord_data, style)
            
            print(f"  Creating image...")
            img = create_meme_from_concept(concept)
            
            path = save_meme(img, concept)
            print(f"  Saved: {path}")
            
            # Add to queue
            add_to_queue(str(path), concept)
            
            # Optionally post immediately
            if auto_post:
                caption = concept.get('caption', '')
                asyncio.run(post_to_discord(str(path), caption))
            
        except Exception as e:
            print(f"  Error: {e}")
            continue
    
    print(f"\nGeneration complete. Queue size: {len(load_queue())}")


def process_queue():
    """Process the posting queue."""
    queue = load_queue()
    now = datetime.now()
    
    for item in queue:
        if item.get('posted'):
            continue
            
        scheduled = item.get('scheduled_time')
        if scheduled:
            scheduled_dt = datetime.fromisoformat(scheduled)
            if now < scheduled_dt:
                continue
        
        # Post the meme
        path = item.get('path')
        caption = item.get('concept', {}).get('caption', '')
        
        if Path(path).exists():
            success = asyncio.run(post_to_discord(path, caption))
            if success:
                item['posted'] = True
                item['posted_at'] = now.isoformat()
    
    save_queue(queue)


def daily_generation():
    """Daily scheduled meme generation."""
    print(f"\n[{datetime.now()}] Running daily meme generation...")
    generate_and_queue(count=3, auto_post=False)


def hourly_posting():
    """Hourly check for queued posts."""
    print(f"\n[{datetime.now()}] Processing posting queue...")
    process_queue()


def run_scheduler():
    """Run the scheduler."""
    print("=" * 50)
    print("HAIRDAO MEME SCHEDULER")
    print("=" * 50)
    print("\nSchedule:")
    print("  - Daily @ 9 AM: Generate 3 memes")
    print("  - Hourly: Process posting queue")
    print("\nPress Ctrl+C to stop\n")
    
    # Schedule tasks
    schedule.every().day.at("09:00").do(daily_generation)
    schedule.every().hour.do(hourly_posting)
    
    # Run immediately on start
    daily_generation()
    
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Meme Generation Scheduler")
    parser.add_argument("--generate", "-g", type=int, help="Generate N memes now")
    parser.add_argument("--post", action="store_true", help="Auto-post generated memes")
    parser.add_argument("--process-queue", action="store_true", help="Process posting queue")
    parser.add_argument("--run", action="store_true", help="Run the scheduler")
    
    args = parser.parse_args()
    
    if args.generate:
        generate_and_queue(args.generate, auto_post=args.post)
    elif args.process_queue:
        process_queue()
    elif args.run:
        run_scheduler()
    else:
        parser.print_help()
