"""
Scans Discord server for community references, usernames, and inside jokes.
"""
import asyncio
import json
import discord
from collections import Counter
from datetime import datetime, timedelta
from config import (
    DISCORD_BOT_TOKEN,
    DISCORD_GUILD_ID,
    DISCORD_CHANNEL_IDS,
    MAX_DISCORD_MESSAGES,
    DATA_DIR
)


class DiscordScanner(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(intents=intents)
        self.scan_data = {
            "active_users": [],
            "frequent_words": [],
            "memorable_messages": [],
            "emojis": [],
            "catchphrases": [],
            "topics": []
        }

    async def on_ready(self):
        print(f"Logged in as {self.user}")
        await self.scan_server()
        await self.close()

    async def scan_server(self):
        """Scan the Discord server for meme-worthy content."""
        if not DISCORD_GUILD_ID:
            print("No DISCORD_GUILD_ID set, skipping Discord scan")
            return

        guild = self.get_guild(int(DISCORD_GUILD_ID))
        if not guild:
            print(f"Could not find guild {DISCORD_GUILD_ID}")
            return

        print(f"Scanning server: {guild.name}")

        all_messages = []
        user_message_counts = Counter()
        word_counts = Counter()
        emoji_counts = Counter()

        # Determine which channels to scan
        channels_to_scan = []
        if DISCORD_CHANNEL_IDS and DISCORD_CHANNEL_IDS[0]:
            for channel_id in DISCORD_CHANNEL_IDS:
                channel = guild.get_channel(int(channel_id.strip()))
                if channel:
                    channels_to_scan.append(channel)
        else:
            # Scan all text channels
            channels_to_scan = [c for c in guild.text_channels if c.permissions_for(guild.me).read_messages]

        for channel in channels_to_scan:
            print(f"  Scanning #{channel.name}...")
            try:
                messages_per_channel = MAX_DISCORD_MESSAGES // len(channels_to_scan)
                async for message in channel.history(limit=messages_per_channel):
                    if message.author.bot:
                        continue

                    all_messages.append({
                        "author": message.author.display_name,
                        "content": message.content,
                        "reactions": sum(r.count for r in message.reactions) if message.reactions else 0,
                        "timestamp": message.created_at.isoformat()
                    })

                    user_message_counts[message.author.display_name] += 1

                    # Count words (filter short words and common ones)
                    words = message.content.lower().split()
                    for word in words:
                        if len(word) > 3 and word.isalpha():
                            word_counts[word] += 1

                    # Count custom emojis
                    for emoji in message.guild.emojis:
                        if str(emoji) in message.content:
                            emoji_counts[str(emoji)] += 1

            except discord.Forbidden:
                print(f"    No access to #{channel.name}")
            except Exception as e:
                print(f"    Error scanning #{channel.name}: {e}")

        # Find memorable messages (high reactions or engagement)
        memorable = sorted(all_messages, key=lambda x: x["reactions"], reverse=True)[:20]

        # Extract potential catchphrases (repeated phrases)
        phrase_counts = Counter()
        for msg in all_messages:
            content = msg["content"].lower()
            if 5 < len(content) < 100:  # Reasonable phrase length
                phrase_counts[content] += 1
        catchphrases = [phrase for phrase, count in phrase_counts.most_common(20) if count > 2]

        # Compile results
        self.scan_data = {
            "active_users": [user for user, count in user_message_counts.most_common(30)],
            "frequent_words": [word for word, count in word_counts.most_common(50)
                            if word not in ['that', 'this', 'with', 'have', 'will', 'from', 'they', 'been', 'would', 'could', 'should', 'about', 'there', 'their', 'what', 'when', 'your', 'just', 'like', 'more', 'some']],
            "memorable_messages": memorable,
            "emojis": [emoji for emoji, count in emoji_counts.most_common(20)],
            "catchphrases": catchphrases,
            "scan_date": datetime.now().isoformat(),
            "total_messages_scanned": len(all_messages)
        }

        # Save to file
        output_file = DATA_DIR / "discord_content.json"
        with open(output_file, 'w') as f:
            json.dump(self.scan_data, f, indent=2)

        print(f"\nSaved Discord data to {output_file}")
        print(f"  - Active users found: {len(self.scan_data['active_users'])}")
        print(f"  - Memorable messages: {len(self.scan_data['memorable_messages'])}")
        print(f"  - Catchphrases found: {len(self.scan_data['catchphrases'])}")


def scan_discord():
    """Run the Discord scanner."""
    if not DISCORD_BOT_TOKEN:
        print("No DISCORD_BOT_TOKEN set. Please set this environment variable.")
        print("To create a bot token:")
        print("1. Go to https://discord.com/developers/applications")
        print("2. Create a new application")
        print("3. Go to Bot section and create a bot")
        print("4. Copy the token and set DISCORD_BOT_TOKEN env var")
        print("5. Invite bot to your server with message read permissions")
        return None

    client = DiscordScanner()
    client.run(DISCORD_BOT_TOKEN)
    return client.scan_data


def load_discord_content() -> dict:
    """Load cached Discord content or return empty dict."""
    cache_file = DATA_DIR / "discord_content.json"

    if cache_file.exists():
        with open(cache_file, 'r') as f:
            return json.load(f)

    return {
        "active_users": [],
        "frequent_words": [],
        "memorable_messages": [],
        "emojis": [],
        "catchphrases": []
    }


if __name__ == "__main__":
    scan_discord()
