/**
 * Dashboard Component
 * Main overview of all transmission lines with status indicators
 */

import { useState, useEffect } from 'react';
import apiService from '../services/api';
import MapView from './MapView';
import './Dashboard.css';

const Dashboard = ({ onLineSelect, selectedScenario, customWeather }) => {
  const [lines, setLines] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [summary, setSummary] = useState(null);
  const [weatherInfo, setWeatherInfo] = useState(null);
  const [viewMode, setViewMode] = useState('map'); // 'map' or 'grid'

  useEffect(() => {
    fetchData();
  }, [selectedScenario, customWeather]);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Determine weather source
      const weatherSource = customWeather ? 'manual' : 'scenario';

      // Fetch all lines with weather (get ALL for map view)
      const data = await apiService.getAllLinesWithWeather(
        weatherSource,
        selectedScenario,
        null, // Get all lines for map visualization
        customWeather
      );

      setLines(data.lines || []);
      setWeatherInfo(data.weather || null);

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getStatusClass = (status) => {
    switch (status) {
      case 'Critical':
        return 'status-critical';
      case 'Warning':
        return 'status-warning';
      case 'Normal':
        return 'status-normal';
      default:
        return '';
    }
  };

  const getStatusEmoji = (status) => {
    switch (status) {
      case 'Critical':
        return '🔴';
      case 'Warning':
        return '⚠️';
      case 'Normal':
        return '✅';
      default:
        return '❓';
    }
  };

  const statusCounts = lines.reduce(
    (acc, line) => {
      acc[line.status] = (acc[line.status] || 0) + 1;
      return acc;
    },
    { Critical: 0, Warning: 0, Normal: 0 }
  );

  if (loading) {
    return <div className="dashboard-loading">Loading transmission lines...</div>;
  }

  if (error) {
    return (
      <div className="dashboard-error">
        <h3>Error loading data</h3>
        <p>{error}</p>
        <button onClick={fetchData}>Retry</button>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h2>Transmission Lines Overview</h2>
        <div className="dashboard-controls">
          <div className="view-toggle">
            <button
              className={`toggle-btn ${viewMode === 'map' ? 'active' : ''}`}
              onClick={() => setViewMode('map')}
            >
              🗺️ Map View
            </button>
            <button
              className={`toggle-btn ${viewMode === 'grid' ? 'active' : ''}`}
              onClick={() => setViewMode('grid')}
            >
              📊 Grid View
            </button>
          </div>
          <button onClick={fetchData} className="refresh-button">
            🔄 Refresh
          </button>
        </div>
      </div>

      {/* Status Summary Cards */}
      <div className="status-summary">
        <div className="summary-card">
          <div className="summary-number">{lines.length}</div>
          <div className="summary-label">Total Lines</div>
        </div>
        <div className="summary-card status-critical">
          <div className="summary-number">{statusCounts.Critical || 0}</div>
          <div className="summary-label">🔴 Critical</div>
        </div>
        <div className="summary-card status-warning">
          <div className="summary-number">{statusCounts.Warning || 0}</div>
          <div className="summary-label">⚠️ Warning</div>
        </div>
        <div className="summary-card status-normal">
          <div className="summary-number">{statusCounts.Normal || 0}</div>
          <div className="summary-label">✅ Normal</div>
        </div>
      </div>

      {/* Map or Grid View */}
      {viewMode === 'map' ? (
        <MapView lines={lines} weatherInfo={weatherInfo} />
      ) : (
        /* Lines Grid */
        <div className="lines-grid">
        {lines.map((line) => (
          <div
            key={line.line_id}
            className={`line-card ${getStatusClass(line.status)}`}
            onClick={() => onLineSelect && onLineSelect(line.line_id)}
          >
            <div className="line-card-header">
              <div className="line-id">{line.line_id}</div>
              <div className="line-status">{getStatusEmoji(line.status)}</div>
            </div>

            <div className="line-card-body">
              <div className="line-name">{line.line_name.substring(0, 40)}...</div>

              <div className="line-stats">
                <div className="stat">
                  <span className="stat-label">Static Rating</span>
                  <span className="stat-value">{line.static_rating_mva?.toFixed(1) || 'N/A'} MVA</span>
                </div>
                <div className="stat">
                  <span className="stat-label">Dynamic Rating</span>
                  <span className="stat-value" style={{ color: line.capacity_increase_pct > 0 ? '#10b981' : undefined }}>
                    {line.ampacity_mva?.toFixed(1) || 'N/A'} MVA
                  </span>
                </div>
              </div>

              <div className="utilization-bar-container">
                <div className="utilization-label">
                  Utilization: {line.utilization_pct?.toFixed(1) || '0'}% of static rating
                </div>
                <div className="utilization-bar">
                  <div
                    className={`utilization-fill ${getStatusClass(line.status)}`}
                    style={{ width: `${Math.min(line.utilization_pct || 0, 100)}%` }}
                  ></div>
                </div>
              </div>

              <div className="line-details">
                <div className="detail-item">
                  <span>Current Load:</span>
                  <span>{line.predicted_load_mw?.toFixed(1) || 'N/A'} MW</span>
                </div>
                <div className="detail-item">
                  <span>DLR Gain:</span>
                  <span style={{ color: line.capacity_increase_pct > 0 ? '#10b981' : '#6b7280' }}>
                    {line.capacity_increase_pct > 0 ? '+' : ''}{line.capacity_increase_pct?.toFixed(1) || '0'}%
                  </span>
                </div>
              </div>
            </div>
          </div>
        ))}
        </div>
      )}

      {lines.length === 0 && (
        <div className="no-data">
          No transmission lines found. Check backend connection.
        </div>
      )}
    </div>
  );
};

export default Dashboard;
