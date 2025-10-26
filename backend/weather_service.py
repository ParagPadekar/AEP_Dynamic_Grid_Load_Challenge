"""
Weather Service Module
Integrates with weather APIs and provides pre-defined scenarios for demos
"""

import os
import requests
from datetime import datetime
from typing import Dict, Optional, Literal
from pydantic import BaseModel


class WeatherData(BaseModel):
    """Weather data model"""
    temperature_c: float
    wind_speed_ms: float
    solar_altitude: float
    wind_angle_deg: float
    humidity_pct: float
    timestamp: str
    source: str  # "openweather", "scenario", "manual"
    location: Optional[str] = None
    description: Optional[str] = None
    hour_of_day: Optional[int] = None  # For time-of-day load profiles (0-23)


class WeatherService:
    """
    Provides weather data from multiple sources:
    1. Live API (OpenWeatherMap)
    2. Pre-defined scenarios (for demos)
    3. Manual input
    """

    # Free OpenWeatherMap API (no credit card required!)
    # Sign up at: https://openweathermap.org/api
    OPENWEATHER_API_URL = "https://api.openweathermap.org/data/2.5/weather"

    # Hawaii coordinates (Honolulu area - center of the 40-bus system)
    DEFAULT_LOCATION = {
        "lat": 21.3099,  # Honolulu latitude
        "lon": -157.8581  # Honolulu longitude
    }

    # Pre-defined demo scenarios organized by severity and time
    SCENARIOS = {
        # CRITICAL SCENARIOS - Worst case overloads
        "critical_evening": {
            "name": "🔥 CRITICAL: Heat Wave Evening Peak (6 PM)",
            "description": "WORST CASE: 44°C heat + 110% load = Cascading failures",
            "temperature_c": 44.0,
            "wind_speed_ms": 0.5,
            "solar_altitude": 15.0,
            "wind_angle_deg": 90,
            "humidity_pct": 70,
            "hour_of_day": 18
        },
        "critical_afternoon": {
            "name": "🔥 CRITICAL: Heat Wave Afternoon (3 PM)",
            "description": "Peak sun + high heat + rising load = Major overloads",
            "temperature_c": 44.0,
            "wind_speed_ms": 0.5,
            "solar_altitude": 70.0,
            "wind_angle_deg": 90,
            "humidity_pct": 65,
            "hour_of_day": 15
        },

        # WARNING SCENARIOS - High stress conditions
        "warning_midday": {
            "name": "⚠️ WARNING: Hot Summer Midday (12 PM)",
            "description": "35°C, moderate load, some lines approaching limits",
            "temperature_c": 35.0,
            "wind_speed_ms": 1.5,
            "solar_altitude": 75.0,
            "wind_angle_deg": 90,
            "humidity_pct": 70,
            "hour_of_day": 12
        },
        "warning_evening": {
            "name": "⚠️ WARNING: Hot Evening (6 PM)",
            "description": "Still hot + evening peak load = Watch closely",
            "temperature_c": 36.0,
            "wind_speed_ms": 1.0,
            "solar_altitude": 15.0,
            "wind_angle_deg": 90,
            "humidity_pct": 75,
            "hour_of_day": 18
        },

        # NORMAL SCENARIOS - Typical operating conditions
        "normal_midday": {
            "name": "✅ NORMAL: Summer Midday (12 PM)",
            "description": "30°C, normal breeze, all lines within limits",
            "temperature_c": 30.0,
            "wind_speed_ms": 2.5,
            "solar_altitude": 75.0,
            "wind_angle_deg": 90,
            "humidity_pct": 75,
            "hour_of_day": 12
        },
        "normal_morning": {
            "name": "✅ NORMAL: Morning Ramp (9 AM)",
            "description": "Comfortable morning, load increasing gradually",
            "temperature_c": 27.0,
            "wind_speed_ms": 2.0,
            "solar_altitude": 45.0,
            "wind_angle_deg": 90,
            "humidity_pct": 78,
            "hour_of_day": 9
        },

        # OPTIMAL SCENARIOS - Best conditions
        "optimal_early": {
            "name": "😎 OPTIMAL: Early Morning (6 AM)",
            "description": "Minimum load (90%), cool temps - Best for maintenance",
            "temperature_c": 24.0,
            "wind_speed_ms": 2.0,
            "solar_altitude": 5.0,
            "wind_angle_deg": 90,
            "humidity_pct": 80,
            "hour_of_day": 6
        },
        "optimal_night": {
            "name": "😎 OPTIMAL: Late Night (2 AM)",
            "description": "Coolest temps + lowest load - Maximum capacity margin",
            "temperature_c": 22.0,
            "wind_speed_ms": 2.5,
            "solar_altitude": 0.0,
            "wind_angle_deg": 90,
            "humidity_pct": 85,
            "hour_of_day": 2
        },
        "optimal_windy": {
            "name": "😎 OPTIMAL: Windy Conditions",
            "description": "Strong trade winds provide excellent conductor cooling",
            "temperature_c": 28.0,
            "wind_speed_ms": 5.5,
            "solar_altitude": 50.0,
            "wind_angle_deg": 90,
            "humidity_pct": 65,
            "hour_of_day": 14
        }
    }

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize weather service.

        Args:
            api_key: OpenWeatherMap API key (optional, can use env var)
        """
        self.api_key = api_key or os.getenv("OPENWEATHER_API_KEY")

    def get_weather_live(
        self,
        lat: Optional[float] = None,
        lon: Optional[float] = None
    ) -> WeatherData:
        """
        Fetch live weather data from OpenWeatherMap API.

        Args:
            lat: Latitude (default: Honolulu)
            lon: Longitude (default: Honolulu)

        Returns:
            WeatherData object with current conditions
        """
        if not self.api_key:
            raise ValueError(
                "OpenWeatherMap API key not found. "
                "Set OPENWEATHER_API_KEY environment variable or pass to constructor. "
                "Get free key at: https://openweathermap.org/api"
            )

        # Use default Hawaii location if not specified
        lat = lat or self.DEFAULT_LOCATION["lat"]
        lon = lon or self.DEFAULT_LOCATION["lon"]

        # Make API request
        params = {
            "lat": lat,
            "lon": lon,
            "appid": self.api_key,
            "units": "metric"  # Celsius
        }

        try:
            response = requests.get(self.OPENWEATHER_API_URL, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()

            # Extract weather parameters
            temperature_c = data["main"]["temp"]
            wind_speed_ms = data["wind"]["speed"]
            humidity_pct = data["main"]["humidity"]
            wind_deg = data["wind"].get("deg", 0)

            # Calculate solar altitude based on time and location
            solar_altitude = self._calculate_solar_altitude(lat, lon)

            # Convert wind direction to angle relative to conductors
            # Assuming most lines run E-W (typical), perpendicular wind is best
            wind_angle_deg = abs(wind_deg - 90) if wind_deg <= 180 else abs(wind_deg - 270)

            return WeatherData(
                temperature_c=temperature_c,
                wind_speed_ms=wind_speed_ms,
                solar_altitude=solar_altitude,
                wind_angle_deg=min(wind_angle_deg, 90),  # Cap at 90° (perpendicular)
                humidity_pct=humidity_pct,
                timestamp=datetime.now().isoformat(),
                source="openweather",
                location=data.get("name", "Hawaii"),
                description=data["weather"][0]["description"] if data.get("weather") else None
            )

        except requests.RequestException as e:
            raise RuntimeError(f"Failed to fetch weather data: {e}")

    def get_weather_scenario(self, scenario_name: str) -> WeatherData:
        """
        Get pre-defined weather scenario for demos.

        Args:
            scenario_name: One of the SCENARIOS keys

        Returns:
            WeatherData object with scenario conditions
        """
        if scenario_name not in self.SCENARIOS:
            available = ", ".join(self.SCENARIOS.keys())
            raise ValueError(
                f"Unknown scenario: {scenario_name}. "
                f"Available scenarios: {available}"
            )

        scenario = self.SCENARIOS[scenario_name]

        return WeatherData(
            temperature_c=scenario["temperature_c"],
            wind_speed_ms=scenario["wind_speed_ms"],
            solar_altitude=scenario["solar_altitude"],
            wind_angle_deg=scenario["wind_angle_deg"],
            humidity_pct=scenario["humidity_pct"],
            timestamp=datetime.now().isoformat(),
            source=f"scenario:{scenario_name}",
            location="Demo Scenario",
            description=scenario["description"]
        )

    def get_weather_manual(
        self,
        temperature_c: float,
        wind_speed_ms: float,
        solar_altitude: float = 45.0,
        wind_angle_deg: float = 90.0,
        humidity_pct: float = 70.0
    ) -> WeatherData:
        """
        Create weather data from manual inputs.

        Args:
            temperature_c: Ambient temperature (°C)
            wind_speed_ms: Wind speed (m/s)
            solar_altitude: Solar altitude angle (degrees)
            wind_angle_deg: Wind angle relative to conductor (degrees)
            humidity_pct: Relative humidity (%)

        Returns:
            WeatherData object with manual inputs
        """
        return WeatherData(
            temperature_c=temperature_c,
            wind_speed_ms=wind_speed_ms,
            solar_altitude=solar_altitude,
            wind_angle_deg=wind_angle_deg,
            humidity_pct=humidity_pct,
            timestamp=datetime.now().isoformat(),
            source="manual",
            location="Manual Input",
            description="User-specified conditions"
        )

    def _calculate_solar_altitude(self, lat: float, lon: float) -> float:
        """
        Calculate approximate solar altitude angle.

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            Solar altitude angle in degrees (0-90)
        """
        import math

        now = datetime.utcnow()

        # Day of year
        day_of_year = now.timetuple().tm_yday

        # Solar declination (simplified)
        declination = 23.45 * math.sin(math.radians((360/365) * (day_of_year - 81)))

        # Hour angle (simplified - assumes solar noon at 12:00 UTC + lon/15)
        solar_noon = 12.0 - lon / 15.0
        hour = now.hour + now.minute / 60.0
        hour_angle = 15.0 * (hour - solar_noon)

        # Solar altitude (simplified formula)
        lat_rad = math.radians(lat)
        dec_rad = math.radians(declination)
        hour_rad = math.radians(hour_angle)

        sin_altitude = (
            math.sin(lat_rad) * math.sin(dec_rad) +
            math.cos(lat_rad) * math.cos(dec_rad) * math.cos(hour_rad)
        )

        altitude = math.degrees(math.asin(max(-1, min(1, sin_altitude))))

        # Return 0 if sun is below horizon
        return max(0, altitude)

    def list_scenarios(self) -> Dict[str, Dict]:
        """
        List all available pre-defined scenarios.

        Returns:
            Dictionary of scenario names and their descriptions
        """
        return {
            name: {
                "name": scenario["name"],
                "description": scenario["description"],
                "temperature_c": scenario["temperature_c"],
                "wind_speed_ms": scenario["wind_speed_ms"]
            }
            for name, scenario in self.SCENARIOS.items()
        }


# Example usage and testing
if __name__ == "__main__":
    print("="*60)
    print("Weather Service Demo")
    print("="*60)

    service = WeatherService()

    # Test scenarios
    print("\n1. Available Scenarios:")
    print("-" * 60)
    scenarios = service.list_scenarios()
    for key, info in scenarios.items():
        print(f"\n{key}:")
        print(f"  {info['name']}")
        print(f"  {info['description']}")
        print(f"  Temp: {info['temperature_c']}°C, Wind: {info['wind_speed_ms']} m/s")

    # Test scenario weather
    print("\n\n2. Extreme Heat Scenario:")
    print("-" * 60)
    extreme = service.get_weather_scenario("extreme_heat")
    print(f"Temperature: {extreme.temperature_c}°C")
    print(f"Wind Speed: {extreme.wind_speed_ms} m/s")
    print(f"Solar Altitude: {extreme.solar_altitude}°")
    print(f"Description: {extreme.description}")

    # Test manual weather
    print("\n\n3. Manual Weather Input:")
    print("-" * 60)
    manual = service.get_weather_manual(
        temperature_c=32.0,
        wind_speed_ms=2.5
    )
    print(f"Temperature: {manual.temperature_c}°C")
    print(f"Wind Speed: {manual.wind_speed_ms} m/s")
    print(f"Source: {manual.source}")

    # Test live weather (if API key available)
    print("\n\n4. Live Weather (requires API key):")
    print("-" * 60)
    if service.api_key:
        try:
            live = service.get_weather_live()
            print(f"Location: {live.location}")
            print(f"Temperature: {live.temperature_c}°C")
            print(f"Wind Speed: {live.wind_speed_ms} m/s")
            print(f"Conditions: {live.description}")
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("No API key found. Set OPENWEATHER_API_KEY to test live weather.")
        print("Get free key at: https://openweathermap.org/api")
