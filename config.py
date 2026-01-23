import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()

# API Keys (set these as environment variables or in .env file)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")

# Discord settings
DISCORD_GUILD_ID = os.getenv("DISCORD_GUILD_ID", "")  # Your server ID
DISCORD_CHANNEL_IDS = os.getenv("DISCORD_CHANNEL_IDS", "").split(",")  # Channels to scan, comma-separated

# Paths
BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
OUTPUT_DIR = BASE_DIR / "output"
DATA_DIR = BASE_DIR / "data"

# Website URLs
HAIRDAO_URL = "https://hairdao.xyz"
ANAGEN_URL = "https://anagen.xyz"

# Meme generation settings
MAX_DISCORD_MESSAGES = 500  # How many recent messages to scan
MEME_STYLES = [
    "classic_top_bottom",  # Traditional meme with top/bottom text
    "modern_caption",      # Caption above image
    "twitter_screenshot",  # Fake tweet style
    "discord_message",     # Fake Discord message style
    "ai_generated",        # Custom DALL-E generated image
]

# Ensure directories exist
TEMPLATES_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)
