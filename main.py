#!/usr/bin/env python3
"""
HairDAO Meme Generator Pipeline

Main entry point for generating memes about HairDAO and Anagen.
"""
import argparse
import json
from datetime import datetime
from pathlib import Path

from config import OUTPUT_DIR, DATA_DIR
from scraper import scrape_all, load_website_content
from discord_scanner import scan_discord, load_discord_content
from meme_generator import generate_meme_concept, generate_multiple_concepts
from image_creator import create_meme_from_concept, save_meme


def refresh_data(include_discord: bool = True):
    """Refresh website and Discord data."""
    print("=" * 50)
    print("REFRESHING DATA SOURCES")
    print("=" * 50)

    print("\n[1/2] Scraping websites...")
    website_data = scrape_all()
    print(f"  - HairDAO: {len(website_data.get('hairdao', {}).get('headings', []))} headings found")
    print(f"  - Anagen: {len(website_data.get('anagen', {}).get('headings', []))} headings found")

    if include_discord:
        print("\n[2/2] Scanning Discord...")
        discord_data = scan_discord()
        if discord_data:
            print(f"  - Users found: {len(discord_data.get('active_users', []))}")
            print(f"  - Catchphrases: {len(discord_data.get('catchphrases', []))}")
    else:
        print("\n[2/2] Skipping Discord scan")

    print("\nData refresh complete!")


def generate_memes(count: int = 5, style: str = None):
    """Generate memes and save them."""
    print("=" * 50)
    print(f"GENERATING {count} MEMES")
    print("=" * 50)

    # Load data
    website_data = load_website_content()
    discord_data = load_discord_content()

    generated = []

    for i in range(count):
        print(f"\n[{i+1}/{count}] Generating meme concept...")

        try:
            concept = generate_meme_concept(website_data, discord_data, style)
            print(f"  Style: {concept.get('style')}")
            print(f"  Template: {concept.get('template_suggestion')}")

            if concept.get('top_text'):
                print(f"  Top: {concept.get('top_text')[:50]}...")
            if concept.get('bottom_text'):
                print(f"  Bottom: {concept.get('bottom_text')[:50]}...")
            if concept.get('caption'):
                print(f"  Caption: {concept.get('caption')[:50]}...")

            print("  Creating image...")
            img = create_meme_from_concept(concept)

            output_path = save_meme(img, concept)

            generated.append({
                "path": str(output_path),
                "concept": concept
            })

        except Exception as e:
            print(f"  Error: {e}")
            continue

    # Save generation log
    log_file = DATA_DIR / f"generation_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(log_file, 'w') as f:
        json.dump(generated, f, indent=2)

    print("\n" + "=" * 50)
    print(f"COMPLETE! Generated {len(generated)} memes")
    print(f"Output folder: {OUTPUT_DIR}")
    print(f"Log file: {log_file}")
    print("=" * 50)

    return generated


def interactive_mode():
    """Interactive mode for generating memes one at a time."""
    print("=" * 50)
    print("HAIRDAO MEME GENERATOR - INTERACTIVE MODE")
    print("=" * 50)
    print("\nCommands:")
    print("  generate [style] - Generate a meme (optional: classic_top_bottom, modern_caption, twitter_screenshot, discord_message)")
    print("  refresh          - Refresh website/Discord data")
    print("  batch <n>        - Generate n memes at once")
    print("  quit             - Exit")
    print()

    website_data = load_website_content()
    discord_data = load_discord_content()

    while True:
        try:
            cmd = input("\n> ").strip().lower()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break

        if not cmd:
            continue

        parts = cmd.split()
        action = parts[0]

        if action == "quit" or action == "exit":
            print("Goodbye!")
            break

        elif action == "generate":
            style = parts[1] if len(parts) > 1 else None
            print("\nGenerating meme...")
            try:
                concept = generate_meme_concept(website_data, discord_data, style)
                print(f"\nConcept:")
                print(f"  Style: {concept.get('style')}")
                print(f"  Template: {concept.get('template_suggestion')}")
                print(f"  Top: {concept.get('top_text')}")
                print(f"  Bottom: {concept.get('bottom_text')}")
                print(f"  Caption: {concept.get('caption')}")
                print(f"  Humor: {concept.get('humor_explanation')}")

                img = create_meme_from_concept(concept)
                path = save_meme(img, concept)
                print(f"\nSaved to: {path}")
            except Exception as e:
                print(f"Error: {e}")

        elif action == "refresh":
            refresh_data()
            website_data = load_website_content()
            discord_data = load_discord_content()

        elif action == "batch":
            count = int(parts[1]) if len(parts) > 1 else 5
            generate_memes(count)

        else:
            print(f"Unknown command: {action}")


def main():
    parser = argparse.ArgumentParser(description="HairDAO Meme Generator")
    parser.add_argument("--refresh", action="store_true", help="Refresh website and Discord data")
    parser.add_argument("--no-discord", action="store_true", help="Skip Discord scanning during refresh")
    parser.add_argument("--generate", "-g", type=int, default=0, help="Generate N memes")
    parser.add_argument("--style", "-s", type=str, help="Meme style (classic_top_bottom, modern_caption, twitter_screenshot, discord_message)")
    parser.add_argument("--interactive", "-i", action="store_true", help="Run in interactive mode")

    args = parser.parse_args()

    if args.refresh:
        refresh_data(include_discord=not args.no_discord)

    if args.generate > 0:
        generate_memes(args.generate, args.style)
    elif args.interactive:
        interactive_mode()
    elif not args.refresh:
        # Default: generate 1 meme
        print("No arguments provided. Generating 1 meme...")
        print("Use --help for options, or -i for interactive mode\n")
        generate_memes(1, args.style)


if __name__ == "__main__":
    main()
