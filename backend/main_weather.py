"""
FastAPI Backend for IEEE 738 Dynamic Line Rating System
WITH WEATHER API INTEGRATION
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Literal
from datetime import datetime
import pandas as pd
import numpy as np
import os

# Import our modules
from ieee738 import IEEE738Calculator, get_conductor_params
from load_model import LoadPredictor
from weather_service import WeatherService, WeatherData

# Initialize FastAPI app
app = FastAPI(
    title="IEEE 738 Dynamic Line Rating API (Weather-Enabled)",
    description="Real-time transmission line ampacity with live weather data",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global data storage
lines_data = None
load_predictor = None
weather_service = None


# Pydantic models
class WeatherBasedRequest(BaseModel):
    """Request for weather-based calculation"""
    line_id: Optional[str] = Field(None, description="Specific line ID, or None for all lines")
    weather_source: Literal["live", "scenario", "manual"] = Field(
        "scenario",
        description="Weather source: 'live' (OpenWeather API), 'scenario' (pre-defined), 'manual'"
    )
    scenario_name: Optional[str] = Field(
        "normal_summer",
        description="Scenario name if weather_source='scenario'"
    )
    # Manual weather parameters (used if weather_source='manual')
    temp_ambient_c: Optional[float] = Field(30, ge=-50, le=60)
    wind_speed_ms: Optional[float] = Field(2.0, ge=0, le=30)
    solar_altitude: Optional[float] = Field(45, ge=0, le=90)
    wind_angle_deg: Optional[float] = Field(90, ge=0, le=180)
    # Advanced parameters
    temp_conductor_max_c: float = Field(75, ge=50, le=100)
    emissivity: Optional[float] = Field(0.5, ge=0.2, le=0.95, description="Conductor emissivity")
    absorptivity: Optional[float] = Field(0.5, ge=0.2, le=0.95, description="Solar absorptivity")


class WeatherBasedResponse(BaseModel):
    """Response with weather-based calculation"""
    line_id: str
    line_name: str
    conductor: str
    voltage_kv: float
    # Weather info
    weather: Dict
    # Ampacity results
    ampacity: float
    ampacity_mva: float
    static_rating_mva: float
    # Load prediction
    predicted_load_mw: float
    predicted_current_a: float
    utilization_pct: float
    status: str
    # Details
    details: Optional[Dict] = None


class ScenarioInfo(BaseModel):
    """Info about a pre-defined scenario"""
    scenario_id: str
    name: str
    description: str
    temperature_c: float
    wind_speed_ms: float


class LoadPredictionRequest(BaseModel):
    """Request model for load prediction"""
    line_id: str
    hours_ahead: int = 24


class CompareScenariosRequest(BaseModel):
    """Request model for comparing scenarios"""
    line_id: str = "L0"
    scenarios: Optional[List[str]] = None


# Utility functions
def load_data():
    """Load transmission line data from CSV files"""
    global lines_data, load_predictor, weather_service

    # Look for data in osu_hackathon repository
    current_dir = os.path.dirname(__file__)
    data_dir = os.path.join(current_dir, '..', 'osu_hackathon', 'hawaii40_osu', 'csv')

    lines_data = pd.read_csv(os.path.join(data_dir, 'lines.csv'))
    buses_data = pd.read_csv(os.path.join(data_dir, 'buses.csv'))

    # Load actual power flow data from PyPSA solution (theoretically correct approach)
    flows_path = os.path.join(current_dir, '..', 'osu_hackathon', 'hawaii40_osu', 'line_flows_nominal.csv')
    flows_data = pd.read_csv(flows_path)

    lines_data = lines_data.merge(
        buses_data[['name', 'v_nom']],
        left_on='bus0',
        right_on='name',
        how='left',
        suffixes=('', '_bus')
    )
    lines_data.rename(columns={'v_nom': 'voltage_kv'}, inplace=True)
    lines_data.drop(columns=['name_bus'], inplace=True, errors='ignore')

    # Merge actual power flow data
    lines_data = lines_data.merge(
        flows_data[['name', 'p0_nominal']],
        on='name',
        how='left'
    )

    load_predictor = LoadPredictor()
    for _, line in lines_data.iterrows():
        # Use actual power flow from PyPSA solution instead of arbitrary percentage
        # This respects network physics (Kirchhoff's laws, impedances, AC power flow)
        baseline_mw = line['p0_nominal'] if pd.notna(line.get('p0_nominal')) else line['s_nom'] * 0.7
        load_predictor.set_baseline_load(line['name'], baseline_mw)

    # Initialize weather service
    weather_service = WeatherService()

    print(f"Loaded {len(lines_data)} transmission lines")
    return lines_data


def determine_status(utilization_pct: float) -> str:
    """Determine line status"""
    if utilization_pct >= 95:
        return "Critical"
    elif utilization_pct >= 80:
        return "Warning"
    else:
        return "Normal"


def calculate_mva_from_current(current_a: float, voltage_kv: float) -> float:
    """Convert current to MVA"""
    return (np.sqrt(3) * voltage_kv * current_a) / 1000


def calculate_line_with_weather(
    line_data: pd.Series,
    weather: WeatherData,
    temp_conductor_max_c: float = 75,
    emissivity: float = 0.5,
    absorptivity: float = 0.5
) -> Dict:
    """Calculate ampacity for a line using weather data"""

    # Get conductor parameters
    conductor_name = line_data['conductor']
    conductor_params = get_conductor_params(conductor_name)

    # Create calculator with dynamic parameters
    calculator = IEEE738Calculator(
        conductor_diameter_m=conductor_params['diameter_m'],
        resistance_25C=conductor_params['R_ohm_per_m'],
        emissivity=emissivity,
        absorptivity=absorptivity,
        resistance_temp_coeff=conductor_params['temp_coeff']
    )

    # Calculate ampacity with weather data
    ampacity_details = calculator.calculate_ampacity_detailed(
        temp_ambient_c=weather.temperature_c,
        wind_speed_ms=weather.wind_speed_ms,
        temp_conductor_max_c=temp_conductor_max_c,
        solar_altitude=weather.solar_altitude,
        wind_angle_deg=weather.wind_angle_deg
    )

    ampacity_amps = ampacity_details['ampacity']
    voltage_kv = line_data['voltage_kv']
    ampacity_mva = calculate_mva_from_current(ampacity_amps, voltage_kv)

    # Predict load with weather sensitivity
    # Use hour_of_day from weather data if available (for time-aware scenarios)
    timestamp = datetime.now()
    if hasattr(weather, 'hour_of_day') and weather.hour_of_day is not None:
        timestamp = timestamp.replace(hour=int(weather.hour_of_day))

    predicted_current_data = load_predictor.predict_line_current(
        line_data['name'],
        voltage_kv,
        timestamp=timestamp,
        temperature_c=weather.temperature_c,
        wind_speed_ms=weather.wind_speed_ms,
        solar_altitude=weather.solar_altitude,
        humidity_pct=weather.humidity_pct
    )

    predicted_current = predicted_current_data['predicted_current_a']
    predicted_load_mw = predicted_current_data['predicted_load_mw']

    # Get static rating from CSV (industry standard)
    static_rating_mva = line_data['s_nom']

    # Calculate utilization based on STATIC RATING (industry standard approach)
    # This aligns with NERC/FERC regulations and protection relay settings
    utilization_pct = (predicted_load_mw / static_rating_mva * 100) if static_rating_mva > 0 else 0
    status = determine_status(utilization_pct)

    # Calculate additional metrics for comparison
    dynamic_utilization_pct = (predicted_current / ampacity_amps * 100) if ampacity_amps > 0 else 0
    capacity_increase_pct = ((ampacity_mva - static_rating_mva) / static_rating_mva * 100) if static_rating_mva > 0 else 0

    return {
        "line_id": line_data['name'],
        "line_name": line_data['branch_name'],
        "conductor": conductor_name,
        "voltage_kv": voltage_kv,
        "weather": {
            "temperature_c": weather.temperature_c,
            "wind_speed_ms": weather.wind_speed_ms,
            "solar_altitude": weather.solar_altitude,
            "wind_angle_deg": weather.wind_angle_deg,
            "source": weather.source,
            "location": weather.location,
            "description": weather.description
        },
        "ampacity": ampacity_amps,
        "ampacity_mva": ampacity_mva,
        "static_rating_mva": static_rating_mva,
        "predicted_load_mw": predicted_load_mw,
        "predicted_current_a": predicted_current,
        "utilization_pct": utilization_pct,  # Based on static rating (industry standard)
        "dynamic_utilization_pct": dynamic_utilization_pct,  # Based on IEEE 738 dynamic rating
        "capacity_increase_pct": capacity_increase_pct,  # How much more capacity DLR provides
        "status": status,
        "details": {
            "temp_conductor_max_c": temp_conductor_max_c,
            "emissivity": emissivity,
            "absorptivity": absorptivity,
            "Qc_convective": ampacity_details['Qc_convective'],
            "Qr_radiative": ampacity_details['Qr_radiative'],
            "Qs_solar": ampacity_details['Qs_solar'],
            "Q_net": ampacity_details['Q_net']
        }
    }


# Startup
@app.on_event("startup")
async def startup_event():
    """Load data on startup"""
    try:
        load_data()
        print("Data loaded successfully")
    except Exception as e:
        print(f"Error loading data: {e}")


# API Endpoints

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "IEEE 738 Dynamic Line Rating API with Weather Integration",
        "version": "2.0.0",
        "features": [
            "Live weather data from OpenWeatherMap",
            "7 pre-defined demo scenarios",
            "Manual weather input",
            "Dynamic conductor properties"
        ],
        "endpoints": {
            "scenarios": "/weather/scenarios",
            "calculate_with_weather": "/calculate_with_weather",
            "compare_scenarios": "/compare_scenarios"
        }
    }


@app.get("/health")
async def health_check():
    """Health check"""
    if lines_data is None:
        raise HTTPException(status_code=503, detail="Data not loaded")

    return {
        "status": "healthy",
        "lines_loaded": len(lines_data),
        "weather_service": "enabled",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/weather/scenarios", response_model=List[ScenarioInfo])
async def list_scenarios():
    """
    List all available pre-defined weather scenarios for demos.

    Perfect for hackathon presentations!
    """
    if weather_service is None:
        raise HTTPException(status_code=503, detail="Weather service not initialized")

    scenarios = weather_service.list_scenarios()

    return [
        ScenarioInfo(
            scenario_id=key,
            name=info["name"],
            description=info["description"],
            temperature_c=info["temperature_c"],
            wind_speed_ms=info["wind_speed_ms"]
        )
        for key, info in scenarios.items()
    ]


@app.post("/calculate_with_weather", response_model=WeatherBasedResponse)
async def calculate_with_weather(request: WeatherBasedRequest):
    """
    Calculate ampacity using weather data.

    Weather sources:
    - 'live': Fetch real-time weather from OpenWeatherMap (Hawaii)
    - 'scenario': Use pre-defined scenario (great for demos!)
    - 'manual': Use provided temperature/wind values
    """
    if lines_data is None or weather_service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")

    # Get weather data based on source
    try:
        if request.weather_source == "live":
            weather = weather_service.get_weather_live()
        elif request.weather_source == "scenario":
            if not request.scenario_name:
                raise ValueError("scenario_name required for scenario weather source")
            weather = weather_service.get_weather_scenario(request.scenario_name)
        else:  # manual
            weather = weather_service.get_weather_manual(
                temperature_c=request.temp_ambient_c,
                wind_speed_ms=request.wind_speed_ms,
                solar_altitude=request.solar_altitude,
                wind_angle_deg=request.wind_angle_deg
            )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Weather error: {str(e)}")

    # Get line data
    if not request.line_id:
        request.line_id = "L0"  # Default to first line

    line = lines_data[lines_data['name'] == request.line_id]
    if line.empty:
        raise HTTPException(status_code=404, detail=f"Line {request.line_id} not found")

    line = line.iloc[0]

    # Calculate with weather
    result = calculate_line_with_weather(
        line,
        weather,
        temp_conductor_max_c=request.temp_conductor_max_c,
        emissivity=request.emissivity,
        absorptivity=request.absorptivity
    )

    return WeatherBasedResponse(**result)


@app.get("/calculate_all_with_weather")
async def calculate_all_with_weather(
    weather_source: Literal["live", "scenario", "manual"] = "scenario",
    scenario_name: str = "normal_summer",
    limit: Optional[int] = None,
    # Manual weather parameters
    temp_ambient_c: float = 30.0,
    wind_speed_ms: float = 2.0,
    solar_altitude: float = 45.0,
    wind_angle_deg: float = 90.0,
    humidity_pct: float = 70.0
):
    """
    Calculate ampacity for all lines using weather data.

    Great for dashboard view!

    Args:
        weather_source: 'scenario', 'live', or 'manual'
        scenario_name: Which pre-defined scenario (if weather_source='scenario')
        limit: Limit number of lines returned
        temp_ambient_c: Manual temperature in Celsius (if weather_source='manual')
        wind_speed_ms: Manual wind speed in m/s (if weather_source='manual')
        solar_altitude: Manual solar altitude 0-90 degrees (if weather_source='manual')
        wind_angle_deg: Wind angle relative to line (usually 90)
        humidity_pct: Relative humidity percentage
    """
    if lines_data is None or weather_service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")

    # Get weather
    try:
        if weather_source == "live":
            weather = weather_service.get_weather_live()
        elif weather_source == "scenario":
            weather = weather_service.get_weather_scenario(scenario_name)
        else:  # manual
            weather = weather_service.get_weather_manual(
                temp_ambient_c,
                wind_speed_ms,
                solar_altitude,
                wind_angle_deg,
                humidity_pct
            )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Weather error: {str(e)}")

    # Calculate for all lines
    results = []
    lines_to_process = lines_data.head(limit) if limit else lines_data

    for _, line in lines_to_process.iterrows():
        try:
            result = calculate_line_with_weather(line, weather)
            results.append(result)
        except Exception as e:
            print(f"Error processing line {line['name']}: {e}")
            continue

    return {
        "weather": {
            "temperature_c": weather.temperature_c,
            "wind_speed_ms": weather.wind_speed_ms,
            "source": weather.source,
            "description": weather.description
        },
        "total_lines": len(results),
        "lines": results
    }


@app.post("/compare_scenarios")
async def compare_scenarios(request: CompareScenariosRequest):
    """
    Compare ampacity across multiple weather scenarios.

    Perfect for hackathon demo - show how weather affects capacity!
    """
    if lines_data is None or weather_service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")

    # Default scenarios for comparison
    scenarios = request.scenarios if request.scenarios else ["extreme_heat", "hot_day", "normal_summer", "optimal", "windy_day"]

    # Get line
    line = lines_data[lines_data['name'] == request.line_id]
    if line.empty:
        raise HTTPException(status_code=404, detail=f"Line {request.line_id} not found")
    line = line.iloc[0]

    # Calculate for each scenario
    comparisons = []
    for scenario_name in scenarios:
        try:
            weather = weather_service.get_weather_scenario(scenario_name)
            result = calculate_line_with_weather(line, weather)
            comparisons.append({
                "scenario": scenario_name,
                "weather": result["weather"],
                "ampacity": float(result["ampacity"]),  # Convert numpy to Python float
                "ampacity_mva": float(result["ampacity_mva"]),
                "utilization_pct": float(result["utilization_pct"]),
                "status": result["status"]
            })
        except Exception as e:
            print(f"Error with scenario {scenario_name}: {e}")
            continue

    return {
        "line_id": request.line_id,
        "line_name": str(line['branch_name']),  # Convert to Python str
        "conductor": str(line['conductor']),
        "static_rating_mva": float(line['s_nom']),  # Convert numpy to Python float
        "comparisons": comparisons
    }


@app.post("/predict_load")
async def predict_load(request: LoadPredictionRequest):
    """
    Predict load for a transmission line over time.

    Returns 24-hour load forecast with predicted MW and current.
    """
    if lines_data is None or load_predictor is None:
        raise HTTPException(status_code=503, detail="Service not initialized")

    # Find the line
    line = lines_data[lines_data['name'] == request.line_id]
    if line.empty:
        raise HTTPException(status_code=404, detail=f"Line {request.line_id} not found")

    line = line.iloc[0]
    voltage_kv = line['voltage_kv']

    # Parse timestamp
    start_time = datetime.now()

    # Generate predictions
    predictions = []
    import pandas as pd
    for hour in range(request.hours_ahead):
        pred_time = start_time + pd.Timedelta(hours=hour)
        pred_data = load_predictor.predict_line_current(
            request.line_id,
            voltage_kv,
            timestamp=pred_time
        )

        predictions.append({
            "timestamp": pred_time.isoformat(),
            "hour": pred_time.hour,
            "predicted_load_mw": round(pred_data['predicted_load_mw'], 2),
            "predicted_current_a": round(pred_data['predicted_current_a'], 1)
        })

    return {
        "line_id": request.line_id,
        "predictions": predictions
    }


@app.get("/timelapse/24hour")
async def get_24hour_timelapse(
    weather_source: str = Query("manual", description="Weather source: 'scenario', 'live', or 'manual'"),
    scenario_name: str = Query("normal_midday", description="Scenario name if using scenario weather"),
    temp_ambient_c: float = Query(30.0, description="Base temperature in Celsius"),
    wind_speed_ms: float = Query(2.0, description="Wind speed in m/s"),
    humidity_pct: float = Query(70.0, description="Humidity percentage")
):
    """
    Get grid state for all 24 hours of the day for time-lapse animation.

    Returns hourly snapshots showing how line utilization changes throughout the day
    based on load patterns and solar heating.

    Perfect for animated dashboard visualization!
    """
    if lines_data is None or weather_service is None or load_predictor is None:
        raise HTTPException(status_code=503, detail="Service not initialized")

    hourly_snapshots = []

    # Process each hour of the day
    for hour in range(24):
        # Calculate solar altitude based on hour (approximate for Hawaii ~21°N)
        # Solar noon at hour 12, sunrise ~6, sunset ~18
        if hour < 6 or hour > 18:
            solar_altitude = 0.0  # Night
        elif hour == 12:
            solar_altitude = 75.0  # Solar noon
        else:
            hours_from_noon = abs(12 - hour)
            solar_altitude = max(0, 75 - (hours_from_noon * 10))

        # Get weather for this hour
        try:
            if weather_source == "live":
                weather = weather_service.get_weather_live()
            elif weather_source == "scenario":
                weather = weather_service.get_weather_scenario(scenario_name)
            else:  # manual
                weather = weather_service.get_weather_manual(
                    temp_ambient_c,
                    wind_speed_ms,
                    solar_altitude,
                    90.0,  # wind angle
                    humidity_pct
                )
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Weather error at hour {hour}: {str(e)}")

        # Calculate for all lines at this hour
        hour_lines = []
        for _, line in lines_data.iterrows():
            try:
                # Get time-based load factor
                load_factor = load_predictor.hourly_profile.get(hour, 1.0)

                # Calculate IEEE 738 ampacity
                conductor_params = get_conductor_params(line['conductor'])
                calc = IEEE738Calculator(
                    conductor_diameter_m=conductor_params['diameter_m'],
                    resistance_25C=conductor_params['R_ohm_per_m'],
                    emissivity=0.5,
                    absorptivity=0.5,
                    resistance_temp_coeff=conductor_params['temp_coeff']
                )

                ampacity_details = calc.calculate_ampacity_detailed(
                    temp_ambient_c=weather.temperature_c,
                    wind_speed_ms=weather.wind_speed_ms,
                    wind_angle_deg=weather.wind_angle_deg,
                    solar_altitude=weather.solar_altitude,
                    temp_conductor_max_c=line['MOT']
                )

                ampacity_amps = ampacity_details['ampacity']

                voltage_kv = line['voltage_kv']
                ampacity_mva = (ampacity_amps * voltage_kv * np.sqrt(3)) / 1000

                # Get baseline load and apply hourly factor
                baseline_load_mw = line.get('p0_nominal', 0)
                predicted_load_mw = baseline_load_mw * load_factor
                predicted_current_a = (predicted_load_mw * 1000) / (voltage_kv * np.sqrt(3))

                # Calculate utilization
                utilization_pct = (predicted_current_a / ampacity_amps * 100) if ampacity_amps > 0 else 0

                # Determine status
                if utilization_pct >= 95:
                    status = "Critical"
                elif utilization_pct >= 80:
                    status = "Warning"
                else:
                    status = "Normal"

                hour_lines.append({
                    "line_id": line['name'],
                    "utilization_pct": round(float(utilization_pct), 1),
                    "status": status,
                    "ampacity_mva": round(float(ampacity_mva), 1),
                    "predicted_load_mw": round(float(predicted_load_mw), 1)
                })

            except Exception as e:
                print(f"Error processing line {line['name']} at hour {hour}: {e}")
                continue

        # Count statuses for this hour
        critical_count = sum(1 for l in hour_lines if l['status'] == 'Critical')
        warning_count = sum(1 for l in hour_lines if l['status'] == 'Warning')
        normal_count = sum(1 for l in hour_lines if l['status'] == 'Normal')

        hourly_snapshots.append({
            "hour": hour,
            "time_label": f"{hour:02d}:00",
            "solar_altitude": round(solar_altitude, 1),
            "load_factor": round(load_predictor.hourly_profile.get(hour, 1.0), 3),
            "lines": hour_lines,
            "summary": {
                "total_lines": len(hour_lines),
                "critical": critical_count,
                "warning": warning_count,
                "normal": normal_count
            }
        })

    return {
        "weather_base": {
            "temperature_c": temp_ambient_c,
            "wind_speed_ms": wind_speed_ms,
            "humidity_pct": humidity_pct
        },
        "total_hours": 24,
        "snapshots": hourly_snapshots
    }


@app.get("/contingency/n1/{failed_line_id}")
async def n1_contingency_analysis(
    failed_line_id: str,
    weather_source: str = Query("manual", description="Weather source"),
    scenario_name: str = Query("normal_midday", description="Scenario name"),
    temp_ambient_c: float = Query(30.0, description="Temperature in Celsius"),
    wind_speed_ms: float = Query(2.5, description="Wind speed in m/s"),
    humidity_pct: float = Query(70.0, description="Humidity percentage")
):
    """
    N-1 Contingency Analysis: What happens if a line fails?

    Simulates the outage of a transmission line and shows how power redistributes
    to other lines, identifying potential overloads and cascade failures.

    This is a simplified analysis using power redistribution heuristics.
    In production, this would use full AC power flow (PyPSA/MATPOWER).
    """
    if lines_data is None or weather_service is None or load_predictor is None:
        raise HTTPException(status_code=503, detail="Service not initialized")

    # Find the failed line
    failed_line = lines_data[lines_data['name'] == failed_line_id]
    if failed_line.empty:
        raise HTTPException(status_code=404, detail=f"Line {failed_line_id} not found")

    failed_line = failed_line.iloc[0]

    # Get weather
    try:
        if weather_source == "live":
            weather = weather_service.get_weather_live()
        elif weather_source == "scenario":
            weather = weather_service.get_weather_scenario(scenario_name)
        else:
            weather = weather_service.get_weather_manual(
                temp_ambient_c, wind_speed_ms, 45.0, 90.0, humidity_pct
            )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Weather error: {str(e)}")

    # Get current hour for load factor
    current_hour = datetime.now().hour
    load_factor = load_predictor.hourly_profile.get(current_hour, 1.0)

    # Calculate baseline state (no outage)
    baseline_state = []
    for _, line in lines_data.iterrows():
        try:
            baseline_load_mw = line.get('p0_nominal', 0) * load_factor
            baseline_state.append({
                'line_id': line['name'],
                'baseline_flow_mw': float(baseline_load_mw),
                'bus0': int(line['bus0']),
                'bus1': int(line['bus1']),
                'impedance': float(line.get('x', 1.0))  # Use reactance as proxy for impedance
            })
        except Exception as e:
            continue

    # Find parallel/alternative paths
    # Lines that share a bus with the failed line are candidates for redistribution
    failed_bus0 = failed_line['bus0']
    failed_bus1 = failed_line['bus1']
    failed_flow = failed_line.get('p0_nominal', 0) * load_factor

    affected_lines = []
    for state in baseline_state:
        if state['line_id'] == failed_line_id:
            continue

        # Check if line is connected to either end of failed line
        is_parallel = (
            (state['bus0'] == failed_bus0 or state['bus0'] == failed_bus1) or
            (state['bus1'] == failed_bus0 or state['bus1'] == failed_bus1)
        )

        if is_parallel:
            affected_lines.append(state)

    # Redistribute failed line's power to parallel paths
    # Simple heuristic: distribute inversely proportional to impedance
    if affected_lines:
        total_conductance = sum(1.0 / max(line['impedance'], 0.01) for line in affected_lines)

        for affected in affected_lines:
            conductance = 1.0 / max(affected['impedance'], 0.01)
            redistribution_factor = conductance / total_conductance
            additional_flow = failed_flow * redistribution_factor
            affected['contingency_flow_mw'] = affected['baseline_flow_mw'] + additional_flow
            affected['flow_increase_mw'] = additional_flow
            affected['flow_increase_pct'] = (additional_flow / max(affected['baseline_flow_mw'], 0.1)) * 100

    # Calculate ampacity and status for affected lines
    contingency_results = []
    overloaded_count = 0
    critical_count = 0
    warning_count = 0

    for affected in affected_lines:
        line_data = lines_data[lines_data['name'] == affected['line_id']].iloc[0]

        try:
            # Calculate ampacity
            conductor_params = get_conductor_params(line_data['conductor'])
            calc = IEEE738Calculator(
                conductor_diameter_m=conductor_params['diameter_m'],
                resistance_25C=conductor_params['R_ohm_per_m'],
                emissivity=0.5,
                absorptivity=0.5,
                resistance_temp_coeff=conductor_params['temp_coeff']
            )

            ampacity_details = calc.calculate_ampacity_detailed(
                temp_ambient_c=weather.temperature_c,
                wind_speed_ms=weather.wind_speed_ms,
                wind_angle_deg=90.0,
                solar_altitude=45.0,
                temp_conductor_max_c=line_data['MOT']
            )

            ampacity_amps = ampacity_details['ampacity']
            voltage_kv = line_data['voltage_kv']
            ampacity_mva = (ampacity_amps * voltage_kv * np.sqrt(3)) / 1000

            # Calculate utilization with contingency flow
            contingency_flow_mw = affected.get('contingency_flow_mw', affected['baseline_flow_mw'])
            static_rating_mva = line_data['s_nom']

            baseline_utilization_pct = (affected['baseline_flow_mw'] / static_rating_mva * 100) if static_rating_mva > 0 else 0
            contingency_utilization_pct = (contingency_flow_mw / static_rating_mva * 100) if static_rating_mva > 0 else 0

            # Determine status
            if contingency_utilization_pct >= 100:
                status = "Overload"
                overloaded_count += 1
            elif contingency_utilization_pct >= 95:
                status = "Critical"
                critical_count += 1
            elif contingency_utilization_pct >= 80:
                status = "Warning"
                warning_count += 1
            else:
                status = "Normal"

            contingency_results.append({
                'line_id': affected['line_id'],
                'line_name': str(line_data['branch_name']),
                'conductor': str(line_data['conductor']),
                'baseline_flow_mw': round(float(affected['baseline_flow_mw']), 2),
                'contingency_flow_mw': round(float(contingency_flow_mw), 2),
                'flow_increase_mw': round(float(affected.get('flow_increase_mw', 0)), 2),
                'flow_increase_pct': round(float(affected.get('flow_increase_pct', 0)), 1),
                'static_rating_mva': round(float(static_rating_mva), 1),
                'ampacity_mva': round(float(ampacity_mva), 1),
                'baseline_utilization_pct': round(float(baseline_utilization_pct), 1),
                'contingency_utilization_pct': round(float(contingency_utilization_pct), 1),
                'utilization_increase_pct': round(float(contingency_utilization_pct - baseline_utilization_pct), 1),
                'status': status
            })
        except Exception as e:
            print(f"Error analyzing line {affected['line_id']}: {e}")
            continue

    # Sort by utilization increase (most affected first)
    contingency_results.sort(key=lambda x: x['utilization_increase_pct'], reverse=True)

    return {
        'failed_line': {
            'line_id': failed_line_id,
            'line_name': str(failed_line['branch_name']),
            'flow_mw': round(float(failed_flow), 2),
            'bus0': int(failed_line['bus0']),
            'bus1': int(failed_line['bus1'])
        },
        'weather': {
            'temperature_c': weather.temperature_c,
            'wind_speed_ms': weather.wind_speed_ms,
            'source': weather.source
        },
        'summary': {
            'total_affected_lines': len(contingency_results),
            'overloaded_lines': overloaded_count,
            'critical_lines': critical_count,
            'warning_lines': warning_count,
            'redistributed_power_mw': round(float(failed_flow), 2)
        },
        'affected_lines': contingency_results
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
