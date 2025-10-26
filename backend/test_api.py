"""
Quick test script to verify the API is working correctly.
Run this after starting the server with: uvicorn main:app --reload
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

def print_section(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_health():
    """Test health check endpoint"""
    print_section("TEST 1: Health Check")

    response = requests.get(f"{BASE_URL}/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    print("✓ Health check passed!")

def test_get_all_lines():
    """Test getting all lines"""
    print_section("TEST 2: Get All Lines (Limited to 3)")

    response = requests.get(f"{BASE_URL}/get_all_lines?limit=3")
    print(f"Status Code: {response.status_code}")

    data = response.json()
    print(f"Number of lines returned: {len(data)}")

    if data:
        print(f"\nFirst line:")
        print(f"  Line ID: {data[0]['line_id']}")
        print(f"  Name: {data[0]['line_name']}")
        print(f"  Ampacity: {data[0]['ampacity']:.1f} A")
        print(f"  Utilization: {data[0]['utilization_pct']:.1f}%")
        print(f"  Status: {data[0]['status']}")

    assert response.status_code == 200
    assert len(data) == 3
    print("✓ Get all lines passed!")

def test_calculate_ampacity():
    """Test ampacity calculation"""
    print_section("TEST 3: Calculate Ampacity (Hot Day)")

    payload = {
        "line_id": "L0",
        "temp_ambient_c": 35,
        "wind_speed_ms": 1.5,
        "temp_conductor_max_c": 75
    }

    response = requests.post(f"{BASE_URL}/calculate_ampacity", json=payload)
    print(f"Status Code: {response.status_code}")

    data = response.json()
    print(f"\nLine: {data['line_name']}")
    print(f"Conductor: {data['conductor']}")
    print(f"Voltage: {data['voltage_kv']} kV")
    print(f"\nAmpacity: {data['ampacity']:.1f} A ({data['ampacity_mva']:.1f} MVA)")
    print(f"Static Rating: {data['static_rating_mva']:.1f} MVA")
    print(f"\nPredicted Load: {data['predicted_load_mw']:.1f} MW")
    print(f"Predicted Current: {data['predicted_current_a']:.1f} A")
    print(f"Utilization: {data['utilization_pct']:.1f}%")
    print(f"Status: {data['status']}")

    print(f"\nHeat Balance Details:")
    print(f"  Convective Cooling: {data['details']['Qc_convective']:.2f} W/m")
    print(f"  Radiative Cooling: {data['details']['Qr_radiative']:.2f} W/m")
    print(f"  Solar Heating: {data['details']['Qs_solar']:.2f} W/m")
    print(f"  Net Heat Capacity: {data['details']['Q_net']:.2f} W/m")

    assert response.status_code == 200
    assert data['ampacity'] > 0
    print("✓ Calculate ampacity passed!")

def test_predict_load():
    """Test load prediction"""
    print_section("TEST 4: Predict Load (Next 6 Hours)")

    payload = {
        "line_id": "L0",
        "hours_ahead": 6
    }

    response = requests.post(f"{BASE_URL}/predict_load", json=payload)
    print(f"Status Code: {response.status_code}")

    data = response.json()
    print(f"\nLine: {data['line_id']}")
    print(f"Predictions:\n")

    for pred in data['predictions']:
        ts = datetime.fromisoformat(pred['timestamp'])
        print(f"  {ts.strftime('%H:%M')} - {pred['predicted_load_mw']:.1f} MW ({pred['predicted_current_a']:.0f} A)")

    assert response.status_code == 200
    assert len(data['predictions']) == 6
    print("✓ Predict load passed!")

def test_lines_summary():
    """Test lines summary"""
    print_section("TEST 5: Lines Summary")

    response = requests.get(f"{BASE_URL}/lines/summary")
    print(f"Status Code: {response.status_code}")

    data = response.json()
    print(f"\nTotal Lines: {data['total_lines']}")
    print(f"Voltage Levels: {data['voltage_levels']}")
    print(f"Average Rating: {data['avg_rating_mva']:.1f} MVA")
    print(f"Max Rating: {data['max_rating_mva']:.1f} MVA")
    print(f"Min Rating: {data['min_rating_mva']:.1f} MVA")
    print(f"\nConductor Types:")
    for conductor in data['conductors'][:5]:
        print(f"  - {conductor}")

    assert response.status_code == 200
    assert data['total_lines'] > 0
    print("✓ Lines summary passed!")

def run_all_tests():
    """Run all API tests"""
    print("\n" + "="*60)
    print("  IEEE 738 DLR API - Test Suite")
    print("="*60)
    print(f"Testing server at: {BASE_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        test_health()
        test_get_all_lines()
        test_calculate_ampacity()
        test_predict_load()
        test_lines_summary()

        print("\n" + "="*60)
        print("  ALL TESTS PASSED! ✓")
        print("="*60)
        print("\nThe API is working correctly!")
        print("\nNext steps:")
        print("  1. Open http://localhost:8000/docs for interactive API docs")
        print("  2. Build the React frontend to visualize the data")
        print("  3. Start developing your dashboard!")

    except requests.exceptions.ConnectionError:
        print("\n✗ ERROR: Cannot connect to server!")
        print(f"Make sure the server is running at {BASE_URL}")
        print("Start it with: uvicorn main:app --reload")
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")

if __name__ == "__main__":
    run_all_tests()
