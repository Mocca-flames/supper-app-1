import requests
import os
from dotenv import load_dotenv

load_dotenv()

def validate_mapbox_token():
    token = os.getenv('MAPBOX_ACCESS_TOKEN')
    
    if not token:
        print("❌ MAPBOX_ACCESS_TOKEN not found in environment")
        return False
    
    # Test with a simple geocoding request
    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/paris.json"
    params = {'access_token': token, 'limit': 1}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            print("✅ MapBox token is valid and working")
            print(f"Token scopes appear to include geocoding")
            return True
        elif response.status_code == 401:
            print("❌ MapBox token is invalid or expired")
            return False
        else:
            print(f"⚠️ Unexpected response: {response.status_code}")
            print(response.text)
            return False
    except requests.RequestException as e:
        print(f"❌ Network error: {e}")
        return False

if __name__ == "__main__":
    validate_mapbox_token()