# IEEE 738 Dynamic Line Rating System

> Real-time transmission line capacity monitoring with weather-based calculations for Hawaii's 40-bus power grid

[![Built for HackOHIO 2024](https://img.shields.io/badge/Built%20for-HackOHIO%202024-8b5cf6)](https://hack.osu.edu/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

## 🌟 Overview

This Dynamic Line Rating (DLR) system uses the **IEEE 738-2012 standard** to calculate real-time transmission line capacity based on weather conditions. Unlike traditional static ratings, our system provides:

- ⚡ **Real-time ampacity calculations** based on temperature, wind, solar radiation, and humidity
- 🗺️ **Interactive GIS map** showing Hawaii's transmission grid with color-coded status
- 📊 **Comprehensive analytics** with scenario comparisons and 24-hour load forecasts
- 🌡️ **Weather-sensitive load modeling** that accounts for A/C demand in extreme heat
- 🎛️ **Custom weather controls** for testing any conditions

## 🚀 Features

### Core Functionality
- **IEEE 738 Thermal Calculations**: Industry-standard ampacity calculations
- **77 Transmission Lines**: Complete Hawaii 40-bus system analysis
- **7 Weather Scenarios**: Pre-configured scenarios from optimal to extreme heat
- **Weather-Sensitive Loads**: Load increases with temperature (realistic A/C demand)
- **Static vs Dynamic Ratings**: Shows both conservative and real-time ratings

### User Interface
- **Interactive Map**: Leaflet-based GIS visualization of Hawaii's grid
- **Dashboard View**: Card-based overview with utilization metrics
- **Table View**: Sortable, filterable table of all lines
- **Charts & Analysis**: Multi-scenario comparisons, load forecasts, utilization trends
- **Custom Weather Input**: Sliders for manual weather parameter control

### Technical Highlights
- **Backend**: FastAPI (Python) with Pydantic validation
- **Frontend**: React + Vite with Leaflet maps and Recharts
- **Data**: Pandas for CSV processing, NumPy for calculations
- **Real-time**: All calculations happen in <1 second

## 📦 Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **NumPy & Pandas** - Data processing and calculations
- **IEEE 738** - Thermal rating standard implementation
- **Pydantic** - Data validation
- **Uvicorn** - ASGI server

### Frontend
- **React 18** - UI framework
- **Vite** - Build tool and dev server
- **Leaflet** - Interactive maps
- **Recharts** - Data visualization
- **Axios** - HTTP client

## 🏃 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- npm or yarn

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
python main_weather.py
```

Backend runs on http://localhost:8000

API Docs: http://localhost:8000/docs

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on http://localhost:5173

## 🌐 Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

### Recommended Setup for Demos:
- **Frontend**: Vercel (blazing fast, no cold starts)
- **Backend**: Render.com (free tier, reliable)

Quick deploy:
1. Push to GitHub
2. Connect to Render/Vercel
3. Auto-deploys in ~10 minutes

## 📖 How It Works

### IEEE 738 Thermal Balance

The system calculates ampacity using the thermal balance equation:

```
I²R(Tc) = Qc + Qr - Qs
```

Where:
- **Qc**: Convective cooling (wind speed dependent)
- **Qr**: Radiative cooling (temperature dependent)
- **Qs**: Solar heating (solar altitude dependent)
- **I**: Maximum current (ampacity)
- **R(Tc)**: Resistance at conductor temperature

### Weather Impact

**Temperature**: Higher ambient temperature reduces cooling capacity
- 30°C → 243 MVA capacity
- 42°C → 135 MVA capacity (45% reduction!)

**Wind Speed**: Higher wind improves convective cooling
- 0.5 m/s → Low cooling
- 5.5 m/s → High cooling (+20-30% capacity)

**Load Modeling**: Weather affects electricity demand
- Hot weather → A/C load increases (2.5-3.5% per degree above 22°C)
- High humidity → Amplifies perceived temperature
- Solar radiation → Increases cooling load during daytime

### Critical Overloads

The system correctly identifies critical overloads during extreme heat:
- **Ampacity drops** (lines can't cool efficiently)
- **Load increases** (A/C demand skyrockets)
- **Result**: Utilization exceeds 100% → **CRITICAL** status

## 🗂️ Project Structure

```
HackOHIO/
├── backend/
│   ├── main_weather.py         # Main FastAPI app
│   ├── ieee738.py              # IEEE 738 calculations
│   ├── weather_service.py      # Weather scenarios & API
│   ├── load_model.py           # Weather-sensitive load predictor
│   ├── data/
│   │   └── hawaii40_lines.csv  # 77 transmission lines
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard.jsx   # Main dashboard
│   │   │   ├── MapView.jsx     # GIS map
│   │   │   ├── TableView.jsx   # Data table
│   │   │   ├── Charts.jsx      # Analytics
│   │   │   └── WeatherControls.jsx
│   │   ├── services/
│   │   │   └── api.js          # API service layer
│   │   └── App.jsx
│   ├── public/gis/             # GeoJSON data
│   └── package.json
├── render.yaml                 # Render deployment config
├── DEPLOYMENT.md               # Deployment guide
└── README.md
```

## 📊 API Endpoints

### Main Endpoints

- `GET /` - Welcome message
- `GET /health` - Health check
- `GET /weather/scenarios` - List all weather scenarios
- `POST /calculate_with_weather` - Calculate single line rating
- `GET /calculate_all_with_weather` - Calculate all lines (supports manual weather)
- `POST /compare_scenarios` - Compare line across multiple scenarios
- `POST /predict_load` - Get 24-hour load forecast

### Example Request

```bash
curl -X GET "http://localhost:8000/calculate_all_with_weather?weather_source=manual&temp_ambient_c=42&wind_speed_ms=0.5&solar_altitude=75&humidity_pct=65"
```

## 🎯 Use Cases

1. **Grid Operators**: Real-time capacity monitoring
2. **Planners**: Scenario analysis for grid expansion
3. **Researchers**: Weather impact studies
4. **Utilities**: DLR implementation validation
5. **Regulators**: Compliance verification (NERC/FERC standards)

## 🏆 Hackathon Demo Tips

1. **Start with Map View**: Shows the WOW factor immediately
2. **Switch to Extreme Heat**: Demonstrates critical overloads
3. **Show Custom Weather**: Let judges try different conditions
4. **Compare Scenarios**: Charts tab shows all scenarios side-by-side
5. **Explain Industry Impact**: DLR can increase grid capacity 10-30% without new infrastructure

## 🤝 Contributing

This is a hackathon project built in 20 hours! Contributions welcome for:
- Additional weather data sources (NOAA, OpenWeatherMap integration)
- More conductor types
- Historical data analysis
- Machine learning load forecasting
- Mobile responsive design improvements

## 📄 License

MIT License - see [LICENSE](LICENSE) file

## 🙏 Acknowledgments

- **IEEE 738-2012** standard for thermal rating calculations
- **OSU Hackathon** for providing the Hawaii 40-bus system data
- **NERC/FERC** for industry standards guidance
- Built with ❤️ for HackOHIO 2024

## 📧 Contact

Questions? Reach out during the hackathon or open an issue!

---

**Built for HackOHIO 2024** | **IEEE 738 Dynamic Line Rating System**
