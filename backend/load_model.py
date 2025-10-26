"""
Load Prediction Module
Implements simple rule-based and time-based load forecasting
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Optional


class LoadPredictor:
    """
    Simple load predictor using time-of-day patterns and baseline loads.

    For hackathon purposes, implements:
    1. Time-of-day load profiles (daily patterns)
    2. Baseline load scaling
    3. Random variability
    """

    def __init__(self, baseline_loads: Optional[Dict[str, float]] = None):
        """
        Initialize load predictor.

        Args:
            baseline_loads: Dictionary mapping line_id -> baseline load (MW)
        """
        self.baseline_loads = baseline_loads or {}

        # Typical daily load profile (percentage of peak)
        # Hour 0-23 -> load factor (0.0 to 1.0)
        self.hourly_profile = self._create_daily_profile()

    def _create_daily_profile(self):
        """
        Create typical 24-hour load profile for power systems.

        Based on real utility load curves from Hawaii 40-bus PyPSA model
        and EIA government data (https://www.eia.gov/todayinenergy/detail.php?id=42915)

        Uses sine wave approximation with:
        - Minimum at 6 AM: 90% of nominal (early morning low)
        - Maximum at 6 PM: 110% of nominal (evening peak - residential A/C + cooking)
        - Values normalized so baseline power flows represent typical midday conditions

        This is realistic for Hawaii which has strong evening residential peaks.
        Formula: load_factor = 0.1 * sin(2π * (hour/24) + π/2) + 1.0
        """
        # Real data from pypsa_load_scale.ipynb - sine wave approximation
        # of actual utility load patterns for Hawaii grid
        hourly_factors = [
            1.0,    # 00:00 - Midnight
            0.974,  # 01:00
            0.95,   # 02:00
            0.929,  # 03:00
            0.913,  # 04:00
            0.903,  # 05:00
            0.9,    # 06:00 - Morning minimum (90%)
            0.903,  # 07:00 - Start of morning ramp
            0.913,  # 08:00
            0.929,  # 09:00
            0.95,   # 10:00
            0.974,  # 11:00
            1.0,    # 12:00 - Noon (nominal)
            1.026,  # 13:00
            1.05,   # 14:00
            1.071,  # 15:00
            1.087,  # 16:00
            1.097,  # 17:00
            1.1,    # 18:00 - Evening peak maximum (110%)
            1.097,  # 19:00
            1.087,  # 20:00
            1.071,  # 21:00
            1.05,   # 22:00
            1.026,  # 23:00
        ]

        # Convert to dictionary for backward compatibility
        profile = {hour: factor for hour, factor in enumerate(hourly_factors)}
        return profile

    def set_baseline_load(self, line_id: str, load_mw: float):
        """Set baseline load for a line."""
        self.baseline_loads[line_id] = load_mw

    def predict_load(
        self,
        line_id: str,
        timestamp: Optional[datetime] = None,
        add_variability: bool = False,
        temperature_c: Optional[float] = None,
        wind_speed_ms: Optional[float] = None,
        solar_altitude: Optional[float] = None,
        humidity_pct: Optional[float] = None
    ) -> float:
        """
        Predict load for a specific line at given timestamp with weather sensitivity.

        Args:
            line_id: Line identifier
            timestamp: Datetime for prediction (default: now)
            add_variability: Add random variability (default: True)
            temperature_c: Ambient temperature in Celsius (affects cooling/heating load)
            wind_speed_ms: Wind speed in m/s (affects perceived temperature)
            solar_altitude: Solar altitude in degrees (affects cooling load)
            humidity_pct: Relative humidity percentage (affects perceived temperature)

        Returns:
            Predicted load in MW
        """
        if timestamp is None:
            timestamp = datetime.now()

        # Get baseline load for this line
        baseline = self.baseline_loads.get(line_id, 50.0)  # Default 50 MW

        # Get hour of day
        hour = timestamp.hour

        # Apply time-of-day profile
        load_factor = self.hourly_profile.get(hour, 0.8)
        predicted_load = baseline * load_factor

        # Apply weather-dependent load adjustments
        weather_factor = 1.0

        if temperature_c is not None:
            # Temperature effect on load (cooling/heating demand)
            # Reference temperature: 22°C (comfortable, minimal HVAC)
            temp_reference = 22.0

            if temperature_c > temp_reference:
                # Hot weather: cooling load increases exponentially
                # Each degree above 22°C adds ~2.5-3% load (A/C demand)
                temp_diff = temperature_c - temp_reference

                # Apply exponential scaling for extreme heat
                if temp_diff > 15:  # Above 37°C
                    cooling_factor = 1.0 + (temp_diff * 0.035)  # 3.5% per degree for extreme heat
                else:
                    cooling_factor = 1.0 + (temp_diff * 0.025)  # 2.5% per degree

                weather_factor *= cooling_factor

                # Humidity amplifies cooling load (higher humidity = feels hotter)
                if humidity_pct is not None and humidity_pct > 60:
                    humidity_factor = 1.0 + ((humidity_pct - 60) * 0.002)  # 0.2% per % above 60%
                    weather_factor *= humidity_factor

                # Solar radiation during daytime increases cooling load
                if solar_altitude is not None and solar_altitude > 0:
                    solar_factor = 1.0 + (solar_altitude / 180.0 * 0.10)  # Up to 10% more load at solar noon
                    weather_factor *= solar_factor

            elif temperature_c < 15.0:
                # Cold weather: heating load increases
                # Each degree below 15°C adds ~1.5-2% load
                temp_diff = 15.0 - temperature_c
                heating_factor = 1.0 + (temp_diff * 0.018)  # 1.8% per degree
                weather_factor *= heating_factor

            # Wind chill effect in cold weather
            if wind_speed_ms is not None and temperature_c < 10.0 and wind_speed_ms > 2.0:
                # Wind makes it feel colder, increasing heating demand
                wind_chill_factor = 1.0 + (wind_speed_ms * 0.01)  # 1% per m/s
                weather_factor *= wind_chill_factor

        # Apply weather factor to load
        predicted_load *= weather_factor

        # Add random variability (±5%)
        if add_variability:
            variability = np.random.uniform(-0.05, 0.05)
            predicted_load *= (1 + variability)

        return max(predicted_load, 0.0)

    def predict_load_series(
        self,
        line_id: str,
        start_time: datetime,
        hours: int = 24
    ) -> pd.DataFrame:
        """
        Predict load time series for multiple hours.

        Args:
            line_id: Line identifier
            start_time: Start datetime
            hours: Number of hours to predict

        Returns:
            DataFrame with columns: timestamp, predicted_load_mw
        """
        timestamps = [start_time + timedelta(hours=h) for h in range(hours)]
        loads = [
            self.predict_load(line_id, ts, add_variability=False)
            for ts in timestamps
        ]

        return pd.DataFrame({
            'timestamp': timestamps,
            'predicted_load_mw': loads,
            'hour': [ts.hour for ts in timestamps],
        })

    def calculate_line_current(
        self,
        power_mw: float,
        voltage_kv: float,
        power_factor: float = 0.95
    ) -> float:
        """
        Calculate line current from power flow.

        I = P / (sqrt(3) * V * pf)

        Args:
            power_mw: Active power in MW
            voltage_kv: Line voltage in kV
            power_factor: Power factor (default 0.95)

        Returns:
            Current in Amperes
        """
        if voltage_kv <= 0:
            return 0.0

        # Convert MW to W
        power_w = power_mw * 1e6

        # Three-phase current calculation
        current_a = power_w / (np.sqrt(3) * voltage_kv * 1000 * power_factor)

        return current_a

    def predict_line_current(
        self,
        line_id: str,
        voltage_kv: float,
        timestamp: Optional[datetime] = None,
        power_factor: float = 0.95,
        temperature_c: Optional[float] = None,
        wind_speed_ms: Optional[float] = None,
        solar_altitude: Optional[float] = None,
        humidity_pct: Optional[float] = None
    ) -> Dict[str, float]:
        """
        Predict line current based on load prediction with weather sensitivity.

        Args:
            line_id: Line identifier
            voltage_kv: Operating voltage (kV)
            timestamp: Prediction time (default: now)
            power_factor: Power factor (default: 0.95)
            temperature_c: Ambient temperature in Celsius (affects load)
            wind_speed_ms: Wind speed in m/s (affects load)
            solar_altitude: Solar altitude in degrees (affects load)
            humidity_pct: Relative humidity percentage (affects load)

        Returns:
            Dictionary with predicted_load_mw, predicted_current_a
        """
        predicted_load = self.predict_load(
            line_id,
            timestamp,
            temperature_c=temperature_c,
            wind_speed_ms=wind_speed_ms,
            solar_altitude=solar_altitude,
            humidity_pct=humidity_pct
        )
        predicted_current = self.calculate_line_current(
            predicted_load, voltage_kv, power_factor
        )

        return {
            'predicted_load_mw': predicted_load,
            'predicted_current_a': predicted_current,
            'voltage_kv': voltage_kv,
            'power_factor': power_factor,
        }


class SimpleLoadForecaster:
    """
    Even simpler forecaster for quick predictions.
    Uses fixed percentages of static rating.
    """

    @staticmethod
    def forecast_load_percentage(
        static_rating_mva: float,
        time_of_day: int,
        season: str = 'summer'
    ) -> float:
        """
        Forecast load as percentage of static rating.

        Args:
            static_rating_mva: Static line rating (MVA)
            time_of_day: Hour (0-23)
            season: 'summer' or 'winter'

        Returns:
            Predicted load in MVA
        """
        # Summer: higher afternoon loads due to AC
        # Winter: higher morning/evening loads due to heating
        if season == 'summer':
            if 6 <= time_of_day <= 9:
                load_pct = 0.75
            elif 10 <= time_of_day <= 17:
                load_pct = 0.90
            elif 18 <= time_of_day <= 21:
                load_pct = 0.85
            else:
                load_pct = 0.65
        else:  # winter
            if 6 <= time_of_day <= 9:
                load_pct = 0.80
            elif 10 <= time_of_day <= 17:
                load_pct = 0.75
            elif 18 <= time_of_day <= 21:
                load_pct = 0.85
            else:
                load_pct = 0.70

        return static_rating_mva * load_pct


# Example usage
if __name__ == "__main__":
    # Create predictor
    predictor = LoadPredictor()

    # Set baseline loads
    predictor.set_baseline_load("L0", 80.0)  # 80 MW baseline
    predictor.set_baseline_load("L1", 60.0)

    # Predict current load
    current_load = predictor.predict_load("L0")
    print(f"Current predicted load for L0: {current_load:.2f} MW")

    # Predict 24-hour series
    series = predictor.predict_load_series(
        "L0",
        datetime.now(),
        hours=24
    )
    print("\n24-hour forecast:")
    print(series.head(10))

    # Predict line current
    current_info = predictor.predict_line_current(
        "L0",
        voltage_kv=138,
        timestamp=datetime(2024, 10, 25, 14, 0)  # 2 PM
    )
    print(f"\nPredicted current: {current_info['predicted_current_a']:.1f} A")
    print(f"Predicted load: {current_info['predicted_load_mw']:.2f} MW")
