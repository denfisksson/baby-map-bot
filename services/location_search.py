import requests
import logging
import re
from typing import List, Dict, Optional
from math import radians, cos, sin, asin, sqrt

logger = logging.getLogger(__name__)


class LocationSearchService:
    """Service for searching kid-friendly venues using Overpass API (OpenStreetMap)."""

    OVERPASS_URL = "https://overpass-api.de/api/interpreter"

    # Kid-friendly venue categories with OSM tags
    KID_FRIENDLY_CATEGORIES = {
        'playground': {'leisure': 'playground'},
        'park': {'leisure': 'park'},
        'cafe': {'amenity': 'cafe'},
        'restaurant': {'amenity': 'restaurant'},
        'fast_food': {'amenity': 'fast_food'},
        'museum': {'tourism': 'museum'},
        'zoo': {'tourism': 'zoo'},
        'theme_park': {'tourism': 'theme_park'},
        'water_park': {'leisure': 'water_park'},
    }

    # Negative patterns that indicate non-kid-friendly context
    NEGATIVE_PATTERNS = [
        r'\bno\s+',           # "no baby chairs"
        r'\bnot\s+',          # "not for kids"
        r'\bwithout\s+',      # "without children's menu"
        r"doesn't\s+",        # "doesn't have kids area"
        r"don't\s+",          # "don't bring babies"
        r'\badults?\s+only',  # "adults only"
    ]

    def __init__(self):
        self.session = requests.Session()

    def search_nearby_venues(self, lat: float, lon: float, radius_km: float = 2.0, max_results: int = 15, category: Optional[str] = None) -> List[Dict]:
        """
        Search for kid-friendly venues near a location.

        Args:
            lat: Latitude
            lon: Longitude
            radius_km: Search radius in kilometers
            max_results: Maximum number of results to return
            category: Optional category filter (cafes, parks, museums, indoor, all)

        Returns:
            List of venue dictionaries
        """
        radius_meters = int(radius_km * 1000)

        # Build Overpass query
        query = self._build_overpass_query(lat, lon, radius_meters)

        try:
            response = self.session.post(
                self.OVERPASS_URL,
                data={'data': query},
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            venues = self._parse_overpass_response(data, lat, lon)

            # Filter by category if specified
            if category:
                venues = [v for v in venues if self._matches_category(v['type'], category)]

            # Sort by kid-friendly score and distance
            venues = sorted(venues, key=lambda x: (-x['kid_friendly_score'], x['distance_km']))

            return venues[:max_results]

        except requests.exceptions.RequestException as e:
            logger.error(f"Overpass API error: {e}")
            return []

    def _build_overpass_query(self, lat: float, lon: float, radius: int) -> str:
        """Build Overpass QL query for kid-friendly venues."""

        # Query for multiple amenity types
        queries = []

        # Playgrounds and parks (highest priority)
        queries.append(f'node["leisure"="playground"](around:{radius},{lat},{lon});')
        queries.append(f'way["leisure"="playground"](around:{radius},{lat},{lon});')
        queries.append(f'node["leisure"="park"](around:{radius},{lat},{lon});')
        queries.append(f'way["leisure"="park"](around:{radius},{lat},{lon});')

        # Cafes and restaurants
        queries.append(f'node["amenity"="cafe"](around:{radius},{lat},{lon});')
        queries.append(f'node["amenity"="restaurant"](around:{radius},{lat},{lon});')
        queries.append(f'node["amenity"="fast_food"](around:{radius},{lat},{lon});')

        # Tourist attractions
        queries.append(f'node["tourism"="museum"](around:{radius},{lat},{lon});')
        queries.append(f'node["tourism"="zoo"](around:{radius},{lat},{lon});')
        queries.append(f'node["tourism"="theme_park"](around:{radius},{lat},{lon});')

        query_union = ''.join(queries)

        return f"""
        [out:json][timeout:25];
        (
          {query_union}
        );
        out body;
        >;
        out skel qt;
        """

    def _parse_overpass_response(self, data: dict, origin_lat: float, origin_lon: float) -> List[Dict]:
        """Parse Overpass API response into venue objects."""
        venues = []

        for element in data.get('elements', []):
            if element['type'] not in ['node', 'way']:
                continue

            tags = element.get('tags', {})

            # Skip if no name
            if 'name' not in tags:
                continue

            # Get coordinates
            if element['type'] == 'node':
                lat = element['lat']
                lon = element['lon']
            elif element['type'] == 'way':
                # For ways, we'd need to get center point, skip for now
                continue
            else:
                continue

            # Calculate distance
            distance_km = self._calculate_distance(origin_lat, origin_lon, lat, lon)

            # Determine venue type and kid-friendly score
            venue_type = self._determine_venue_type(tags)
            kid_friendly_score = self._calculate_kid_friendly_score(tags, venue_type)

            venue = {
                'name': tags['name'],
                'type': venue_type,
                'lat': lat,
                'lon': lon,
                'distance_km': round(distance_km, 2),
                'address': self._extract_address(tags),
                'kid_friendly_score': kid_friendly_score,
                'tags': tags
            }

            venues.append(venue)

        return venues

    def _determine_venue_type(self, tags: dict) -> str:
        """Determine the venue type from OSM tags."""
        if tags.get('leisure') == 'playground':
            return 'Playground'
        elif tags.get('leisure') == 'park':
            return 'Park'
        elif tags.get('amenity') == 'cafe':
            return 'Cafe'
        elif tags.get('amenity') == 'restaurant':
            return 'Restaurant'
        elif tags.get('amenity') == 'fast_food':
            return 'Fast Food'
        elif tags.get('tourism') == 'museum':
            return 'Museum'
        elif tags.get('tourism') == 'zoo':
            return 'Zoo'
        elif tags.get('tourism') == 'theme_park':
            return 'Theme Park'
        elif tags.get('leisure') == 'water_park':
            return 'Water Park'
        else:
            return 'Other'

    def _calculate_kid_friendly_score(self, tags: dict, venue_type: str) -> int:
        """Calculate kid-friendly score (0-100)."""
        score = 0

        # Base score by venue type
        type_scores = {
            'Playground': 100,
            'Park': 90,
            'Zoo': 85,
            'Theme Park': 85,
            'Water Park': 85,
            'Museum': 60,
            'Cafe': 50,
            'Restaurant': 50,
            'Fast Food': 45,
        }
        score = type_scores.get(venue_type, 30)

        # Boost for kid-friendly keywords in name or description (with negative context detection)
        name_lower = tags.get('name', '').lower()
        description_lower = tags.get('description', '').lower()

        kid_keywords = ['kid', 'child', 'baby', 'family', 'playground', 'play area']
        for keyword in kid_keywords:
            # Check in name
            if keyword in name_lower:
                if not self._has_negative_context(name_lower, keyword):
                    score += 10
                else:
                    score -= 5  # Penalize explicit negative mentions

            # Check in description
            if keyword in description_lower:
                if not self._has_negative_context(description_lower, keyword):
                    score += 10
                else:
                    score -= 5

        # Check for family-friendly amenities
        if tags.get('changing_table') == 'yes':
            score += 5
        if tags.get('highchair') == 'yes':
            score += 5
        if tags.get('kids_area') == 'yes':
            score += 10

        return min(max(score, 0), 100)  # Clamp between 0-100

    def _extract_address(self, tags: dict) -> str:
        """Extract address from OSM tags."""
        address_parts = []

        if 'addr:street' in tags:
            street = tags['addr:street']
            if 'addr:housenumber' in tags:
                street = f"{tags['addr:housenumber']} {street}"
            address_parts.append(street)

        if 'addr:city' in tags:
            address_parts.append(tags['addr:city'])

        return ', '.join(address_parts) if address_parts else 'Address not available'

    def _has_negative_context(self, text: str, keyword: str, window: int = 30) -> bool:
        """
        Check if a keyword appears within negative context.

        Args:
            text: The full text to search
            keyword: The keyword to check
            window: Character window before keyword to check for negatives

        Returns:
            True if keyword is in negative context, False otherwise
        """
        # Find all positions where keyword appears
        keyword_positions = [m.start() for m in re.finditer(re.escape(keyword), text)]

        for pos in keyword_positions:
            # Extract text window before the keyword
            start = max(0, pos - window)
            context_window = text[start:pos + len(keyword)]

            # Check if any negative pattern appears in the window
            for pattern in self.NEGATIVE_PATTERNS:
                if re.search(pattern, context_window, re.IGNORECASE):
                    return True

        return False

    def _matches_category(self, venue_type: str, category: str) -> bool:
        """Check if venue type matches requested category."""
        category_map = {
            'cafes': ['Cafe', 'Restaurant', 'Fast Food'],
            'parks': ['Park', 'Playground'],
            'museums': ['Museum'],
            'indoor': ['Zoo', 'Theme Park', 'Water Park'],
            'all': None  # No filtering
        }

        if category == 'all' or category not in category_map:
            return True

        allowed_types = category_map.get(category)
        if allowed_types is None:
            return True

        return venue_type in allowed_types

    @staticmethod
    def _calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates using Haversine formula."""
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))

        # Earth radius in kilometers
        r = 6371

        return c * r
