"""
IEEE 738 Dynamic Line Rating Calculator
Implements simplified thermal balance equation for transmission line ampacity
"""

import math
import numpy as np


class IEEE738Calculator:
    """
    Simplified IEEE 738 ampacity calculator using thermal balance equation:
    I²R(Tc) = Qc + Qr - Qs

    Where:
    - I = current (amperes)
    - R(Tc) = conductor resistance at temperature Tc
    - Qc = convective heat loss (cooling)
    - Qr = radiative heat loss (cooling)
    - Qs = solar heat gain (heating)
    """

    # Physical constants
    STEFAN_BOLTZMANN = 5.67e-8  # W/(m²·K⁴)

    def __init__(
        self,
        conductor_diameter_m=0.028,  # Default: ~28mm diameter (795 ACSR DRAKE)
        emissivity=0.5,
        absorptivity=0.5,
        resistance_25C=0.0001,  # ohm/m at 25°C
        resistance_temp_coeff=0.00404,  # per °C (aluminum)
    ):
        """
        Initialize IEEE 738 calculator with conductor parameters.

        Args:
            conductor_diameter_m: Conductor diameter in meters
            emissivity: Surface emissivity (0-1), typical 0.5 for weathered conductors
            absorptivity: Solar absorptivity (0-1), typical 0.5
            resistance_25C: AC resistance at 25°C in ohm/meter
            resistance_temp_coeff: Temperature coefficient of resistance (1/°C)
        """
        self.diameter = conductor_diameter_m
        self.emissivity = emissivity
        self.absorptivity = absorptivity
        self.R_25 = resistance_25C
        self.alpha = resistance_temp_coeff

    def conductor_resistance(self, temp_c):
        """
        Calculate conductor resistance at given temperature.
        R(T) = R(25) * [1 + α(T - 25)]

        Args:
            temp_c: Conductor temperature in Celsius

        Returns:
            Resistance in ohm/meter
        """
        return self.R_25 * (1 + self.alpha * (temp_c - 25))

    def solar_heat_gain(self, solar_altitude=45):
        """
        Calculate solar heat gain per meter of conductor (Qs).
        Simplified model assuming clear sky conditions.

        Qs = α * I_solar * D

        Args:
            solar_altitude: Solar altitude angle in degrees (default 45°)

        Returns:
            Solar heat gain in W/m
        """
        # Solar radiation intensity (W/m²) - simplified model
        # Clear sky: 1000 W/m² at solar noon, scaled by sin(altitude)
        if solar_altitude <= 0:
            return 0.0

        I_solar = 1000 * math.sin(math.radians(solar_altitude))

        # Heat gain per unit length
        Qs = self.absorptivity * I_solar * self.diameter

        return Qs

    def radiative_heat_loss(self, temp_conductor_c, temp_ambient_c):
        """
        Calculate radiative heat loss per meter (Qr).

        Qr = π * D * ε * σ * (Tc⁴ - Ta⁴)

        Args:
            temp_conductor_c: Conductor temperature in Celsius
            temp_ambient_c: Ambient temperature in Celsius

        Returns:
            Radiative heat loss in W/m
        """
        # Convert to Kelvin
        Tc_K = temp_conductor_c + 273.15
        Ta_K = temp_ambient_c + 273.15

        # Stefan-Boltzmann law
        Qr = (
            math.pi * self.diameter * self.emissivity * self.STEFAN_BOLTZMANN
            * (Tc_K**4 - Ta_K**4)
        )

        return Qr

    def convective_heat_loss(
        self, temp_conductor_c, temp_ambient_c, wind_speed_ms, wind_angle_deg=90
    ):
        """
        Calculate convective (forced + natural) heat loss per meter (Qc).

        Uses simplified correlation for forced convection on cylinders.

        Args:
            temp_conductor_c: Conductor temperature in Celsius
            temp_ambient_c: Ambient temperature in Celsius
            wind_speed_ms: Wind speed in m/s
            wind_angle_deg: Angle between wind and conductor (default 90° perpendicular)

        Returns:
            Convective heat loss in W/m
        """
        # Average film temperature
        T_film = (temp_conductor_c + temp_ambient_c) / 2 + 273.15  # Kelvin

        # Air properties at film temperature (simplified)
        # Thermal conductivity of air (W/m·K)
        k_air = 0.024 + 0.00007 * (T_film - 273.15)

        # Kinematic viscosity (m²/s) - approximate
        nu = 15e-6 * (T_film / 300) ** 1.5

        # Prandtl number for air (dimensionless)
        Pr = 0.7

        # Effective wind speed (perpendicular component)
        V_eff = wind_speed_ms * abs(math.sin(math.radians(wind_angle_deg)))
        V_eff = max(V_eff, 0.5)  # Minimum wind speed for natural convection

        # Reynolds number
        Re = V_eff * self.diameter / nu

        # Nusselt number - Churchill-Bernstein correlation (simplified)
        if Re < 1:
            Nu = 0.4  # Free convection minimum
        else:
            Nu = 0.3 + 0.62 * Re**0.5 * Pr**(1/3)

        # Convective heat transfer coefficient (W/m²·K)
        h = Nu * k_air / self.diameter

        # Convective heat loss per unit length
        delta_T = temp_conductor_c - temp_ambient_c
        Qc = math.pi * self.diameter * h * delta_T

        return max(Qc, 0)  # Ensure non-negative

    def calculate_ampacity(
        self,
        temp_ambient_c,
        wind_speed_ms,
        temp_conductor_max_c=75,
        solar_altitude=45,
        wind_angle_deg=90,
    ):
        """
        Calculate maximum steady-state current (ampacity) using thermal balance.

        Heat balance at maximum conductor temperature:
        I² * R(Tc_max) = Qc + Qr - Qs

        Args:
            temp_ambient_c: Ambient air temperature (°C)
            wind_speed_ms: Wind speed (m/s)
            temp_conductor_max_c: Maximum allowable conductor temperature (°C), default 75°C
            solar_altitude: Solar altitude angle (degrees), default 45°
            wind_angle_deg: Wind angle relative to conductor (degrees), default 90°

        Returns:
            Maximum current (ampacity) in Amperes
        """
        # Calculate heat losses and gains at maximum conductor temperature
        Qc = self.convective_heat_loss(
            temp_conductor_max_c, temp_ambient_c, wind_speed_ms, wind_angle_deg
        )
        Qr = self.radiative_heat_loss(temp_conductor_max_c, temp_ambient_c)
        Qs = self.solar_heat_gain(solar_altitude)

        # Net heat dissipation capacity (W/m)
        Q_net = Qc + Qr - Qs

        # Conductor resistance at maximum temperature
        R_Tc = self.conductor_resistance(temp_conductor_max_c)

        # Maximum current from thermal balance: I = sqrt(Q_net / R)
        if Q_net <= 0 or R_Tc <= 0:
            # No cooling capacity or invalid conditions
            return 0.0

        I_max = math.sqrt(Q_net / R_Tc)

        return I_max

    def calculate_ampacity_detailed(
        self,
        temp_ambient_c,
        wind_speed_ms,
        temp_conductor_max_c=75,
        solar_altitude=45,
        wind_angle_deg=90,
    ):
        """
        Calculate ampacity with detailed breakdown of heat balance components.

        Returns:
            dict with keys:
                - ampacity: Maximum current (A)
                - Qc: Convective heat loss (W/m)
                - Qr: Radiative heat loss (W/m)
                - Qs: Solar heat gain (W/m)
                - Q_net: Net heat dissipation (W/m)
                - R_conductor: Conductor resistance (ohm/m)
                - temp_conductor: Conductor temperature (°C)
        """
        Qc = self.convective_heat_loss(
            temp_conductor_max_c, temp_ambient_c, wind_speed_ms, wind_angle_deg
        )
        Qr = self.radiative_heat_loss(temp_conductor_max_c, temp_ambient_c)
        Qs = self.solar_heat_gain(solar_altitude)
        Q_net = Qc + Qr - Qs
        R_Tc = self.conductor_resistance(temp_conductor_max_c)

        I_max = math.sqrt(max(Q_net / R_Tc, 0)) if R_Tc > 0 else 0.0

        return {
            "ampacity": I_max,
            "Qc_convective": Qc,
            "Qr_radiative": Qr,
            "Qs_solar": Qs,
            "Q_net": Q_net,
            "R_conductor": R_Tc,
            "temp_conductor": temp_conductor_max_c,
            "temp_ambient": temp_ambient_c,
            "wind_speed": wind_speed_ms,
        }


def get_conductor_params(conductor_name):
    """
    Get conductor parameters from name.
    Returns default parameters for common ACSR conductors.

    Args:
        conductor_name: Conductor type name (e.g., "795 ACSR 26/7 DRAKE")

    Returns:
        dict with diameter_m, resistance_25C, temp_coeff
    """
    # Lookup table for common conductors (diameter in meters, resistance in ohm/km at 25°C)
    conductor_database = {
        "336.4 ACSR 30/7 ORIOLE": {"diameter_m": 0.0188, "R_ohm_per_km": 0.2708, "temp_coeff": 0.00404},
        "556.5 ACSR 26/7 DOVE": {"diameter_m": 0.0235, "R_ohm_per_km": 0.1655, "temp_coeff": 0.00404},
        "795 ACSR 26/7 DRAKE": {"diameter_m": 0.028, "R_ohm_per_km": 0.1166, "temp_coeff": 0.00404},
        "954 ACSR 54/7 CARDINAL": {"diameter_m": 0.0303, "R_ohm_per_km": 0.0986, "temp_coeff": 0.00404},
        "1272 ACSR 45/7 BITTERN": {"diameter_m": 0.0341, "R_ohm_per_km": 0.0761, "temp_coeff": 0.00404},
        "1590 ACSR 54/19 FALCON": {"diameter_m": 0.0392, "R_ohm_per_km": 0.0613, "temp_coeff": 0.00404},
    }

    # Default conductor if not found
    default = {"diameter_m": 0.028, "R_ohm_per_km": 0.1166, "temp_coeff": 0.00404}

    params = conductor_database.get(conductor_name, default)

    # Convert resistance from ohm/km to ohm/m
    params["R_ohm_per_m"] = params["R_ohm_per_km"] / 1000

    return params


# Example usage
if __name__ == "__main__":
    # Create calculator for 795 ACSR DRAKE conductor
    calc = IEEE738Calculator(
        conductor_diameter_m=0.028,
        resistance_25C=0.1166 / 1000,  # Convert ohm/km to ohm/m
        emissivity=0.5,
        absorptivity=0.5,
    )

    # Calculate ampacity for typical summer conditions
    ampacity = calc.calculate_ampacity(
        temp_ambient_c=35,      # 35°C ambient
        wind_speed_ms=2.0,      # 2 m/s wind
        temp_conductor_max_c=75, # 75°C max conductor temp
        solar_altitude=60,      # 60° sun angle
        wind_angle_deg=90       # Perpendicular wind
    )

    print(f"Ampacity: {ampacity:.1f} A")

    # Detailed calculation
    details = calc.calculate_ampacity_detailed(
        temp_ambient_c=35,
        wind_speed_ms=2.0,
        temp_conductor_max_c=75,
    )

    print("\nDetailed Heat Balance:")
    print(f"  Convective cooling: {details['Qc_convective']:.2f} W/m")
    print(f"  Radiative cooling:  {details['Qr_radiative']:.2f} W/m")
    print(f"  Solar heating:      {details['Qs_solar']:.2f} W/m")
    print(f"  Net heat capacity:  {details['Q_net']:.2f} W/m")
    print(f"  Ampacity:           {details['ampacity']:.1f} A")
