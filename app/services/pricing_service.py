from decimal import Decimal
from typing import Dict, Any
import logging

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