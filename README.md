# 🧬 HairDAO Meme Generator

> AI-powered, trend-aware meme generation for the HairDAO community.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![HairDAO](https://img.shields.io/badge/HairDAO-WAGMI-purple.svg)

Generate on-brand memes for HairDAO by combining:
- 🔍 **Discord community insights** – catchphrases, active users, inside jokes
- 📈 **Real-time trends** – Twitter/X, Reddit, and crypto news
- 🎨 **AI image generation** – DALL-E 3 for custom visuals
- 🧠 **GPT-powered humor** – contextually relevant captions

---

## ✨ Features

### 📡 Discord Scanner
Scans your HairDAO Discord server to extract:
- Active community members (for natural mentions)
- Frequently used words and catchphrases
- Memorable high-engagement messages
- Custom emojis and inside jokes

### 📊 Trend Analyzer
Fetches and analyzes trending topics from:
- Twitter/X trending hashtags
- Reddit r/cryptocurrency, r/tressless, r/HairLoss
- Crypto news aggregators
- Filters for hair loss + crypto relevance using GPT

### 🎨 Meme Styles
- **Classic Top/Bottom** – Traditional Impact font memes
- **Modern Caption** – Clean caption above image
- **Twitter Screenshot** – Fake tweet style
- **Discord Message** – Community message style
- **AI Generated** – Custom DALL-E 3 images with text overlay

### 🌐 Web UI
Beautiful dark-themed web interface for:
- Viewing trending topics and their meme potential
- Generating memes with custom topics
- Browsing the meme gallery
- One-click downloads

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        HairDAO Meme Generator                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │   Discord    │    │    Trend     │    │   Website    │      │
│  │   Scanner    │    │   Fetcher    │    │   Scraper    │      │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘      │
│         │                   │                   │               │
│         └───────────────────┼───────────────────┘               │
│                             ▼                                   │
│                   ┌─────────────────┐                           │
│                   │  Trend Analyzer │                           │
│                   │    (GPT-4o)     │                           │
│                   └────────┬────────┘                           │
│                            │                                    │
│                            ▼                                    │
│                   ┌─────────────────┐                           │
│                   │ Meme Generator  │                           │
│                   │    (GPT-4o)     │                           │
│                   └────────┬────────┘                           │
│                            │                                    │
│              ┌─────────────┼─────────────┐                      │
│              ▼             ▼             ▼                      │
│      ┌───────────┐  ┌───────────┐  ┌───────────┐               │
│      │  Template │  │   DALL-E  │  │   Text    │               │
│      │  Library  │  │  3 Image  │  │  Overlay  │               │
│      └─────┬─────┘  └─────┬─────┘  └─────┬─────┘               │
│            └──────────────┼──────────────┘                      │
│                           ▼                                     │
│                   ┌─────────────────┐                           │
│                   │  Image Creator  │                           │
│                   │    (Pillow)     │                           │
│                   └────────┬────────┘                           │
│                            │                                    │
│                            ▼                                    │
│                   ┌─────────────────┐                           │
│                   │  Output Memes   │                           │
│                   │   (PNG/JPG)     │                           │
│                   └─────────────────┘                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- OpenAI API key (for GPT-4o and DALL-E 3)
- Discord bot token (optional, for community scanning)

### Installation

```bash
# Clone the repository
git clone https://github.com/hairdao/meme-generator.git
cd meme-generator

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env
```

### Configuration

Edit `.env` with your credentials:

```env
# Required
OPENAI_API_KEY=sk-your-openai-api-key

# Optional: Discord integration
DISCORD_BOT_TOKEN=your-discord-bot-token
DISCORD_GUILD_ID=your-server-id
DISCORD_CHANNEL_IDS=channel1,channel2,channel3
```

---

## 💻 Usage

### CLI Commands

```bash
# Generate a single meme (default)
python main.py

# Generate multiple memes
python main.py --generate 5

# Generate with specific style
python main.py --generate 3 --style ai_generated

# Refresh data sources (scrape websites + Discord)
python main.py --refresh

# Refresh without Discord (websites only)
python main.py --refresh --no-discord

# Interactive mode
python main.py --interactive
```

### Interactive Mode Commands

```
> generate              # Generate a meme with random style
> generate ai_generated # Generate with specific style
> batch 10             # Generate 10 memes at once
> refresh              # Refresh all data sources
> quit                 # Exit
```

### Meme Styles

| Style | Description |
|-------|-------------|
| `classic_top_bottom` | Traditional meme with white Impact text |
| `modern_caption` | Clean caption above the image |
| `twitter_screenshot` | Fake tweet format |
| `discord_message` | Fake Discord message |
| `ai_generated` | Custom DALL-E 3 generated image |

### Web UI

```bash
# Start the web server
python web_app.py

# Or with uvicorn for production
uvicorn web_app:app --host 0.0.0.0 --port 8000
```

Then open http://localhost:8000 in your browser.

---

## 📁 Project Structure

```
hairdao-meme-generator/
├── main.py              # CLI entry point
├── web_app.py           # FastAPI web server
├── config.py            # Configuration and env vars
├── meme_generator.py    # GPT-powered concept generation
├── image_creator.py     # Image composition with Pillow
├── ai_image_generator.py # DALL-E 3 integration
├── discord_scanner.py   # Discord community scanning
├── trend_analyzer.py    # Trend relevance analysis
├── trend_fetcher.py     # Multi-source trend fetching
├── scraper.py           # HairDAO/Anagen website scraping
├── templates/
│   ├── base.html        # Jinja2 base template
│   ├── home.html        # Homepage template
│   ├── generate.html    # Generation page
│   ├── gallery.html     # Meme gallery
│   └── memes/           # HairDAO meme templates
├── data/                # Cached data (auto-generated)
├── output/              # Generated memes (auto-generated)
├── requirements.txt     # Python dependencies
└── .env.example         # Environment template
```

---

## 🎯 HairDAO Meme Templates

The generator includes HairDAO-specific meme templates:

| Template | Use Case |
|----------|----------|
| `bald_wojak` | Hair loss struggle reactions |
| `hair_diamond_hands` | Holding $HAIR through dips |
| `regrowth_gigachad` | Treatment success stories |
| `minoxidil_vs_hairdao` | Product comparisons |
| `norwood_reaper` | Hair loss progression humor |
| `anagen_phase` | Hair cycle science memes |
| `wagmi_hair` | Community optimism |
| `before_after` | Treatment results |

---

## 🔧 API Reference

### Generate Meme Concept

```python
from meme_generator import generate_meme_concept

concept = generate_meme_concept(
    website_data=None,  # Auto-loads if None
    discord_data=None,  # Auto-loads if None
    style="modern_caption"
)
```

### Create Image from Concept

```python
from image_creator import create_meme_from_concept, save_meme

img = create_meme_from_concept(concept)
path = save_meme(img, concept)
```

### Generate Trending Memes

```python
from trend_analyzer import generate_trending_memes

memes = generate_trending_memes(count=5)
```

---

## 🚢 Deployment

### Railway

The project includes Railway configuration:

```bash
# Deploy to Railway
railway up
```

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "web_app:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-meme`)
3. Commit your changes (`git commit -m 'Add amazing meme template'`)
4. Push to the branch (`git push origin feature/amazing-meme`)
5. Open a Pull Request

---

## 📜 License

MIT License - feel free to use for your own meme needs!

---

## 🔗 Links

- [HairDAO Website](https://hairdao.xyz)
- [Anagen](https://anagen.xyz)
- [HairDAO Discord](https://discord.gg/hairdao)
- [HairDAO Twitter](https://twitter.com/HairDAO)

---

**Built with 💚 for the HairDAO community. WAGMI! 🧬**
