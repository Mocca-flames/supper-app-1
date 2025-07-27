import os
from aiohttp_retry import List
import requests
from typing import Dict, Optional
from ..utils.redis_client import RedisService # Assuming RedisService is in utils

class LocationService:
    MAPBOX_BASE_URL = os.getenv("MAPBOX_BASE_URL", "https://api.mapbox.com")
    MAPBOX_ACCESS_TOKEN = os.getenv("MAPBOX_ACCESS_TOKEN")
    
    @staticmethod
    def geocode_address(address: str) -> Optional[Dict]:
        """
        Converts an address to geographic coordinates (latitude, longitude) using Mapbox Geocoding API.
        Includes caching for frequently requested addresses.
        """
        cache_key = f"geocode:{address}"
        cached_coords = RedisService.get_cached_data(cache_key)
        if cached_coords:
            return cached_coords

        if not LocationService.MAPBOX_ACCESS_TOKEN:
            raise ValueError("Mapbox access token not configured.")

        endpoint = f"{LocationService.MAPBOX_BASE_URL}/geocoding/v5/mapbox.places/{address}.json"
        params = {
            "access_token": LocationService.MAPBOX_ACCESS_TOKEN,
            "limit": 1
        }

        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()

            if data and data.get("features"):
                feature = data["features"][0]
                longitude, latitude = feature["geometry"]["coordinates"]
                coords = {
                    "latitude": latitude,
                    "longitude": longitude,
                    "place_name": feature.get("place_name")
                }
                RedisService.set_cached_data(cache_key, coords, ttl=int(os.getenv("CACHE_TTL_GEOCODING", 86400)))
                return coords
            return None
        except requests.exceptions.RequestException as e:
            print(f"Error geocoding address '{address}': {e}")
            return None

    @staticmethod
    def reverse_geocode_coordinates(longitude: float, latitude: float) -> Optional[Dict]:
        """
        Converts geographic coordinates (longitude, latitude) to a human-readable address.
        """
        cache_key = f"reverse_geocode:{longitude},{latitude}"
        cached_address = RedisService.get_cached_data(cache_key)
        if cached_address:
            return cached_address

        if not LocationService.MAPBOX_ACCESS_TOKEN:
            raise ValueError("Mapbox access token not configured.")

        endpoint = f"{LocationService.MAPBOX_BASE_URL}/geocoding/v5/mapbox.places/{longitude},{latitude}.json"
        params = {
            "access_token": LocationService.MAPBOX_ACCESS_TOKEN,
            "limit": 1
        }

        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()

            if data and data.get("features"):
                feature = data["features"][0]
                address_info = {
                    "place_name": feature.get("place_name"),
                    "address": feature.get("address"),
                    "context": feature.get("context")
                }
                RedisService.set_cached_data(cache_key, address_info, ttl=int(os.getenv("CACHE_TTL_GEOCODING", 86400)))
                return address_info
            return None
        except requests.exceptions.RequestException as e:
            print(f"Error reverse geocoding coordinates ({longitude}, {latitude}): {e}")
            return None

    @staticmethod
    def get_address_autocomplete_suggestions(query: str) -> List[Dict]:
        """
        Provides address autocomplete suggestions using Mapbox Geocoding API.
        """
        if not LocationService.MAPBOX_ACCESS_TOKEN:
            raise ValueError("Mapbox access token not configured.")

        endpoint = f"{LocationService.MAPBOX_BASE_URL}/geocoding/v5/mapbox.places/{query}.json"
        params = {
            "access_token": LocationService.MAPBOX_ACCESS_TOKEN,
            "autocomplete": True,
            "language": "en"
        }

        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()

            suggestions = []
            if data and data.get("features"):
                for feature in data["features"]:
                    suggestions.append({
                        "place_name": feature.get("place_name"),
                        "address": feature.get("address"),
                        "coordinates": feature["geometry"]["coordinates"]
                    })
            return suggestions
        except requests.exceptions.RequestException as e:
            print(f"Error getting autocomplete suggestions for '{query}': {e}")
            return []

    # Placeholder for geofencing capabilities
    @staticmethod
    def is_within_service_area(latitude: float, longitude: float) -> bool:
        """
        Checks if a given coordinate is within a predefined service area.
        This is a placeholder and would require actual geofence definitions.
        """
        # Example: Simple rectangular geofence for demonstration
        min_lat, max_lat = -34.0, -33.5 # Example bounds for a city
        min_lon, max_lon = 18.0, 19.0

        return min_lat <= latitude <= max_lat and min_lon <= longitude <= max_lon

    # Placeholder for location validation and normalization
    @staticmethod
    def validate_and_normalize_location(address: str) -> Optional[Dict]:
        """
        Validates and normalizes an address, returning standardized details.
        Combines geocoding and potentially other validation logic.
        """
        # For now, this can just call geocode_address
        return LocationService.geocode_address(address)

    # Placeholder for bulk processing capabilities
    @staticmethod
    def bulk_geocode_addresses(addresses: List[str]) -> Dict[str, Optional[Dict]]:
        """
        Processes a list of addresses for geocoding in bulk.
        This would ideally use a batch geocoding API if available or process in parallel.
        """
        results = {}
        for address in addresses:
            results[address] = LocationService.geocode_address(address)
        return results
