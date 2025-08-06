#!/usr/bin/env python3
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_order():
    order_data = {
        "client_id": "some_client_id",
        "order_type": "RIDE",
        "pickup_address": "Pickup Address",
        "dropoff_address": "Dropoff Address",
        "pickup_latitude": 37.7749,
        "pickup_longitude": -122.4194,
        "dropoff_latitude": 37.7859,
        "dropoff_longitude": -122.4364,
        "special_instructions": "Some instructions",
        "patient_details": None,
        "medical_items": None
    }
    
    response = client.post("/api/client/orders", json=order_data)
    assert response.status_code == 201
"""
Enhanced test script for GET /api/orders/ endpoint with Firebase authentication
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional

class OrdersAPITester:
    def __init__(self, base_url: str = "http://localhost:8000", firebase_token: str = None):
        """
        Initialize the API tester
        
        Args:
            base_url: Base URL of the API (default: http://localhost:8000)
            firebase_token: Firebase authentication token
        """
        self.base_url = base_url.rstrip('/')
        self.firebase_token = firebase_token
        self.session = requests.Session()
        
        # Set up default headers
        if self.firebase_token:
            self.session.headers.update({
                "Authorization": f"Bearer {self.firebase_token}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            })
    
    def test_orders_endpoint(self, endpoint: str = "/api/client/orders/") -> Dict[str, Any]:
        """
        Test the orders endpoint with comprehensive validation
        
        Args:
            endpoint: API endpoint to test (default: /api/client/orders/)
            
        Returns:
            Dictionary containing test results
        """
        url = f"{self.base_url}{endpoint}"
        test_result = {
            "timestamp": datetime.now().isoformat(),
            "url": url,
            "method": "GET",
            "success": False,
            "status_code": None,
            "response_time_ms": None,
            "response_size_bytes": None,
            "headers": {},
            "data": None,
            "error": None
        }
        
        try:
            print(f"🔍 Testing endpoint: {url}")
            print(f"🔐 Using token: {self.firebase_token[:20]}..." if self.firebase_token else "❌ No token provided")
            
            start_time = time.time()
            response = self.session.get(url, timeout=30)
            end_time = time.time()
            
            # Calculate response time
            response_time_ms = round((end_time - start_time) * 1000, 2)
            
            # Update test result
            test_result.update({
                "status_code": response.status_code,
                "response_time_ms": response_time_ms,
                "response_size_bytes": len(response.content),
                "headers": dict(response.headers),
                "success": response.status_code < 400
            })
            
            # Try to parse JSON response
            try:
                test_result["data"] = response.json()
            except json.JSONDecodeError:
                test_result["data"] = response.text
            
            # Print results
            self._print_response_summary(test_result)
            
            # Validate response based on status code
            if response.status_code == 200:
                self._validate_success_response(test_result)
            elif response.status_code == 401:
                print("❌ Authentication failed - check your Firebase token")
            elif response.status_code == 403:
                print("❌ Access forbidden - token may not have required permissions")
            elif response.status_code == 404:
                print("❌ Endpoint not found - check the URL")
            elif response.status_code >= 500:
                print(f"❌ Server error ({response.status_code}) - check server logs")
            else:
                print(f"⚠️  Unexpected status code: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            test_result["error"] = "Connection failed - is the server running?"
            print(f"❌ {test_result['error']}")
        except requests.exceptions.Timeout:
            test_result["error"] = "Request timed out"
            print(f"❌ {test_result['error']}")
        except requests.exceptions.RequestException as e:
            test_result["error"] = f"Request failed: {str(e)}"
            print(f"❌ {test_result['error']}")
        except Exception as e:
            test_result["error"] = f"Unexpected error: {str(e)}"
            print(f"❌ {test_result['error']}")
        
        return test_result
    
    def _print_response_summary(self, result: Dict[str, Any]) -> None:
        """Print a formatted summary of the response"""
        status = result["status_code"]
        time_ms = result["response_time_ms"]
        size_bytes = result["response_size_bytes"]
        
        # Status icon
        if status == 200:
            status_icon = "✅"
        elif status in [401, 403]:
            status_icon = "🔒"
        elif status >= 400:
            status_icon = "❌"
        else:
            status_icon = "⚠️"
        
        print(f"\n{status_icon} Response Summary:")
        print(f"   Status: {status}")
        print(f"   Time: {time_ms}ms")
        print(f"   Size: {size_bytes} bytes")
        
        # Print response headers (important ones)
        important_headers = ['content-type', 'content-length', 'server', 'date']
        headers = result.get("headers", {})
        for header in important_headers:
            if header in headers:
                print(f"   {header.title()}: {headers[header]}")
    
    def _validate_success_response(self, result: Dict[str, Any]) -> None:
        """Validate the structure of a successful response"""
        data = result.get("data")
        
        if data is None:
            print("⚠️  Warning: No response data received")
            return
        
        if isinstance(data, dict):
            print(f"📊 Response contains {len(data)} fields")
            if "orders" in data:
                orders = data["orders"]
                if isinstance(orders, list):
                    print(f"📦 Found {len(orders)} orders")
                    if orders:
                        self._validate_order_structure(orders[0])
                else:
                    print("⚠️  'orders' field is not a list")
        elif isinstance(data, list):
            print(f"📦 Response contains {len(data)} orders")
            if data:
                self._validate_order_structure(data[0])
        else:
            print(f"⚠️  Unexpected response type: {type(data)}")
    
    def _validate_order_structure(self, order: Dict[str, Any]) -> None:
        """Validate the structure of a single order"""
        expected_fields = ['id', 'user_id', 'status', 'created_at', 'total']
        present_fields = [field for field in expected_fields if field in order]
        missing_fields = [field for field in expected_fields if field not in order]
        
        print(f"🔍 Order validation:")
        print(f"   Present fields: {present_fields}")
        if missing_fields:
            print(f"   Missing fields: {missing_fields}")
        
        # Show first order sample
        print(f"📋 Sample order (first 3 fields):")
        for i, (key, value) in enumerate(order.items()):
            if i >= 3:  # Limit output
                break
            print(f"   {key}: {value}")
    
    def test_multiple_scenarios(self) -> None:
        """Run multiple test scenarios"""
        print("🚀 Starting comprehensive API tests...\n")
        
        scenarios = [
            ("/api/client/orders/", "Main orders endpoint"),
            ("/api/client/orders", "Orders endpoint without trailing slash"),
        ]
        
        results = []
        for endpoint, description in scenarios:
            print(f"\n{'='*50}")
            print(f"Testing: {description}")
            print('='*50)
            result = self.test_orders_endpoint(endpoint)
            results.append((description, result))
        
        # Summary
        print(f"\n{'='*50}")
        print("TEST SUMMARY")
        print('='*50)
        for description, result in results:
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            print(f"{status} {description} - Status: {result['status_code']}")
    
    def save_results(self, result: Dict[str, Any], filename: str = None) -> None:
        """Save test results to a JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"orders_api_test_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            print(f"💾 Results saved to: {filename}")
        except Exception as e:
            print(f"❌ Failed to save results: {e}")


def main():
    """Main function to run the tests"""
    # Configuration
    BASE_URL = "http://localhost:8000"
    FIREBASE_TOKEN = "uSzR7yypwZhWVsfRQLCKnWgTlND2"  # Replace with your actual token
    
    print("🔥 Firebase Orders API Tester")
    print("="*40)
    
    # Initialize tester
    tester = OrdersAPITester(BASE_URL, FIREBASE_TOKEN)
    
    # Run comprehensive tests
    tester.test_multiple_scenarios()
    
    # Optional: Test with invalid token
    print(f"\n{'='*50}")
    print("Testing with invalid token")
    print('='*50)
    invalid_tester = OrdersAPITester(BASE_URL, "invalid_token_123")
    invalid_result = invalid_tester.test_orders_endpoint()
    
    print("\n🏁 Testing completed!")


if __name__ == "__main__":
    main()
