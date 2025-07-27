from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Optional

from ..services.location_service import LocationService
from ..auth.middleware import get_current_user # Assuming authentication is needed for these endpoints
from ..schemas.user_schemas import UserResponse # Assuming UserResponse is the schema for current_user

router = APIRouter(
    prefix="/geocode",
    tags=["Geocoding & Location"]
)

@router.post("/forward", response_model=Optional[Dict])
def forward_geocode(
    address: str = Query(..., description="Address to convert to coordinates"),
    current_user: UserResponse = Depends(get_current_user) # Protect endpoint
):
    """
    Converts a human-readable address into geographic coordinates (latitude, longitude).
    """
    try:
        coords = LocationService.geocode_address(address)
        if not coords:
            raise HTTPException(status_code=404, detail="Address not found or could not be geocoded.")
        return coords
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

@router.post("/reverse", response_model=Optional[Dict])
def reverse_geocode(
    latitude: float = Query(..., description="Latitude of the location"),
    longitude: float = Query(..., description="Longitude of the location"),
    current_user: UserResponse = Depends(get_current_user) # Protect endpoint
):
    """
    Converts geographic coordinates (latitude, longitude) into a human-readable address.
    """
    try:
        address_info = LocationService.reverse_geocode_coordinates(longitude, latitude)
        if not address_info:
            raise HTTPException(status_code=404, detail="Coordinates could not be reverse geocoded to an address.")
        return address_info
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

@router.get("/autocomplete", response_model=List[Dict])
def get_autocomplete_suggestions(
    query: str = Query(..., description="Partial address query for autocomplete suggestions"),
    current_user: UserResponse = Depends(get_current_user) # Protect endpoint
):
    """
    Provides address autocomplete suggestions based on a partial query.
    """
    try:
        suggestions = LocationService.get_address_autocomplete_suggestions(query)
        return suggestions
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

@router.get("/service-area-check", response_model=bool)
def check_service_area(
    latitude: float = Query(..., description="Latitude of the location to check"),
    longitude: float = Query(..., description="Longitude of the location to check"),
    current_user: UserResponse = Depends(get_current_user) # Protect endpoint
):
    """
    Checks if a given coordinate falls within the defined service area.
    """
    try:
        is_within = LocationService.is_within_service_area(latitude, longitude)
        return is_within
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

@router.post("/bulk-geocode", response_model=Dict[str, Optional[Dict]])
def bulk_geocode_addresses_endpoint(
    addresses: List[str],
    current_user: UserResponse = Depends(get_current_user) # Protect endpoint
):
    """
    Performs bulk geocoding for a list of addresses.
    """
    try:
        results = LocationService.bulk_geocode_addresses(addresses)
        return results
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")
