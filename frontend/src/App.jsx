/**
 * Main App Component
 * IEEE 738 Dynamic Line Rating Dashboard
 */

import { useState, useEffect } from 'react';
import Dashboard from './components/Dashboard';
import TableView from './components/TableView';
import Charts from './components/Charts';
import WeatherControls from './components/WeatherControls';
import apiService from './services/api';
import './App.css';

function App() {
  const [activeView, setActiveView] = useState('dashboard');
  const [selectedLine, setSelectedLine] = useState('L0');
  const [selectedScenario, setSelectedScenario] = useState('normal_summer');
  const [customWeather, setCustomWeather] = useState(null);
  const [backendStatus, setBackendStatus] = useState(null);
  const [showWeatherPanel, setShowWeatherPanel] = useState(true);

  useEffect(() => {
    checkBackendHealth();
    // Check health every 30 seconds
    const interval = setInterval(checkBackendHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const checkBackendHealth = async () => {
    try {
      const health = await apiService.healthCheck();
      setBackendStatus({
        healthy: true,
        linesLoaded: health.lines_loaded,
        timestamp: health.timestamp,
      });
    } catch (err) {
      setBackendStatus({
        healthy: false,
        error: err.message,
      });
    }
  };

  const handleLineSelect = (lineId) => {
    setSelectedLine(lineId);
    setActiveView('charts');
  };

  const handleScenarioChange = (scenario, customWeatherParams = null) => {
    setSelectedScenario(scenario);
    setCustomWeather(customWeatherParams);
  };

  return (
    <div className="app">
      {/* Header */}
      <header className="app-header">
        <div className="header-content">
          <div className="header-title">
            <h1>⚡ IEEE 738 Dynamic Line Rating System</h1>
            <p className="subtitle">
              Real-time transmission line capacity monitoring with weather-based calculations
            </p>
          </div>
          <div className="header-status">
            {backendStatus && (
              <div className={`status-indicator ${backendStatus.healthy ? 'online' : 'offline'}`}>
                <span className="status-dot"></span>
                <span className="status-text">
                  {backendStatus.healthy
                    ? `${backendStatus.linesLoaded} lines loaded`
                    : 'Backend offline'}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Navigation */}
        <nav className="app-nav">
          <button
            className={`nav-button ${activeView === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveView('dashboard')}
          >
            📊 Dashboard
          </button>
          <button
            className={`nav-button ${activeView === 'table' ? 'active' : ''}`}
            onClick={() => setActiveView('table')}
          >
            📋 Table View
          </button>
          <button
            className={`nav-button ${activeView === 'charts' ? 'active' : ''}`}
            onClick={() => setActiveView('charts')}
          >
            📈 Charts & Analysis
          </button>
          <button
            className={`nav-button ${showWeatherPanel ? 'active' : ''}`}
            onClick={() => setShowWeatherPanel(!showWeatherPanel)}
          >
            🌦️ Weather
          </button>
        </nav>
      </header>

      {/* Main Content */}
      <div className="app-main">
        {/* Weather Panel (Collapsible) */}
        {showWeatherPanel && (
          <aside className="weather-panel">
            <WeatherControls
              onScenarioChange={handleScenarioChange}
              currentScenario={selectedScenario}
            />
          </aside>
        )}

        {/* Main Content Area */}
        <main className={`content-area ${showWeatherPanel ? 'with-sidebar' : 'full-width'}`}>
          {!backendStatus?.healthy && (
            <div className="backend-error">
              <h3>⚠️ Backend Connection Error</h3>
              <p>{backendStatus?.error || 'Cannot connect to backend API'}</p>
              <p>Make sure the backend server is running at http://localhost:8000</p>
              <button onClick={checkBackendHealth}>Retry Connection</button>
            </div>
          )}

          {backendStatus?.healthy && (
            <>
              {activeView === 'dashboard' && (
                <Dashboard
                  onLineSelect={handleLineSelect}
                  selectedScenario={selectedScenario}
                  customWeather={customWeather}
                />
              )}

              {activeView === 'table' && (
                <TableView
                  onLineSelect={handleLineSelect}
                  selectedScenario={selectedScenario}
                  customWeather={customWeather}
                />
              )}

              {activeView === 'charts' && (
                <Charts
                  selectedLine={selectedLine}
                  selectedScenario={selectedScenario}
                  customWeather={customWeather}
                />
              )}
            </>
          )}
        </main>
      </div>

      {/* Footer */}
      <footer className="app-footer">
        <div className="footer-content">
          <div className="footer-info">
            <span>Built for HackOHIO 2024</span>
            <span>•</span>
            <span>IEEE 738 Thermal Rating Standard</span>
            <span>•</span>
            <span>Hawaii 40-Bus Test System</span>
          </div>
          <div className="footer-scenario">
            Current Scenario: <strong>{selectedScenario.replace('_', ' ')}</strong>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
