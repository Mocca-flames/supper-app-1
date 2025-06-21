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
