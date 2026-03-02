import requests
import logging

logger = logging.getLogger(__name__)


class GeocodingService:
    """Service for converting location names to coordinates using Nominatim."""

    BASE_URL = "https://nominatim.openstreetmap.org/search"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'BabyFriendlySpots/1.0'
        })

    def geocode(self, location_name: str) -> dict:
        """
        Convert a location name to coordinates.

        Args:
            location_name: Name of the location to geocode

        Returns:
            dict with 'lat', 'lon', 'display_name' or None if not found
        """
        try:
            params = {
                'q': location_name,
                'format': 'json',
                'limit': 1
            }

            response = self.session.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if not data:
                logger.warning(f"No results found for location: {location_name}")
                return None

            result = data[0]
            return {
                'lat': float(result['lat']),
                'lon': float(result['lon']),
                'display_name': result['display_name']
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Geocoding error: {e}")
            return None
