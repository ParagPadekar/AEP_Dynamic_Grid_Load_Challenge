# IEEE 738 Dynamic Line Rating - Backend API

FastAPI backend for real-time transmission line ampacity calculation and overload detection.

## Features

- **IEEE 738 Thermal Calculations**: Real-time ampacity calculation based on ambient temperature, wind speed, and conductor properties
- **Load Prediction**: Time-based load forecasting using daily load profiles
- **Overload Detection**: Automatic status classification (Normal/Warning/Critical)
- **77 Transmission Lines**: Hawaii 40-bus test case with real conductor data
- **REST API**: Fast, documented endpoints with automatic OpenAPI/Swagger docs

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Start the Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The server will start at `http://localhost:8000`

### 3. View API Documentation

Open your browser to:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### Health Check
```bash
GET /health
```

Returns server status and number of lines loaded.

**Example**:
```bash
curl http://localhost:8000/health
```

**Response**:
```json
{
  "status": "healthy",
  "lines_loaded": 77,
  "timestamp": "2025-10-25T12:47:41.258931"
}
```

---

### Calculate Ampacity
```bash
POST /calculate_ampacity
```

Calculate real-time ampacity for a specific transmission line.

**Request Body**:
```json
{
  "line_id": "L0",
  "temp_ambient_c": 35,
  "wind_speed_ms": 1.5,
  "temp_conductor_max_c": 75,
  "solar_altitude": 45,
  "wind_angle_deg": 90
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/calculate_ampacity \
  -H "Content-Type: application/json" \
  -d '{
    "line_id": "L0",
    "temp_ambient_c": 35,
    "wind_speed_ms": 1.5,
    "temp_conductor_max_c": 75
  }'
```

**Response**:
```json
{
  "line_id": "L0",
  "line_name": "ALOHA138 (1) TO HONOLULU138 (5) CKT 1",
  "conductor": "795 ACSR 26/7 DRAKE",
  "voltage_kv": 138.0,
  "ampacity": 847.29,
  "ampacity_mva": 202.52,
  "static_rating_mva": 228.0,
  "predicted_load_mw": 164.10,
  "predicted_current_a": 722.67,
  "utilization_pct": 85.29,
  "status": "Warning",
  "details": {
    "temp_ambient_c": 35.0,
    "wind_speed_ms": 1.5,
    "temp_conductor_max_c": 75.0,
    "Qc_convective": 96.36,
    "Qr_radiative": 14.15,
    "Qs_solar": 9.90,
    "Q_net": 100.62
  }
}
```

**Status Values**:
- `Normal`: Utilization < 80%
- `Warning`: Utilization 80-95%
- `Critical`: Utilization >= 95%

---

### Get All Lines
```bash
GET /get_all_lines?temp_ambient_c=30&wind_speed_ms=2.0&limit=10
```

Get ampacity and status for all transmission lines.

**Query Parameters**:
- `temp_ambient_c` (default: 30): Ambient temperature in °C
- `wind_speed_ms` (default: 2.0): Wind speed in m/s
- `temp_conductor_max_c` (default: 75): Max conductor temperature in °C
- `solar_altitude` (default: 45): Solar altitude angle in degrees
- `limit` (optional): Limit number of lines returned

**Example**:
```bash
curl "http://localhost:8000/get_all_lines?limit=5"
```

**Response**: Array of line data (same format as `/calculate_ampacity`)

---

### Predict Load
```bash
POST /predict_load
```

Predict load for a transmission line over time.

**Request Body**:
```json
{
  "line_id": "L0",
  "timestamp": "2025-10-25T14:00:00",
  "hours_ahead": 24
}
```

**Example**:
```bash
curl -X POST http://localhost:8000/predict_load \
  -H "Content-Type: application/json" \
  -d '{
    "line_id": "L0",
    "hours_ahead": 6
  }'
```

**Response**:
```json
{
  "line_id": "L0",
  "predictions": [
    {
      "timestamp": "2025-10-25T12:00:00",
      "hour": 12,
      "predicted_load_mw": 161.27,
      "predicted_current_a": 710.2
    },
    {
      "timestamp": "2025-10-25T13:00:00",
      "hour": 13,
      "predicted_load_mw": 163.45,
      "predicted_current_a": 719.8
    }
  ]
}
```

---

### Lines Summary
```bash
GET /lines/summary
```

Get summary statistics of all transmission lines.

**Example**:
```bash
curl http://localhost:8000/lines/summary
```

**Response**:
```json
{
  "total_lines": 77,
  "voltage_levels": [138.0, 69.0],
  "conductors": ["795 ACSR 26/7 DRAKE", "556.5 ACSR 26/7 DOVE", ...],
  "avg_rating_mva": 153.45,
  "max_rating_mva": 278.0,
  "min_rating_mva": 70.0
}
```

## IEEE 738 Thermal Model

The ampacity calculation uses the IEEE 738 heat balance equation:

```
I²R(Tc) = Qc + Qr - Qs
```

Where:
- **I**: Current (amperes)
- **R(Tc)**: Conductor resistance at temperature Tc
- **Qc**: Convective heat loss (cooling)
- **Qr**: Radiative heat loss (cooling)
- **Qs**: Solar heat gain (heating)

### Heat Balance Components

1. **Convective Cooling (Qc)**: Forced and natural convection based on wind speed and temperature difference
2. **Radiative Cooling (Qr)**: Stefan-Boltzmann law for thermal radiation
3. **Solar Heating (Qs)**: Solar radiation absorption based on sun angle and conductor properties

## Load Prediction Model

Simple time-based forecasting using:
- **Daily Load Profile**: Typical 24-hour pattern with morning ramp, peak hours, and evening decline
- **Baseline Scaling**: Each line has a baseline load (70% of static rating)
- **Time-of-Day Factors**: Hour-specific multipliers (0.58-1.0)

Load profile pattern:
- **Night (0-6)**: 60-70% of peak
- **Morning (6-9)**: Ramp to 90%
- **Midday (9-17)**: 95-100% peak
- **Evening (17-20)**: 100% peak
- **Late evening (20-24)**: Decline to 70%

## Data Sources

- **Lines Data**: `osu_hackathon/hawaii40_osu/csv/lines.csv` (77 lines)
- **Buses Data**: `osu_hackathon/hawaii40_osu/csv/buses.csv` (40 buses)
- **Conductor Library**: `osu_hackathon/ieee738/conductor_library.csv` (9 conductor types)

### Conductor Types
- 336.4 ACSR 30/7 ORIOLE
- 556.5 ACSR 26/7 DOVE
- 795 ACSR 26/7 DRAKE
- 954 ACSR 54/7 CARDINAL
- 1272 ACSR 45/7 BITTERN
- 1590 ACSR 54/19 FALCON

### Voltage Levels
- **138 kV**: High voltage transmission
- **69 kV**: Sub-transmission

## Project Structure

```
backend/
├── main.py              # FastAPI application and endpoints
├── ieee738.py           # IEEE 738 ampacity calculator
├── load_model.py        # Load prediction logic
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Development

### Run Tests
```bash
# Test IEEE 738 calculator
python ieee738.py

# Test load predictor
python load_model.py
```

### Enable Hot Reload
```bash
uvicorn main:app --reload
```

### Change Port
```bash
uvicorn main:app --port 8080
```

## Next Steps

After the backend is running, you can:

1. **Test the API**: Use the Swagger UI at http://localhost:8000/docs
2. **Build the Frontend**: Create a React dashboard to visualize the data
3. **Add Weather Integration**: Connect to real weather APIs for live data
4. **Enhance Predictions**: Use machine learning for better load forecasting
5. **Add Alerts**: Email/SMS notifications for critical overload conditions

## Example Use Cases

### Scenario 1: Hot Summer Day
```bash
curl -X POST http://localhost:8000/calculate_ampacity \
  -H "Content-Type: application/json" \
  -d '{
    "line_id": "L0",
    "temp_ambient_c": 40,
    "wind_speed_ms": 0.5,
    "temp_conductor_max_c": 75
  }'
```
Result: Lower ampacity due to high temp and low wind → May show "Critical" status

### Scenario 2: Optimal Conditions
```bash
curl -X POST http://localhost:8000/calculate_ampacity \
  -H "Content-Type: application/json" \
  -d '{
    "line_id": "L0",
    "temp_ambient_c": 20,
    "wind_speed_ms": 3.0,
    "temp_conductor_max_c": 75
  }'
```
Result: Higher ampacity due to cool temp and good wind → Likely "Normal" status

## Troubleshooting

### Server won't start
- Check if port 8000 is already in use
- Verify all dependencies are installed: `pip list`
- Check data files exist in `../osu_hackathon/hawaii40_osu/csv/`

### Import errors
- Ensure you're in the `backend/` directory
- Reinstall requirements: `pip install -r requirements.txt`

### No data loaded
- Verify the relative path to data files is correct
- Check console output for specific error messages

## License

Built for HackOHIO 2024 Hackathon
