# Baby-Friendly Spots Telegram Bot

## Project Overview
A Telegram bot that helps parents find kid-friendly locations (cafes, bars, parks, playgrounds, museums, etc.) based on a location search query.

## Target Audience
Parents with children up to 8 years old.

## Project Scope & Decisions

### Geographic Scope
- **Phase 1:** Single city (MVP)
- **Phase 2:** Multiple cities
- **Phase 3:** Whole country
- **Phase 4:** International expansion

### Age Range
- Primary: 0-8 years
- Post-MVP: Consider filtering by age ranges (0-3, 4-8)

### Data Strategy
- Prioritize up-to-date results (real-time or daily caching)
- Start with free APIs, abstract for easy migration to paid services later

## API Strategy

### Starting Point: Free APIs
- **Overpass API** (OpenStreetMap) - venue data
- **Nominatim** - geocoding (location name → coordinates)
- **Pros:** Free, unlimited usage
- **Cons:** Less detailed business info, more manual filtering needed

### Migration Option: Google Places API
- **When:** After MVP validation, when budget allows
- **Cost:** ~$17 per 1000 searches (free $200/month credit)
- **Pros:** Rich data (photos, reviews, ratings, hours, amenities)
- **Migration Effort:** Low-medium (abstraction layer recommended)

## Tech Stack (Recommended)

### Backend
- **Language:** Python
- **Telegram Library:** python-telegram-bot
- **Location API:** Overpass API (OSM) → Google Places later
- **Geocoding:** Nominatim
- **Database:** SQLite (MVP) → PostgreSQL (production)

### Hosting
- Heroku / Railway / DigitalOcean VPS

## Development Phases

### Phase 1: MVP Foundation ✅ COMPLETED
1. ✅ Set up Telegram Bot (BotFather registration)
2. ✅ Implement basic commands: /start, /help
3. ✅ Integrate Overpass API for venue search
4. ✅ Implement geocoding (location name → coordinates)
5. ✅ Query nearby venues by category (cafes, parks, playgrounds)
6. ✅ Basic filtering by venue type and distance radius (2km default)
7. ✅ Return up to 15 results with name, address, distance
8. ✅ Include map links (Google Maps)
9. ✅ Kid-friendly scoring system implemented (0-100 points)
10. ✅ Modular architecture with service layer

### Phase 2: Kid-Friendly Intelligence ⚠️ IN PROGRESS
1. ✅ Category selection system (cafes, parks, museums, indoor)
2. ✅ Negative keyword filtering implemented
3. 🔄 Fix unnamed venue filtering (parks/playgrounds)
4. 🔄 AI-based museum filtering (Claude API)
5. 🔄 Multilingual keyword support (Spanish, French, German, Czech)
6. 📋 Data enrichment from OSM tags
7. 📋 Enhanced scoring for family-related attributes

### Phase 3: Enhanced UX (Future)
1. Accept GPS location sharing
2. Handle typos/fuzzy location matching
3. Rich responses:
   - Photos (if available)
   - Ratings/reviews
   - Opening hours
4. Community ratings via `/rate` command

### Phase 4: Scale & Optimize
1. Caching layer (cache popular searches for 24h)
2. Database for user preferences and popular locations
3. Multi-city support with automatic city detection
4. Crowdsourced kid-friendly ratings

### Phase 5: Premium Features (Post-MVP)
- Age-specific filtering (0-3 vs 4-8 years)
- Parent reviews and ratings
- Save favorites functionality
- Migration to Google Places API if needed

## Timeline Estimate
- **MVP:** ✅ Complete (March 2, 2026)
- **Full Featured v1:** 6-8 weeks from MVP

## Current Status (Last Updated: March 9, 2026)

### Completed Features
- ✅ Working Telegram bot with `/start` and `/help` commands
- ✅ Location search using Nominatim geocoding
- ✅ Venue search using Overpass API (OpenStreetMap)
- ✅ **Interactive category selection** (cafes, parks, museums, indoor activities)
- ✅ Kid-friendly scoring algorithm with **negative context detection**
- ✅ Distance calculation and sorting (by score, then distance)
- ✅ Rich formatted responses with emojis, addresses, and map links
- ✅ Error handling for invalid locations and no results
- ✅ Modular service architecture (easy to swap APIs later)
- ✅ GitHub repository setup

### Recent Updates (March 9, 2026)
- ✅ Added category selection via inline keyboard buttons
- ✅ Implemented negative keyword filtering (e.g., "no baby chairs" won't boost score)
- ✅ Category filtering: cafes, parks, museums, indoor activities, or show all
- ✅ User flow: Location → Category selection → Filtered results

### Known Issues & Planned Fixes
1. **Unnamed venues filtered out** - Parks/playgrounds without names are excluded (90% loss)
   - Fix: Generate auto-names like "Playground near [street]" or keep unnamed with descriptive labels
2. **Naive museum filtering** - Shows all museums including non-kid-friendly (bullfighting, modern art)
   - Fix: Use AI-based filtering (Claude API) to analyze venue appropriateness
3. **English-only keywords** - Keyword boosting only works for English text
   - Fix: Add multilingual keywords (Spanish, French, German, Czech, etc.)

### Project Structure
```
baby-friendly-spots/
├── bot.py                      # Main bot application
├── config.py                   # Configuration and env variables
├── services/
│   ├── geocoding.py           # Nominatim geocoding service
│   └── location_search.py     # Overpass API venue search
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables (not in git)
├── .gitignore                # Git ignore rules
└── README.md                 # Project documentation
```

### How to Run
1. Install dependencies: `pip install -r requirements.txt`
2. Set up `.env` with `TELEGRAM_BOT_TOKEN`
3. Run: `python3 bot.py`

### GitHub Repository
- **URL:** https://github.com/denfisksson/baby-map-bot
- **Status:** Public, actively maintained
- **Branch:** main

## Kid-Friendly Criteria

### Scoring System (0-100 points)
**Base Scores by Type:**
- Playground: 100
- Park: 90
- Zoo/Theme Park/Water Park: 85
- Museum: 60 (needs improvement - too many non-kid-friendly results)
- Cafe/Restaurant: 50
- Fast Food: 45

**Keyword Boosting (+10 each):**
- Positive keywords: "kids", "children", "baby", "family", "playground", "play area"
- **Negative context detection:** Phrases like "no baby chairs", "not for kids" reduce score by -5

**Amenity Bonuses:**
- Changing table: +5
- High chair: +5
- Kids area: +10

**Language Support:**
- Currently: English keywords only
- Planned: Multilingual (Spanish, French, German, Czech)

## Architecture Guidelines
- Abstract location provider behind a service layer for easy API switching
- Keep Telegram bot logic separate from location search logic
- Design for horizontal scaling (multi-city support)
- Cache aggressively to reduce API costs
