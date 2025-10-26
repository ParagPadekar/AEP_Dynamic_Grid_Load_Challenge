/**
 * Charts Component
 * Visualizations using Recharts for load predictions and scenario comparisons
 */

import { useState, useEffect } from 'react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import apiService from '../services/api';
import './Charts.css';

const Charts = ({ selectedLine, selectedScenario, customWeather }) => {
  const [loadPrediction, setLoadPrediction] = useState([]);
  const [scenarioComparison, setScenarioComparison] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (selectedLine) {
      fetchChartData();
    }
  }, [selectedLine, selectedScenario, JSON.stringify(customWeather)]);

  const fetchChartData = async () => {
    setLoading(true);
    try {
      // Fetch load prediction
      const loadData = await apiService.predictLoad(selectedLine, 24);
      setLoadPrediction(
        loadData.predictions.map((p, index) => ({
          hour: p.hour,
          hourLabel: `Hour ${index + 1}`,
          timestamp: new Date(p.timestamp).toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
          }),
          load: p.predicted_load_mw,
          current: p.predicted_current_a,
        }))
      );

      // Fetch current line details for the selected scenario
      try {
        const comparisonData = await apiService.compareScenarios(selectedLine, [
          'critical_evening',
          'warning_midday',
          'normal_midday',
          'optimal_early',
        ]);
        setScenarioComparison(comparisonData);
      } catch (err) {
        console.warn('Scenario comparison not available');
        setScenarioComparison(null);
      }
    } catch (err) {
      console.error('Error fetching chart data:', err);
    } finally {
      setLoading(false);
    }
  };

  if (!selectedLine) {
    return (
      <div className="charts-placeholder">
        <p>Select a transmission line to view detailed charts</p>
      </div>
    );
  }

  if (loading) {
    return <div className="charts-loading">Loading charts...</div>;
  }

  // Prepare scenario comparison data
  const comparisonChartData = scenarioComparison
    ? scenarioComparison.comparisons.map((c) => ({
        scenario: c.scenario.replace('_', ' '),
        ampacity: c.ampacity,
        utilization: c.utilization_pct,
        temp: c.weather.temperature_c,
        wind: c.weather.wind_speed_ms,
      }))
    : [];

  // Debug: Log chart data
  console.log('Scenario Comparison Data:', scenarioComparison);
  console.log('Comparison Chart Data:', comparisonChartData);

  // Status distribution for pie chart
  const statusData = scenarioComparison
    ? [
        {
          name: 'Critical',
          value: scenarioComparison.comparisons.filter((c) => c.status === 'Critical')
            .length,
          color: '#ef4444',
        },
        {
          name: 'Warning',
          value: scenarioComparison.comparisons.filter((c) => c.status === 'Warning')
            .length,
          color: '#f59e0b',
        },
        {
          name: 'Normal',
          value: scenarioComparison.comparisons.filter((c) => c.status === 'Normal')
            .length,
          color: '#10b981',
        },
      ].filter((d) => d.value > 0)
    : [];

  return (
    <div className="charts-container">
      <div className="chart-header">
        <h2>Line Details: {selectedLine}</h2>
        {scenarioComparison && (
          <div className="line-info">
            <span><strong>{scenarioComparison.line_name}</strong></span>
            <span>Conductor: {scenarioComparison.conductor}</span>
            <span>Static Rating: <strong>{scenarioComparison.static_rating_mva} MVA</strong></span>
          </div>
        )}
      </div>

      {/* 24-Hour Load Forecast - MOST IMPORTANT for showing time-of-day patterns */}
      <div className="chart-section">
        <h3>24-Hour Load Forecast (Time-of-Day Patterns)</h3>
        <p className="chart-description">
          Shows how load varies throughout the day based on real utility patterns -
          minimum at 6 AM (90%), peak at 6 PM (110%)
        </p>
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={loadPrediction}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="hourLabel"
              label={{ value: 'Next 24 Hours', position: 'insideBottom', offset: -5 }}
            />
            <YAxis
              yAxisId="left"
              label={{ value: 'Load (MW)', angle: -90, position: 'insideLeft' }}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const data = payload[0].payload;
                  return (
                    <div style={{
                      backgroundColor: 'var(--bg-tertiary)',
                      border: '2px solid var(--primary-color)',
                      borderRadius: '8px',
                      padding: '10px'
                    }}>
                      <p style={{ margin: 0, fontWeight: 'bold' }}>{data.hourLabel}</p>
                      <p style={{ margin: '5px 0 0 0', fontSize: '0.9em', color: 'var(--text-secondary)' }}>
                        Time: {data.timestamp}
                      </p>
                      <p style={{ margin: '5px 0 0 0', color: '#8b5cf6', fontWeight: 'bold' }}>
                        Load: {data.load.toFixed(2)} MW
                      </p>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Legend />
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="load"
              stroke="#8b5cf6"
              strokeWidth={3}
              name="Predicted Load (MW)"
              dot={{ fill: '#8b5cf6', r: 4 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Scenario Comparison Table - Clean and informative */}
      {scenarioComparison && (
        <div className="comparison-table-section">
          <h3>How Weather Affects This Line</h3>
          <p className="chart-description">
            Comparison across different weather scenarios showing how temperature and wind affect line capacity
          </p>
          <table className="comparison-table">
            <thead>
              <tr>
                <th>Scenario</th>
                <th>Temp</th>
                <th>Wind</th>
                <th>Dynamic Capacity</th>
                <th>vs Static Rating</th>
                <th>Utilization</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {scenarioComparison.comparisons.map((comp, idx) => {
                const vsStatic =
                  ((comp.ampacity_mva - scenarioComparison.static_rating_mva) /
                    scenarioComparison.static_rating_mva) *
                  100;
                return (
                  <tr key={idx}>
                    <td><strong>{comp.scenario.replace('_', ' ')}</strong></td>
                    <td>{comp.weather.temperature_c}°C</td>
                    <td>{comp.weather.wind_speed_ms} m/s</td>
                    <td><strong>{comp.ampacity_mva.toFixed(1)} MVA</strong></td>
                    <td className={vsStatic >= 0 ? 'positive' : 'negative'}>
                      <strong>{vsStatic >= 0 ? '+' : ''}{vsStatic.toFixed(1)}%</strong>
                    </td>
                    <td><strong>{comp.utilization_pct.toFixed(1)}%</strong></td>
                    <td>
                      <span className={`badge-${comp.status.toLowerCase()}`}>
                        {comp.status}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Key Takeaway Summary */}
      {scenarioComparison && (
        <div className="chart-section">
          <h3>Key Insights</h3>
          <div className="insights-grid">
            <div className="insight-card">
              <div className="insight-label">Best Conditions</div>
              <div className="insight-value">
                {Math.max(...scenarioComparison.comparisons.map(c => c.ampacity_mva)).toFixed(0)} MVA
              </div>
              <div className="insight-note">Cool temp + strong wind</div>
            </div>
            <div className="insight-card">
              <div className="insight-label">Worst Conditions</div>
              <div className="insight-value">
                {Math.min(...scenarioComparison.comparisons.map(c => c.ampacity_mva)).toFixed(0)} MVA
              </div>
              <div className="insight-note">High heat + low wind</div>
            </div>
            <div className="insight-card">
              <div className="insight-label">Capacity Range</div>
              <div className="insight-value">
                {((Math.max(...scenarioComparison.comparisons.map(c => c.ampacity_mva)) -
                   Math.min(...scenarioComparison.comparisons.map(c => c.ampacity_mva))) /
                   scenarioComparison.static_rating_mva * 100).toFixed(0)}%
              </div>
              <div className="insight-note">Weather impact on capacity</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Charts;
