# Baby-Friendly Spots Telegram Bot

A Telegram bot that helps parents find kid-friendly locations based on location queries.

## Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Configure your bot token:**
```bash
cp .env.example .env
```
Edit `.env` and add your Telegram bot token from BotFather.

3. **Run the bot:**
```bash
python bot.py
```

## Project Structure

- `bot.py` - Main bot application
- `config.py` - Configuration and environment variables
- `requirements.txt` - Python dependencies
- `CLAUDE.md` - Project documentation and roadmap

## Development Status

- ✅ Phase 1: Basic bot setup with /start and /help commands
- 🚧 Phase 1: Location API integration (in progress)
- ⏳ Phase 2: Kid-friendly intelligence
- ⏳ Phase 3: Enhanced UX
