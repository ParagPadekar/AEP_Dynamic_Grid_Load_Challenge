"""
FastAPI Backend for IEEE 738 Dynamic Line Rating System
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
import pandas as pd
import numpy as np
import os
import sys

# Import our modules
from ieee738 import IEEE738Calculator, get_conductor_params
from load_model import LoadPredictor, SimpleLoadForecaster

# Initialize FastAPI app
app = FastAPI(
    title="IEEE 738 Dynamic Line Rating API",
    description="Real-time transmission line ampacity calculation and overload detection",
    version="1.0.0"
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global data storage
lines_data = None
conductor_library = None
load_predictor = None


# Pydantic models for API
class AmpacityRequest(BaseModel):
    """Request model for ampacity calculation"""
    line_id: str = Field(..., description="Line identifier (e.g., L0, L1)")
    temp_ambient_c: float = Field(..., ge=-50, le=60, description="Ambient temperature (°C)")
    wind_speed_ms: float = Field(..., ge=0, le=30, description="Wind speed (m/s)")
    temp_conductor_max_c: float = Field(75, ge=50, le=100, description="Max conductor temp (°C)")
    solar_altitude: float = Field(45, ge=0, le=90, description="Solar altitude angle (degrees)")
    wind_angle_deg: float = Field(90, ge=0, le=180, description="Wind angle (degrees)")


class AmpacityResponse(BaseModel):
    """Response model for ampacity calculation"""
    line_id: str
    line_name: str
    conductor: str
    voltage_kv: float
    ampacity: float
    ampacity_mva: float
    static_rating_mva: float
    predicted_load_mw: float
    predicted_current_a: float
    utilization_pct: float
    status: str
    details: Optional[Dict] = None


class LoadPredictionRequest(BaseModel):
    """Request model for load prediction"""
    line_id: str
    timestamp: Optional[str] = None
    hours_ahead: int = Field(1, ge=1, le=48)


class LoadPredictionResponse(BaseModel):
    """Response model for load prediction"""
    line_id: str
    predictions: List[Dict]


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    lines_loaded: int
    timestamp: str


# Utility functions
def load_data():
    """Load transmission line data from CSV files"""
    global lines_data, conductor_library, load_predictor

    # Path to data files
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'osu_hackathon', 'hawaii40_osu', 'csv')
    conductor_dir = os.path.join(os.path.dirname(__file__), '..', 'osu_hackathon', 'ieee738')

    # Load lines data
    lines_path = os.path.join(data_dir, 'lines.csv')
    if not os.path.exists(lines_path):
        raise FileNotFoundError(f"Lines data not found at {lines_path}")

    lines_data = pd.read_csv(lines_path)

    # Load buses to get voltage levels
    buses_path = os.path.join(data_dir, 'buses.csv')
    buses_data = pd.read_csv(buses_path)

    # Merge to get voltage info
    lines_data = lines_data.merge(
        buses_data[['name', 'v_nom']],
        left_on='bus0',
        right_on='name',
        how='left',
        suffixes=('', '_bus')
    )
    lines_data.rename(columns={'v_nom': 'voltage_kv'}, inplace=True)
    lines_data.drop(columns=['name_bus'], inplace=True, errors='ignore')

    # Load conductor library
    conductor_path = os.path.join(conductor_dir, 'conductor_library.csv')
    if os.path.exists(conductor_path):
        conductor_library = pd.read_csv(conductor_path)

    # Initialize load predictor with baseline loads from line flows
    load_predictor = LoadPredictor()

    # Set baseline loads based on static ratings (rough estimate)
    for _, line in lines_data.iterrows():
        # Use s_nom (MVA rating) as rough guide for baseline load
        baseline_mw = line['s_nom'] * 0.7  # Assume 70% loading as baseline
        load_predictor.set_baseline_load(line['name'], baseline_mw)

    print(f"Loaded {len(lines_data)} transmission lines")
    return lines_data


def determine_status(utilization_pct: float) -> str:
    """Determine line status based on utilization"""
    if utilization_pct >= 95:
        return "Critical"
    elif utilization_pct >= 80:
        return "Warning"
    else:
        return "Normal"


def calculate_mva_from_current(current_a: float, voltage_kv: float) -> float:
    """Convert current to MVA"""
    return (np.sqrt(3) * voltage_kv * current_a) / 1000


# Startup event
@app.on_event("startup")
async def startup_event():
    """Load data on startup"""
    try:
        load_data()
        print("Data loaded successfully")
    except Exception as e:
        print(f"Error loading data: {e}")
        # Continue anyway for development


# API Endpoints

@app.get("/", response_model=Dict)
async def root():
    """Root endpoint"""
    return {
        "message": "IEEE 738 Dynamic Line Rating API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "calculate_ampacity": "/calculate_ampacity",
            "get_all_lines": "/get_all_lines",
            "predict_load": "/predict_load"
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    if lines_data is None:
        raise HTTPException(status_code=503, detail="Data not loaded")

    return HealthResponse(
        status="healthy",
        lines_loaded=len(lines_data),
        timestamp=datetime.now().isoformat()
    )


@app.post("/calculate_ampacity", response_model=AmpacityResponse)
async def calculate_ampacity(request: AmpacityRequest):
    """
    Calculate ampacity for a specific transmission line.

    Uses IEEE 738 thermal balance equation with real-time weather data.
    """
    if lines_data is None:
        raise HTTPException(status_code=503, detail="Data not loaded")

    # Find the line
    line = lines_data[lines_data['name'] == request.line_id]
    if line.empty:
        raise HTTPException(status_code=404, detail=f"Line {request.line_id} not found")

    line = line.iloc[0]

    # Get conductor parameters
    conductor_name = line['conductor']
    conductor_params = get_conductor_params(conductor_name)

    # Create IEEE 738 calculator
    calculator = IEEE738Calculator(
        conductor_diameter_m=conductor_params['diameter_m'],
        resistance_25C=conductor_params['R_ohm_per_m'],
        emissivity=0.5,
        absorptivity=0.5,
        resistance_temp_coeff=conductor_params['temp_coeff']
    )

    # Calculate ampacity
    ampacity_details = calculator.calculate_ampacity_detailed(
        temp_ambient_c=request.temp_ambient_c,
        wind_speed_ms=request.wind_speed_ms,
        temp_conductor_max_c=request.temp_conductor_max_c,
        solar_altitude=request.solar_altitude,
        wind_angle_deg=request.wind_angle_deg
    )

    ampacity_amps = ampacity_details['ampacity']
    voltage_kv = line['voltage_kv']
    ampacity_mva = calculate_mva_from_current(ampacity_amps, voltage_kv)

    # Predict load
    predicted_current_data = load_predictor.predict_line_current(
        request.line_id,
        voltage_kv,
        timestamp=datetime.now()
    )

    predicted_current = predicted_current_data['predicted_current_a']
    predicted_load_mw = predicted_current_data['predicted_load_mw']

    # Calculate utilization
    utilization_pct = (predicted_current / ampacity_amps * 100) if ampacity_amps > 0 else 0

    # Determine status
    status = determine_status(utilization_pct)

    return AmpacityResponse(
        line_id=request.line_id,
        line_name=line['branch_name'],
        conductor=conductor_name,
        voltage_kv=voltage_kv,
        ampacity=ampacity_amps,
        ampacity_mva=ampacity_mva,
        static_rating_mva=line['s_nom'],
        predicted_load_mw=predicted_load_mw,
        predicted_current_a=predicted_current,
        utilization_pct=utilization_pct,
        status=status,
        details={
            "temp_ambient_c": request.temp_ambient_c,
            "wind_speed_ms": request.wind_speed_ms,
            "temp_conductor_max_c": request.temp_conductor_max_c,
            "Qc_convective": ampacity_details['Qc_convective'],
            "Qr_radiative": ampacity_details['Qr_radiative'],
            "Qs_solar": ampacity_details['Qs_solar'],
            "Q_net": ampacity_details['Q_net']
        }
    )


@app.get("/get_all_lines", response_model=List[AmpacityResponse])
async def get_all_lines(
    temp_ambient_c: float = 30,
    wind_speed_ms: float = 2.0,
    temp_conductor_max_c: float = 75,
    solar_altitude: float = 45,
    limit: Optional[int] = None
):
    """
    Get ampacity and status for all transmission lines.

    Default conditions: 30°C ambient, 2 m/s wind, 75°C conductor limit
    """
    if lines_data is None:
        raise HTTPException(status_code=503, detail="Data not loaded")

    results = []
    lines_to_process = lines_data.head(limit) if limit else lines_data

    for _, line in lines_to_process.iterrows():
        try:
            # Get conductor parameters
            conductor_name = line['conductor']
            conductor_params = get_conductor_params(conductor_name)

            # Create calculator
            calculator = IEEE738Calculator(
                conductor_diameter_m=conductor_params['diameter_m'],
                resistance_25C=conductor_params['R_ohm_per_m'],
                emissivity=0.5,
                absorptivity=0.5,
                resistance_temp_coeff=conductor_params['temp_coeff']
            )

            # Calculate ampacity
            ampacity_details = calculator.calculate_ampacity_detailed(
                temp_ambient_c=temp_ambient_c,
                wind_speed_ms=wind_speed_ms,
                temp_conductor_max_c=temp_conductor_max_c,
                solar_altitude=solar_altitude,
                wind_angle_deg=90
            )

            ampacity_amps = ampacity_details['ampacity']
            voltage_kv = line['voltage_kv']
            ampacity_mva = calculate_mva_from_current(ampacity_amps, voltage_kv)

            # Predict load
            predicted_current_data = load_predictor.predict_line_current(
                line['name'],
                voltage_kv,
                timestamp=datetime.now()
            )

            predicted_current = predicted_current_data['predicted_current_a']
            predicted_load_mw = predicted_current_data['predicted_load_mw']

            # Calculate utilization
            utilization_pct = (predicted_current / ampacity_amps * 100) if ampacity_amps > 0 else 0

            # Determine status
            status = determine_status(utilization_pct)

            results.append(AmpacityResponse(
                line_id=line['name'],
                line_name=line['branch_name'],
                conductor=conductor_name,
                voltage_kv=voltage_kv,
                ampacity=ampacity_amps,
                ampacity_mva=ampacity_mva,
                static_rating_mva=line['s_nom'],
                predicted_load_mw=predicted_load_mw,
                predicted_current_a=predicted_current,
                utilization_pct=utilization_pct,
                status=status
            ))

        except Exception as e:
            print(f"Error processing line {line['name']}: {e}")
            continue

    return results


@app.post("/predict_load", response_model=LoadPredictionResponse)
async def predict_load(request: LoadPredictionRequest):
    """
    Predict load for a transmission line over time.
    """
    if lines_data is None or load_predictor is None:
        raise HTTPException(status_code=503, detail="Data not loaded")

    # Find the line
    line = lines_data[lines_data['name'] == request.line_id]
    if line.empty:
        raise HTTPException(status_code=404, detail=f"Line {request.line_id} not found")

    line = line.iloc[0]
    voltage_kv = line['voltage_kv']

    # Parse timestamp
    if request.timestamp:
        start_time = datetime.fromisoformat(request.timestamp)
    else:
        start_time = datetime.now()

    # Generate predictions
    predictions = []
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

    return LoadPredictionResponse(
        line_id=request.line_id,
        predictions=predictions
    )


@app.get("/lines/summary")
async def get_lines_summary():
    """Get summary statistics of all lines"""
    if lines_data is None:
        raise HTTPException(status_code=503, detail="Data not loaded")

    return {
        "total_lines": len(lines_data),
        "voltage_levels": lines_data['voltage_kv'].unique().tolist(),
        "conductors": lines_data['conductor'].unique().tolist(),
        "avg_rating_mva": float(lines_data['s_nom'].mean()),
        "max_rating_mva": float(lines_data['s_nom'].max()),
        "min_rating_mva": float(lines_data['s_nom'].min())
    }


# Run with: uvicorn main:app --reload --host 0.0.0.0 --port 8000
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
