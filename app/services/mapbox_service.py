import requests
from requests.adapters import HTTPAdapter, Retry
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class MapboxService:
    def __init__(self):
        self.base_url = settings.MAPBOX_BASE_URL
        self.api_version = settings.MAPBOX_API_VERSION
        self.access_token = settings.MAPBOX_ACCESS_TOKEN
        self.timeout = settings.MAPBOX_REQUEST_TIMEOUT
        self.retry_attempts = settings.MAPBOX_RETRY_ATTEMPTS
        self.requests_per_minute = settings.MAPBOX_REQUESTS_PER_MINUTE
        self.requests_per_hour = settings.MAPBOX_REQUESTS_PER_HOUR

        self.session = self._create_session()

    def _create_session(self):
        session = requests.Session()
        retries = Retry(
            total=self.retry_attempts,
            backoff_factor=0.1,
            status_forcelist=[500, 502, 503, 504]
        )
        session.mount("http://", HTTPAdapter(max_retries=retries))
        session.mount("https://", HTTPAdapter(max_retries=retries))
        return session

    def _build_url(self, endpoint: str):
        return f"{self.base_url}/{self.api_version}/{endpoint}"

    def _make_request(self, url: str, params: dict):
        params["access_token"] = self.access_token
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error for {url}: {e.response.status_code} - {e.response.text}")
            raise
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error for {url}: {e}")
            raise
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout error for {url}: {e}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error for {url}: {e}")
            raise

    def get_directions(self, origin: tuple, destination: tuple, profile: str = "driving", alternatives: bool = False):
        """
        Calculates directions between two points.
        Origin and destination should be (longitude, latitude) tuples.
        Profile can be 'driving', 'walking', 'cycling'.
        """
        coordinates = f"{origin[0]},{origin[1]};{destination[0]},{destination[1]}"
        endpoint = f"directions/v5/mapbox/{profile}/{coordinates}"
        url = self._build_url(endpoint)
        params = {
            "alternatives": "true" if alternatives else "false",
            "geometries": "geojson",
            "overview": "full",
            "steps": "false",
            "annotations": "duration,distance,speed"
        }
        logger.info(f"Requesting directions from {origin} to {destination} with profile {profile}")
        return self._make_request(url, params)

    def geocode(self, query: str, reverse: bool = False, proximity: tuple = None):
        """
        Performs forward or reverse geocoding.
        Query is an address string for forward geocoding, or (longitude, latitude) for reverse.
        Proximity is (longitude, latitude) to bias results.
        """
        if reverse:
            endpoint = f"geocoding/v5/mapbox.places/{query[0]},{query[1]}.json"
        else:
            endpoint = f"geocoding/v5/mapbox.places/{requests.utils.quote(query)}.json"
        
        url = self._build_url(endpoint)
        params = {}
        if proximity:
            params["proximity"] = f"{proximity[0]},{proximity[1]}"
        
        logger.info(f"Performing {'reverse' if reverse else 'forward'} geocoding for query: {query}")
        return self._make_request(url, params)

mapbox_service = MapboxService()
