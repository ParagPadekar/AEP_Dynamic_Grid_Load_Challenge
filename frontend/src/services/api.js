/**
 * API Service Layer
 * Handles all communication with the IEEE 738 DLR backend
 */

import axios from 'axios';

// API Base URL - change this if backend is on different host/port
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000, // 10 second timeout
  headers: {
    'Content-Type': 'application/json',
  },
});

// API Service Object
const apiService = {
  /**
   * Health check
   */
  async healthCheck() {
    const response = await api.get('/health');
    return response.data;
  },

  /**
   * Get all weather scenarios
   */
  async getScenarios() {
    const response = await api.get('/weather/scenarios');
    return response.data;
  },

  /**
   * Calculate ampacity with weather for a single line
   * @param {Object} params - Calculation parameters
   * @param {string} params.line_id - Line ID (e.g., "L0")
   * @param {string} params.weather_source - "scenario", "live", or "manual"
   * @param {string} params.scenario_name - Scenario name if weather_source="scenario"
   * @param {number} params.temp_ambient_c - Temperature if manual
   * @param {number} params.wind_speed_ms - Wind speed if manual
   */
  async calculateWithWeather(params) {
    const response = await api.post('/calculate_with_weather', params);
    return response.data;
  },

  /**
   * Get all lines with weather-based calculations
   * @param {string} weatherSource - "scenario", "live", or "manual"
   * @param {string} scenarioName - Scenario name
   * @param {number} limit - Max number of lines to return
   * @param {Object} customWeather - Custom weather parameters (if weatherSource="manual")
   */
  async getAllLinesWithWeather(weatherSource = 'scenario', scenarioName = 'normal_summer', limit = null, customWeather = null) {
    try {
      // Try weather-enabled endpoint first (main_weather.py)
      const params = {
        weather_source: weatherSource,
        scenario_name: scenarioName,
      };
      if (limit) params.limit = limit;

      // Add custom weather parameters if in manual mode
      if (weatherSource === 'manual' && customWeather) {
        params.temp_ambient_c = customWeather.temperature;
        params.wind_speed_ms = customWeather.windSpeed;
        params.solar_altitude = customWeather.solarAltitude;
        params.humidity_pct = customWeather.humidity;
      }

      const response = await api.get('/calculate_all_with_weather', { params });
      return response.data;
    } catch (err) {
      // Fallback to original endpoint (main.py)
      console.warn('Weather endpoint not available, falling back to /get_all_lines');
      const params = {};
      if (limit) params.limit = limit;

      const response = await api.get('/get_all_lines', { params });
      // Transform response to match expected format
      return {
        weather: { source: 'default', temperature_c: 30, wind_speed_ms: 2.0 },
        total_lines: response.data.length,
        lines: response.data
      };
    }
  },

  /**
   * Compare multiple scenarios for a single line
   * @param {string} lineId - Line ID
   * @param {Array<string>} scenarios - Array of scenario names
   */
  async compareScenarios(lineId, scenarios = null) {
    const response = await api.post('/compare_scenarios', {
      line_id: lineId,
      scenarios: scenarios,
    });
    return response.data;
  },

  /**
   * Predict load for a line
   * @param {string} lineId - Line ID
   * @param {number} hoursAhead - Hours to forecast
   */
  async predictLoad(lineId, hoursAhead = 24) {
    const response = await api.post('/predict_load', {
      line_id: lineId,
      hours_ahead: hoursAhead,
    });
    return response.data;
  },

  /**
   * Get lines summary statistics
   */
  async getLinesSummary() {
    const response = await api.get('/lines/summary');
    return response.data;
  },
};

// Error handling interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // Server responded with error status
      console.error('API Error:', error.response.data);
      throw new Error(error.response.data.detail || 'Server error');
    } else if (error.request) {
      // Request made but no response
      console.error('Network Error:', error.request);
      throw new Error('Network error - is the backend running?');
    } else {
      // Other error
      console.error('Error:', error.message);
      throw error;
    }
  }
);

export default apiService;
