from decimal import Decimal
from typing import Dict, Any, Optional, List
import logging
import math
from datetime import datetime, timedelta
from ..schemas.order_schemas import OrderEstimateRequest, CostEstimationResponse, EstimateDetails

# Configure logger for PricingService
logger = logging.getLogger(__name__)

class PricingService:
    """Central service for managing pricing configuration and calculations"""

    # Default pricing presets - matches what's in admin_routes.py
    _PRICING_PRESETS = {
        "rush_hour": {"rate_per_km": Decimal("15.00"), "minimum_fare": Decimal("70.00")},
        "off_peak": {"rate_per_km": Decimal("8.00"), "minimum_fare": Decimal("40.00")},
        "weekend": {"rate_per_km": Decimal("12.00"), "minimum_fare": Decimal("60.00")},
        "standard": {"rate_per_km": Decimal("10.00"), "minimum_fare": Decimal("50.00")}
    }

    # Default to standard pricing
    _current_preset = "standard"

    @classmethod
    def get_current_pricing(cls) -> Dict[str, Decimal]:
        """Get the current pricing configuration"""
        preset = cls._PRICING_PRESETS.get(cls._current_preset)
        if not preset:
            logger.warning(f"Unknown pricing preset '{cls._current_preset}', using 'standard'")
            preset = cls._PRICING_PRESETS["standard"]

        return preset

    @classmethod
    def set_pricing_preset(cls, preset_name: str) -> None:
        """Set the current pricing preset"""
        if preset_name not in cls._PRICING_PRESETS:
            logger.warning(f"Attempt to set unknown pricing preset '{preset_name}'")
            return

        logger.info(f"Setting pricing preset to: {preset_name}")
        cls._current_preset = preset_name

    @classmethod
    def get_pricing_presets(cls) -> Dict[str, Any]:
        """Get all available pricing presets"""
        return cls._PRICING_PRESETS

    @classmethod
    def calculate_price(cls, distance_km: Decimal) -> Decimal:
        """Calculate price using current pricing configuration"""
        pricing = cls.get_current_pricing()
        rate_per_km = pricing["rate_per_km"]
        minimum_fare = pricing["minimum_fare"]

        calculated_price = distance_km * rate_per_km
        final_price = max(calculated_price, minimum_fare)

        logger.debug(f"Price calculation - Distance: {distance_km}km, Rate: R{rate_per_km}, "
                    f"Calculated: R{calculated_price}, Minimum: R{minimum_fare}, Final: R{final_price}")

        return final_price

    @classmethod
    def calculate_distance(cls, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates using Haversine formula"""
        # Convert to radians
        lat1_rad, lon1_rad = math.radians(lat1), math.radians(lon1)
        lat2_rad, lon2_rad = math.radians(lat2), math.radians(lon2)

        # Haversine formula
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

        # Earth's radius in kilometers
        R = 6371.0
        distance = R * c

        return distance

    @classmethod
    def estimate_order_cost(cls, request: OrderEstimateRequest) -> CostEstimationResponse:
        """Calculate comprehensive cost estimation for an order"""
        try:
            # Calculate distance
            distance_km = cls.calculate_distance(
                request.pickup_latitude, request.pickup_longitude,
                request.dropoff_latitude, request.dropoff_longitude
            )

            # Get base pricing
            pricing = cls.get_current_pricing()
            rate_per_km = pricing["rate_per_km"]
            minimum_fare = pricing["minimum_fare"]

            # Calculate base fare
            base_fare = float(minimum_fare)  # Base fare is the minimum fare
            distance_fare = float(Decimal(str(distance_km)) * rate_per_km)

            # Service-specific calculations
            service_fee = 5.0  # Base service fee
            surge_multiplier = 1.0  # Default no surge
            medical_surcharge = 0.0
            package_surcharge = 0.0
            delivery_fee = 0.0

            # Apply service-specific surcharges
            if request.service_type == "medical_transport":
                medical_surcharge = 15.0
                if request.mobility_needs:
                    medical_surcharge += len(request.mobility_needs) * 5.0
            elif request.service_type in ["food_delivery", "product_delivery"]:
                delivery_fee = 8.0
                if request.package_size == "large":
                    package_surcharge = 10.0
                elif request.package_size == "medium":
                    package_surcharge = 5.0

            # Calculate total
            subtotal = base_fare + distance_fare + service_fee + medical_surcharge + package_surcharge + delivery_fee
            total = subtotal * surge_multiplier

            # Estimate duration (rough calculation: 30 km/h average speed + 5 min pickup/dropoff)
            estimated_duration_minutes = int((distance_km / 30.0) * 60) + 10

            # Create estimate details
            estimate_details = EstimateDetails(
                base_fare=round(base_fare, 2),
                distance_fare=round(distance_fare, 2),
                service_fee=round(service_fee, 2),
                total=round(total, 2),
                estimated_duration_minutes=estimated_duration_minutes,
                currency="ZAR",
                surge_multiplier=surge_multiplier,
                medical_surcharge=round(medical_surcharge, 2),
                package_surcharge=round(package_surcharge, 2),
                delivery_fee=round(delivery_fee, 2)
            )

            # Valid for 10 minutes
            valid_until = (datetime.utcnow() + timedelta(minutes=10)).isoformat() + "Z"

            return CostEstimationResponse(
                estimate=estimate_details,
                valid_until=valid_until
            )

        except Exception as e:
            logger.error(f"Error calculating order estimate: {str(e)}")
            raise ValueError(f"Failed to calculate order estimate: {str(e)}")