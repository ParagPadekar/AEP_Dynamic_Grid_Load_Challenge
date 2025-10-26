/**
 * WeatherControls Component
 * Dynamic weather and time-of-day controls with quick presets
 */

import { useState, useEffect } from 'react';
import './WeatherControls.css';

const WeatherControls = ({ onScenarioChange }) => {
  // Dynamic weather state
  const [hourOfDay, setHourOfDay] = useState(12); // 12 PM default
  const [temperature, setTemperature] = useState(30);
  const [windSpeed, setWindSpeed] = useState(2.5);
  const [solarAltitude, setSolarAltitude] = useState(75);
  const [humidity, setHumidity] = useState(70);

  // Quick presets
  const presets = {
    worst_case: {
      name: '🔥 Worst Case',
      description: 'Evening peak + extreme heat wave',
      hourOfDay: 18,
      temperature: 44,
      windSpeed: 0.5,
      solarAltitude: 15,
      humidity: 70,
      color: '#ef4444'
    },
    typical: {
      name: '✅ Typical Day',
      description: 'Normal summer midday conditions',
      hourOfDay: 12,
      temperature: 30,
      windSpeed: 2.5,
      solarAltitude: 75,
      humidity: 70,
      color: '#10b981'
    },
    best_case: {
      name: '😎 Best Case',
      description: 'Early morning + cool & windy',
      hourOfDay: 6,
      temperature: 22,
      windSpeed: 5.5,
      solarAltitude: 5,
      humidity: 80,
      color: '#3b82f6'
    }
  };

  // Apply weather changes
  const applyWeather = () => {
    const customWeather = {
      temperature,
      windSpeed,
      solarAltitude,
      humidity,
      hourOfDay
    };
    onScenarioChange('custom', customWeather);
  };

  // Auto-apply when values change (debounced)
  useEffect(() => {
    const timer = setTimeout(() => {
      applyWeather();
    }, 500); // 500ms debounce

    return () => clearTimeout(timer);
  }, [hourOfDay, temperature, windSpeed, solarAltitude, humidity]);

  const applyPreset = (presetKey) => {
    const preset = presets[presetKey];
    setHourOfDay(preset.hourOfDay);
    setTemperature(preset.temperature);
    setWindSpeed(preset.windSpeed);
    setSolarAltitude(preset.solarAltitude);
    setHumidity(preset.humidity);
    setManualSolar(false); // Reset to auto solar when applying preset
  };

  const getTimeLabel = (hour) => {
    if (hour === 0) return '12 AM';
    if (hour < 12) return `${hour} AM`;
    if (hour === 12) return '12 PM';
    return `${hour - 12} PM`;
  };

  const getLoadLevel = (hour) => {
    // Based on real utility load curve
    const loadFactors = [
      1.0, 0.974, 0.95, 0.929, 0.913, 0.903, 0.9, 0.903,
      0.913, 0.929, 0.95, 0.974, 1.0, 1.026, 1.05, 1.071,
      1.087, 1.097, 1.1, 1.097, 1.087, 1.071, 1.05, 1.026
    ];
    return (loadFactors[hour] * 100).toFixed(0);
  };

  const getSolarFromHour = (hour) => {
    // Approximate solar altitude based on time (Hawaii ~21°N latitude)
    if (hour < 6 || hour > 18) return 0; // Night
    if (hour === 12) return 75; // Solar noon
    const hoursSinceNoon = Math.abs(12 - hour);
    return Math.max(0, 75 - (hoursSinceNoon * 10));
  };

  // Auto-adjust solar altitude when time changes (only if user isn't manually adjusting solar)
  const [manualSolar, setManualSolar] = useState(false);

  useEffect(() => {
    if (!manualSolar) {
      const autoSolar = getSolarFromHour(hourOfDay);
      setSolarAltitude(autoSolar);
    }
  }, [hourOfDay, manualSolar]);

  return (
    <div className="weather-controls">
      <div className="weather-header">
        <h3>Dynamic Grid Analysis</h3>
        <p>Adjust time and weather to see real-time impact on grid capacity</p>
      </div>

      {/* Quick Presets */}
      <div className="presets-section">
        <h4>Quick Scenarios</h4>
        <div className="preset-buttons">
          {Object.entries(presets).map(([key, preset]) => (
            <button
              key={key}
              className="preset-btn"
              onClick={() => applyPreset(key)}
              style={{ borderLeftColor: preset.color }}
            >
              <div className="preset-name">{preset.name}</div>
              <div className="preset-desc">{preset.description}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Time of Day Control */}
      <div className="control-section time-control">
        <h4>Time of Day</h4>
        <div className="time-display">
          <span className="time-value">{getTimeLabel(hourOfDay)}</span>
          <span className="load-indicator">Load: {getLoadLevel(hourOfDay)}%</span>
        </div>
        <select
          value={hourOfDay}
          onChange={(e) => setHourOfDay(parseInt(e.target.value))}
          className="time-dropdown"
        >
          {[...Array(24)].map((_, hour) => (
            <option key={hour} value={hour}>
              {getTimeLabel(hour)} - Load: {getLoadLevel(hour)}%
            </option>
          ))}
        </select>
        <div className="time-markers">
          <span onClick={() => setHourOfDay(6)}>6 AM<br/>Min</span>
          <span onClick={() => setHourOfDay(9)}>9 AM<br/>Ramp</span>
          <span onClick={() => setHourOfDay(12)}>12 PM<br/>Noon</span>
          <span onClick={() => setHourOfDay(18)}>6 PM<br/>Peak</span>
          <span onClick={() => setHourOfDay(2)}>2 AM<br/>Low</span>
        </div>
      </div>

      {/* Weather Parameters */}
      <div className="control-section">
        <h4>Weather Conditions</h4>

        <div className="weather-input-group">
          <label>
            <span className="label-text">Temperature</span>
            <span className="label-value">{temperature}°C</span>
          </label>
          <input
            type="range"
            min="15"
            max="50"
            step="1"
            value={temperature}
            onChange={(e) => setTemperature(parseInt(e.target.value))}
            className="weather-slider temp-slider"
          />
          <div className="slider-labels">
            <span>15°C Cool</span>
            <span>50°C Extreme</span>
          </div>
        </div>

        <div className="weather-input-group">
          <label>
            <span className="label-text">Wind Speed</span>
            <span className="label-value">{windSpeed} m/s</span>
          </label>
          <input
            type="range"
            min="0"
            max="10"
            step="0.5"
            value={windSpeed}
            onChange={(e) => setWindSpeed(parseFloat(e.target.value))}
            className="weather-slider wind-slider"
          />
          <div className="slider-labels">
            <span>0 m/s Calm</span>
            <span>10 m/s Strong</span>
          </div>
        </div>

        <div className="weather-input-group">
          <label>
            <span className="label-text">Solar Altitude</span>
            <span className="label-value">{solarAltitude}°</span>
          </label>
          <input
            type="range"
            min="0"
            max="90"
            step="5"
            value={solarAltitude}
            onChange={(e) => {
              setSolarAltitude(parseInt(e.target.value));
              setManualSolar(true); // User manually adjusted solar
            }}
            className="weather-slider solar-slider"
          />
          <div className="slider-labels">
            <span>0° Night</span>
            <span>90° Overhead</span>
          </div>
        </div>

        <div className="weather-input-group">
          <label>
            <span className="label-text">Humidity</span>
            <span className="label-value">{humidity}%</span>
          </label>
          <input
            type="range"
            min="20"
            max="100"
            step="5"
            value={humidity}
            onChange={(e) => setHumidity(parseInt(e.target.value))}
            className="weather-slider humidity-slider"
          />
          <div className="slider-labels">
            <span>20% Dry</span>
            <span>100% Humid</span>
          </div>
        </div>
      </div>

      {/* Impact Summary */}
      <div className="impact-summary">
        <h4>Current Conditions</h4>
        <div className="summary-grid">
          <div className="summary-item">
            <span className="summary-label">Time</span>
            <span className="summary-value">{getTimeLabel(hourOfDay)}</span>
          </div>
          <div className="summary-item">
            <span className="summary-label">Load Level</span>
            <span className="summary-value">{getLoadLevel(hourOfDay)}%</span>
          </div>
          <div className="summary-item">
            <span className="summary-label">Temperature</span>
            <span className="summary-value">{temperature}°C</span>
          </div>
          <div className="summary-item">
            <span className="summary-label">Wind</span>
            <span className="summary-value">{windSpeed} m/s</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WeatherControls;
