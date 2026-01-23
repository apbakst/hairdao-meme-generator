#!/bin/bash
# HairDAO Meme Generator Setup Script

echo "Setting up HairDAO Meme Generator..."

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Set your OpenAI API key:"
echo "   export OPENAI_API_KEY='your-key-here'"
echo ""
echo "2. (Optional) Set up Discord bot for community references:"
echo "   export DISCORD_BOT_TOKEN='your-bot-token'"
echo "   export DISCORD_GUILD_ID='your-server-id'"
echo "   export DISCORD_CHANNEL_IDS='channel1,channel2'  # optional, scans all if not set"
echo ""
echo "3. Run the generator:"
echo "   python main.py --refresh      # Refresh data from websites/Discord"
echo "   python main.py -g 5           # Generate 5 memes"
echo "   python main.py -i             # Interactive mode"
echo ""
