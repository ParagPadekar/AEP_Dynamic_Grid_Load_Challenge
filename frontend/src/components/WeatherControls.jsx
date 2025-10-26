/**
 * WeatherControls Component
 * Allows user to select weather scenarios and view weather information
 */

import { useState, useEffect } from 'react';
import apiService from '../services/api';
import './WeatherControls.css';

const WeatherControls = ({ onScenarioChange, currentScenario }) => {
  const [scenarios, setScenarios] = useState([]);
  const [loading, setLoading] = useState(true);
  const [weatherInfo, setWeatherInfo] = useState(null);
  const [customMode, setCustomMode] = useState(false);
  const [customWeather, setCustomWeather] = useState({
    temperature: 30,
    windSpeed: 2.0,
    solarAltitude: 45,
    humidity: 70
  });

  useEffect(() => {
    fetchScenarios();
  }, []);

  const fetchScenarios = async () => {
    try {
      const data = await apiService.getScenarios();
      setScenarios(data);
      setLoading(false);
    } catch (err) {
      console.warn('Weather scenarios not available (requires main_weather.py backend)');
      // Fallback: Use default scenario list for display only
      setScenarios([
        {
          scenario_id: 'normal_summer',
          name: 'Normal Summer',
          description: 'Weather scenarios require main_weather.py backend',
          temperature_c: 30,
          wind_speed_ms: 2.5
        }
      ]);
      setLoading(false);
    }
  };

  const handleScenarioSelect = (scenarioId) => {
    const scenario = scenarios.find((s) => s.scenario_id === scenarioId);
    setWeatherInfo(scenario);
    setCustomMode(false);
    onScenarioChange(scenarioId);
  };

  const handleCustomWeatherChange = (field, value) => {
    setCustomWeather(prev => ({
      ...prev,
      [field]: parseFloat(value)
    }));
  };

  const applyCustomWeather = () => {
    setCustomMode(true);
    setWeatherInfo(null);
    onScenarioChange('custom', customWeather);
  };

  const getScenarioIcon = (scenarioId) => {
    const icons = {
      extreme_heat: '🔥',
      hot_day: '☀️',
      normal_summer: '🌤️',
      optimal: '😎',
      night_peak: '🌙',
      windy_day: '💨',
      cloudy_cool: '☁️',
    };
    return icons[scenarioId] || '🌡️';
  };

  const getScenarioColor = (scenarioId) => {
    const colors = {
      extreme_heat: '#ef4444',
      hot_day: '#f59e0b',
      normal_summer: '#10b981',
      optimal: '#3b82f6',
      night_peak: '#6366f1',
      windy_day: '#06b6d4',
      cloudy_cool: '#8b5cf6',
    };
    return colors[scenarioId] || '#6b7280';
  };

  if (loading) {
    return <div className="weather-loading">Loading scenarios...</div>;
  }

  return (
    <div className="weather-controls">
      <div className="weather-header">
        <h3>🌦️ Weather Scenarios</h3>
        <p>Select a weather condition to see how it affects line capacity</p>
      </div>

      <div className="scenarios-grid">
        {scenarios.map((scenario) => (
          <div
            key={scenario.scenario_id}
            className={`scenario-card ${
              currentScenario === scenario.scenario_id ? 'active' : ''
            }`}
            onClick={() => handleScenarioSelect(scenario.scenario_id)}
            style={{
              borderLeftColor: getScenarioColor(scenario.scenario_id),
            }}
          >
            <div className="scenario-icon">
              {getScenarioIcon(scenario.scenario_id)}
            </div>
            <div className="scenario-content">
              <div className="scenario-name">{scenario.name}</div>
              <div className="scenario-description">{scenario.description}</div>
              <div className="scenario-conditions">
                <span className="condition-item">
                  🌡️ {scenario.temperature_c}°C
                </span>
                <span className="condition-item">
                  💨 {scenario.wind_speed_ms} m/s
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {weatherInfo && (
        <div className="current-weather-info">
          <h4>Current Selection: {weatherInfo.name}</h4>
          <div className="weather-details">
            <div className="weather-detail-item">
              <span className="detail-label">Temperature:</span>
              <span className="detail-value">{weatherInfo.temperature_c}°C</span>
            </div>
            <div className="weather-detail-item">
              <span className="detail-label">Wind Speed:</span>
              <span className="detail-value">{weatherInfo.wind_speed_ms} m/s</span>
            </div>
            <div className="weather-detail-item description">
              <span className="detail-label">Expected Impact:</span>
              <span className="detail-value">{weatherInfo.description}</span>
            </div>
          </div>
        </div>
      )}

      <div className="custom-weather-panel">
        <h4>🎛️ Custom Weather Input</h4>
        <p className="custom-weather-hint">
          Enter your own weather conditions for custom analysis
        </p>

        <div className="custom-inputs">
          <div className="custom-input-group">
            <label>
              🌡️ Temperature: {customWeather.temperature}°C
            </label>
            <input
              type="range"
              min="-10"
              max="60"
              step="1"
              value={customWeather.temperature}
              onChange={(e) => handleCustomWeatherChange('temperature', e.target.value)}
              className="weather-slider"
            />
            <div className="range-labels">
              <span>-10°C</span>
              <span>60°C</span>
            </div>
          </div>

          <div className="custom-input-group">
            <label>
              💨 Wind Speed: {customWeather.windSpeed} m/s
            </label>
            <input
              type="range"
              min="0"
              max="15"
              step="0.5"
              value={customWeather.windSpeed}
              onChange={(e) => handleCustomWeatherChange('windSpeed', e.target.value)}
              className="weather-slider"
            />
            <div className="range-labels">
              <span>0 m/s (Calm)</span>
              <span>15 m/s (Strong)</span>
            </div>
          </div>

          <div className="custom-input-group">
            <label>
              ☀️ Solar Altitude: {customWeather.solarAltitude}°
            </label>
            <input
              type="range"
              min="0"
              max="90"
              step="5"
              value={customWeather.solarAltitude}
              onChange={(e) => handleCustomWeatherChange('solarAltitude', e.target.value)}
              className="weather-slider"
            />
            <div className="range-labels">
              <span>0° (Night)</span>
              <span>90° (Overhead)</span>
            </div>
          </div>

          <div className="custom-input-group">
            <label>
              💧 Humidity: {customWeather.humidity}%
            </label>
            <input
              type="range"
              min="20"
              max="100"
              step="5"
              value={customWeather.humidity}
              onChange={(e) => handleCustomWeatherChange('humidity', e.target.value)}
              className="weather-slider"
            />
            <div className="range-labels">
              <span>20% (Dry)</span>
              <span>100% (Humid)</span>
            </div>
          </div>

          <button
            className={`apply-custom-button ${customMode ? 'active' : ''}`}
            onClick={applyCustomWeather}
          >
            {customMode ? '✓ Applied' : 'Apply Custom Weather'}
          </button>
        </div>
      </div>

      <div className="weather-info-panel">
        <h4>ℹ️ How Weather Affects Capacity</h4>
        <ul>
          <li>
            <strong>Temperature:</strong> Higher temperatures reduce cooling efficiency →
            Lower ampacity
          </li>
          <li>
            <strong>Wind Speed:</strong> More wind increases convective cooling →
            Higher ampacity
          </li>
          <li>
            <strong>Solar Radiation:</strong> Sun heats conductors → Lower ampacity
          </li>
        </ul>
      </div>
    </div>
  );
};

export default WeatherControls;
