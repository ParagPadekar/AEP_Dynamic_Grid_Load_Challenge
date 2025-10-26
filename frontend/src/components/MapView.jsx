/**
 * MapView Component
 * Interactive map visualization of Hawaii transmission grid
 * Shows transmission lines color-coded by status (Normal/Warning/Critical)
 */

import { useState, useEffect } from 'react';
import { MapContainer, TileLayer, GeoJSON, CircleMarker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import './MapView.css';

// Fix Leaflet default icon issue with Vite
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

// Component to fit map bounds to data
function FitBounds({ bounds }) {
  const map = useMap();
  useEffect(() => {
    if (bounds) {
      map.fitBounds(bounds, { padding: [50, 50] });
    }
  }, [bounds, map]);
  return null;
}

const MapView = ({ lines, weatherInfo }) => {
  const [geoJsonData, setGeoJsonData] = useState(null);
  const [busesData, setBusesData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [bounds, setBounds] = useState(null);

  // Hawaii center coordinates
  const center = [21.3099, -157.8581];

  // Debug logging
  useEffect(() => {
    console.log('MapView received:', lines?.length, 'lines');
    console.log('Weather info:', weatherInfo);
  }, [lines, weatherInfo]);

  useEffect(() => {
    loadGeoJSON();
  }, []);

  const loadGeoJSON = async () => {
    try {
      console.log('Loading GeoJSON files...');

      // Load lines GeoJSON
      const linesResponse = await fetch('/gis/lines.geojson');
      if (!linesResponse.ok) {
        throw new Error(`Failed to load lines.geojson: ${linesResponse.status}`);
      }
      const linesData = await linesResponse.json();
      console.log('Lines GeoJSON loaded:', linesData.features?.length, 'features');

      // Load buses GeoJSON
      const busesResponse = await fetch('/gis/buses.geojson');
      if (!busesResponse.ok) {
        throw new Error(`Failed to load buses.geojson: ${busesResponse.status}`);
      }
      const busesDataJson = await busesResponse.json();
      console.log('Buses GeoJSON loaded:', busesDataJson.features?.length, 'features');

      setGeoJsonData(linesData);
      setBusesData(busesDataJson);

      // Calculate bounds from GeoJSON
      if (linesData.features.length > 0) {
        const coords = [];
        linesData.features.forEach(feature => {
          if (feature.geometry.type === 'LineString') {
            feature.geometry.coordinates.forEach(coord => {
              coords.push([coord[1], coord[0]]); // [lat, lon]
            });
          }
        });

        if (coords.length > 0) {
          const lats = coords.map(c => c[0]);
          const lngs = coords.map(c => c[1]);
          setBounds([
            [Math.min(...lats), Math.min(...lngs)],
            [Math.max(...lats), Math.max(...lngs)]
          ]);
        }
      }

      console.log('GeoJSON loading complete. Bounds:', bounds);
      setLoading(false);
    } catch (err) {
      console.error('Error loading GeoJSON:', err);
      alert('Error loading map data: ' + err.message);
      setLoading(false);
    }
  };

  // Get line status data by line ID
  const getLineStatus = (lineId) => {
    const line = lines?.find(l => l.line_id === lineId);
    return line || null;
  };

  // Get color based on status
  const getStatusColor = (status) => {
    switch (status) {
      case 'Critical':
        return '#ef4444'; // Red
      case 'Warning':
        return '#f59e0b'; // Orange
      case 'Normal':
        return '#10b981'; // Green
      default:
        return '#6b7280'; // Gray
    }
  };

  // Style function for GeoJSON lines
  const lineStyle = (feature) => {
    const lineId = feature.properties.Name;
    const lineData = getLineStatus(lineId);
    const status = lineData?.status || 'Normal';
    const voltage = feature.properties.nomkv;

    return {
      color: getStatusColor(status),
      weight: voltage >= 138 ? 4 : 2.5,
      opacity: 0.8,
      lineJoin: 'round',
      lineCap: 'round',
    };
  };

  // Popup content for each line
  const onEachLine = (feature, layer) => {
    const lineId = feature.properties.Name;
    const lineData = getLineStatus(lineId);

    if (lineData) {
      const popupContent = `
        <div class="map-popup">
          <h4>${feature.properties.LineName}</h4>
          <div class="popup-details">
            <div class="popup-row">
              <span class="popup-label">Line ID:</span>
              <span class="popup-value">${lineId}</span>
            </div>
            <div class="popup-row">
              <span class="popup-label">Status:</span>
              <span class="popup-value status-${lineData.status.toLowerCase()}">${lineData.status}</span>
            </div>
            <div class="popup-row">
              <span class="popup-label">Utilization:</span>
              <span class="popup-value">${lineData.utilization_pct?.toFixed(1)}%</span>
            </div>
            <div class="popup-row">
              <span class="popup-label">Ampacity:</span>
              <span class="popup-value">${lineData.ampacity?.toFixed(0)} A</span>
            </div>
            <div class="popup-row">
              <span class="popup-label">Current Load:</span>
              <span class="popup-value">${lineData.predicted_current_a?.toFixed(0)} A</span>
            </div>
            <div class="popup-row">
              <span class="popup-label">Voltage:</span>
              <span class="popup-value">${feature.properties.nomkv} kV</span>
            </div>
            <div class="popup-row">
              <span class="popup-label">Conductor:</span>
              <span class="popup-value">${lineData.conductor}</span>
            </div>
          </div>
        </div>
      `;

      layer.bindPopup(popupContent);

      // Highlight on hover
      layer.on('mouseover', function () {
        this.setStyle({
          weight: voltage >= 138 ? 6 : 4,
          opacity: 1
        });
      });

      layer.on('mouseout', function () {
        this.setStyle({
          weight: voltage >= 138 ? 4 : 2.5,
          opacity: 0.8
        });
      });
    }
  };

  // Get summary statistics
  const getSummary = () => {
    if (!lines) return { critical: 0, warning: 0, normal: 0 };

    return {
      critical: lines.filter(l => l.status === 'Critical').length,
      warning: lines.filter(l => l.status === 'Warning').length,
      normal: lines.filter(l => l.status === 'Normal').length,
    };
  };

  const summary = getSummary();

  if (loading) {
    return (
      <div className="map-loading">
        <div className="loading-spinner"></div>
        <p>Loading transmission grid map...</p>
      </div>
    );
  }

  return (
    <div className="map-view">
      <div className="map-header">
        <h3>🗺️ Hawaii Transmission Grid - Live Status Map</h3>
        {weatherInfo && (
          <div className="map-weather-info">
            <span>🌡️ {weatherInfo.temperature_c}°C</span>
            <span>💨 {weatherInfo.wind_speed_ms} m/s</span>
            <span>{weatherInfo.description || weatherInfo.source}</span>
          </div>
        )}
      </div>

      <div className="map-summary">
        <div className="summary-item critical">
          <span className="summary-dot"></span>
          <span className="summary-label">Critical:</span>
          <span className="summary-value">{summary.critical}</span>
        </div>
        <div className="summary-item warning">
          <span className="summary-dot"></span>
          <span className="summary-label">Warning:</span>
          <span className="summary-value">{summary.warning}</span>
        </div>
        <div className="summary-item normal">
          <span className="summary-dot"></span>
          <span className="summary-label">Normal:</span>
          <span className="summary-value">{summary.normal}</span>
        </div>
      </div>

      <div className="map-container-wrapper">
        <MapContainer
          center={center}
          zoom={10}
          className="leaflet-map"
          zoomControl={true}
          scrollWheelZoom={true}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {geoJsonData && (
            <GeoJSON
              data={geoJsonData}
              style={lineStyle}
              onEachFeature={onEachLine}
            />
          )}

          {busesData && busesData.features.map((bus, idx) => {
            // Filter unique buses by name
            const busName = bus.properties.BusName;
            const isFirstOccurrence = busesData.features.findIndex(
              b => b.properties.BusName === busName
            ) === idx;

            if (isFirstOccurrence) {
              const [lon, lat] = bus.geometry.coordinates;
              return (
                <CircleMarker
                  key={`bus-${idx}`}
                  center={[lat, lon]}
                  radius={5}
                  fillColor="#333"
                  color="#fff"
                  weight={2}
                  opacity={1}
                  fillOpacity={0.8}
                >
                  <Popup>
                    <div className="bus-popup">
                      <strong>{busName}</strong>
                      <div>{bus.properties.kV} kV</div>
                    </div>
                  </Popup>
                </CircleMarker>
              );
            }
            return null;
          })}

          {bounds && <FitBounds bounds={bounds} />}
        </MapContainer>
      </div>

      <div className="map-legend">
        <h4>Legend</h4>
        <div className="legend-items">
          <div className="legend-item">
            <div className="legend-line" style={{ backgroundColor: '#10b981' }}></div>
            <span>Normal (&lt;80%)</span>
          </div>
          <div className="legend-item">
            <div className="legend-line" style={{ backgroundColor: '#f59e0b' }}></div>
            <span>Warning (80-95%)</span>
          </div>
          <div className="legend-item">
            <div className="legend-line" style={{ backgroundColor: '#ef4444' }}></div>
            <span>Critical (≥95%)</span>
          </div>
          <div className="legend-item">
            <div className="legend-circle"></div>
            <span>Substation</span>
          </div>
          <div className="legend-note">
            <small>Line thickness indicates voltage level (138kV vs 69kV)</small>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MapView;
