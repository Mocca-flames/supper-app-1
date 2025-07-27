import redis
from ..config import settings

redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

class RedisService:
    @staticmethod
    def set_driver_location(driver_id: str, latitude: float, longitude: float):
        redis_client.hset(
            f"driver_location:{driver_id}",
            mapping={"lat": latitude, "lng": longitude}
        )
    
    @staticmethod
    def get_driver_location(driver_id: str):
        return redis_client.hgetall(f"driver_location:{driver_id}")
    
    @staticmethod
    def set_order_status(order_id: str, status: str):
        redis_client.set(f"order_status:{order_id}", status)
    
    @staticmethod
    def get_order_status(order_id: str):
        return redis_client.get(f"order_status:{order_id}")

    @staticmethod
    def set_route_cache(key: str, route_data: str, ttl: int = settings.CACHE_TTL_ROUTES):
        """Caches route data with a given TTL."""
        redis_client.setex(f"route_cache:{key}", ttl, route_data)

    @staticmethod
    def get_route_cache(key: str):
        """Retrieves cached route data."""
        return redis_client.get(f"route_cache:{key}")

    @staticmethod
    def set_geocoding_cache(key: str, geocoding_data: str, ttl: int = settings.CACHE_TTL_GEOCODING):
        """Caches geocoding results with a given TTL."""
        redis_client.setex(f"geocoding_cache:{key}", ttl, geocoding_data)

    @staticmethod
    def get_geocoding_cache(key: str):
        """Retrieves cached geocoding results."""
        return redis_client.get(f"geocoding_cache:{key}")
