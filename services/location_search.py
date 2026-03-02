import requests
import logging
from typing import List, Dict
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

    def __init__(self):
        self.session = requests.Session()

    def search_nearby_venues(self, lat: float, lon: float, radius_km: float = 2.0, max_results: int = 15) -> List[Dict]:
        """
        Search for kid-friendly venues near a location.

        Args:
            lat: Latitude
            lon: Longitude
            radius_km: Search radius in kilometers
            max_results: Maximum number of results to return

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

        # Boost for kid-friendly keywords in name or description
        name_lower = tags.get('name', '').lower()
        description_lower = tags.get('description', '').lower()

        kid_keywords = ['kid', 'child', 'baby', 'family', 'playground', 'play area']
        for keyword in kid_keywords:
            if keyword in name_lower or keyword in description_lower:
                score += 10

        # Check for family-friendly amenities
        if tags.get('changing_table') == 'yes':
            score += 5
        if tags.get('highchair') == 'yes':
            score += 5
        if tags.get('kids_area') == 'yes':
            score += 10

        return min(score, 100)

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
