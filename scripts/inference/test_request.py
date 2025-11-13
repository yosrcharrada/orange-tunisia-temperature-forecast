"""
Test script for LSTM Temperature Forecast API.
Sends a sample request to the local API server.
"""
import json
import random
import sys

import requests


def generate_sample_temps(length: int = 168, base_temp: float = 20.0) -> list:
    """
    Generate synthetic temperature data for testing.
    
    Args:
        length: Number of temperature values to generate
        base_temp: Base temperature around which to vary
        
    Returns:
        List of synthetic temperature values
    """
    temps = []
    for i in range(length):
        # Add some daily and random variation
        hour_of_day = i % 24
        daily_variation = 5 * (hour_of_day - 12) / 12  # ±5°C daily swing
        random_noise = random.uniform(-2, 2)
        temp = base_temp + daily_variation + random_noise
        temps.append(round(temp, 2))
    return temps


def test_health_endpoint(base_url: str = "http://localhost:8000"):
    """Test the health check endpoint."""
    print("Testing /health endpoint...")
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        response.raise_for_status()
        data = response.json()
        print(f"✓ Health check passed: {json.dumps(data, indent=2)}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"✗ Health check failed: {e}")
        return False


def test_forecast_endpoint(
    base_url: str = "http://localhost:8000",
    steps: int = 24
):
    """Test the forecast endpoint."""
    print(f"\nTesting /forecast endpoint (steps={steps})...")
    
    # Generate sample data
    sample_temps = generate_sample_temps(168)
    
    payload = {
        "recent_temps": sample_temps,
        "steps": steps
    }
    
    print(f"Sending request with {len(sample_temps)} temperature values...")
    
    try:
        response = requests.post(
            f"{base_url}/forecast",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        print(f"✓ Forecast successful!")
        print(f"  - Received {len(data['forecasts'])} forecasts")
        print(f"  - Sequence length used: {data['sequence_length']}")
        print(f"  - First 5 forecasts: {data['forecasts'][:5]}")
        print(f"  - Last 5 forecasts: {data['forecasts'][-5:]}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"✗ Forecast failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                print(f"  Error details: {json.dumps(error_detail, indent=2)}")
            except:
                print(f"  Response text: {e.response.text}")
        return False


def test_root_endpoint(base_url: str = "http://localhost:8000"):
    """Test the root endpoint."""
    print("\nTesting / (root) endpoint...")
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        response.raise_for_status()
        data = response.json()
        print(f"✓ Root endpoint response:")
        print(json.dumps(data, indent=2))
        return True
    except requests.exceptions.RequestException as e:
        print(f"✗ Root endpoint failed: {e}")
        return False


def test_invalid_input(base_url: str = "http://localhost:8000"):
    """Test error handling with invalid input."""
    print("\nTesting error handling with insufficient data...")
    
    payload = {
        "recent_temps": [20.0] * 50,  # Only 50 values (need 168)
        "steps": 24
    }
    
    try:
        response = requests.post(
            f"{base_url}/forecast",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        if response.status_code == 400:
            print(f"✓ Correctly rejected invalid input (HTTP {response.status_code})")
            error = response.json()
            print(f"  Error message: {error.get('detail', 'N/A')}")
            return True
        else:
            print(f"✗ Expected HTTP 400, got {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"✗ Test failed unexpectedly: {e}")
        return False


def main():
    """Run all tests."""
    base_url = "http://localhost:8000"
    
    print("="*60)
    print("LSTM Temperature Forecast API - Test Suite")
    print("="*60)
    print(f"Testing API at: {base_url}")
    print()
    
    results = []
    
    # Test health endpoint
    results.append(("Health Check", test_health_endpoint(base_url)))
    
    # Test root endpoint
    results.append(("Root Endpoint", test_root_endpoint(base_url)))
    
    # Test forecast with 24 hours
    results.append(("Forecast (24h)", test_forecast_endpoint(base_url, steps=24)))
    
    # Test forecast with 168 hours (1 week)
    results.append(("Forecast (168h)", test_forecast_endpoint(base_url, steps=168)))
    
    # Test error handling
    results.append(("Error Handling", test_invalid_input(base_url)))
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name:20s}: {status}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print("="*60)
    
    # Exit with appropriate code
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
