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

### Phase 1: MVP Foundation (1-2 weeks)
1. Set up Telegram Bot (BotFather registration)
2. Implement basic commands: /start, /help
3. Integrate Overpass API for venue search
4. Implement geocoding (location name → coordinates)
5. Query nearby venues by category (cafes, parks, playgrounds)
6. Basic filtering by venue type and distance radius (e.g., 2km)
7. Return 10-15 results with name, address, distance
8. Include map links

### Phase 2: Kid-Friendly Intelligence (1 week)
1. Category scoring system:
   - Parks/playgrounds: high score
   - Cafes/restaurants: keyword-based filtering
   - Museums: detect children's museums
2. Data enrichment from OSM tags (amenity=playground, leisure=park)
3. Filter for family-related attributes

### Phase 3: Enhanced UX (1 week)
1. Accept GPS location sharing
2. Handle typos/fuzzy location matching
3. Add filters (e.g., "show only parks")
4. Rich responses:
   - Photos (if available)
   - Ratings/reviews
   - Opening hours
   - Inline buttons for "Get Directions"

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
- **MVP:** 3-4 weeks
- **Full Featured v1:** 6-8 weeks

## Kid-Friendly Criteria
Venues are scored based on:
- Venue type (parks, playgrounds automatically qualify)
- Amenities (high chairs, changing tables, play areas)
- Keywords in descriptions/tags ("kids", "children", "family-friendly")
- Community ratings (post-MVP feature)

## Architecture Guidelines
- Abstract location provider behind a service layer for easy API switching
- Keep Telegram bot logic separate from location search logic
- Design for horizontal scaling (multi-city support)
- Cache aggressively to reduce API costs
