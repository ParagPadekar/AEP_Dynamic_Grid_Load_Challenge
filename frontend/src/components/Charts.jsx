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

const Charts = ({ selectedLine, selectedScenario }) => {
  const [loadPrediction, setLoadPrediction] = useState([]);
  const [scenarioComparison, setScenarioComparison] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (selectedLine) {
      fetchChartData();
    }
  }, [selectedLine, selectedScenario]);

  const fetchChartData = async () => {
    setLoading(true);
    try {
      // Fetch load prediction
      const loadData = await apiService.predictLoad(selectedLine, 24);
      setLoadPrediction(
        loadData.predictions.map((p) => ({
          hour: p.hour,
          timestamp: new Date(p.timestamp).toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit',
          }),
          load: p.predicted_load_mw,
          current: p.predicted_current_a,
        }))
      );

      // Try to fetch scenario comparison (only available in main_weather.py)
      try {
        const comparisonData = await apiService.compareScenarios(selectedLine, [
          'extreme_heat',
          'hot_day',
          'normal_summer',
          'optimal',
          'windy_day',
        ]);
        setScenarioComparison(comparisonData);
      } catch (err) {
        console.warn('Scenario comparison not available (requires main_weather.py backend)');
        // Set null to hide scenario comparison charts
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
        <h2>Line Analysis: {selectedLine}</h2>
        {scenarioComparison && (
          <div className="line-info">
            <span>{scenarioComparison.line_name}</span>
            <span>{scenarioComparison.conductor}</span>
            <span>Static Rating: {scenarioComparison.static_rating_mva} MVA</span>
          </div>
        )}
      </div>

      {/* Load Prediction Chart */}
      <div className="chart-section">
        <h3>📈 24-Hour Load Forecast</h3>
        <ResponsiveContainer width="100%" height={350}>
          <LineChart data={loadPrediction}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="timestamp" />
            <YAxis
              yAxisId="left"
              label={{ value: 'Load (MW)', angle: -90, position: 'insideLeft' }}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              label={{ value: 'Current (A)', angle: 90, position: 'insideRight' }}
            />
            <Tooltip />
            <Legend />
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="load"
              stroke="#8b5cf6"
              strokeWidth={2}
              name="Predicted Load (MW)"
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="current"
              stroke="#06b6d4"
              strokeWidth={2}
              name="Current (A)"
              strokeDasharray="5 5"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Scenario Comparison - Ampacity */}
      <div className="chart-section">
        <h3>⚡ Ampacity Across Weather Scenarios</h3>
        <ResponsiveContainer width="100%" height={350}>
          <BarChart data={comparisonChartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="scenario" />
            <YAxis label={{ value: 'Ampacity (A)', angle: -90, position: 'insideLeft' }} />
            <Tooltip />
            <Legend />
            <Bar dataKey="ampacity" fill="#8b5cf6" name="Ampacity (A)">
              {comparisonChartData.map((entry, index) => {
                const color =
                  entry.utilization > 95
                    ? '#ef4444'
                    : entry.utilization > 80
                    ? '#f59e0b'
                    : '#10b981';
                return <Cell key={`cell-${index}`} fill={color} />;
              })}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Scenario Comparison - Utilization */}
      <div className="chart-section">
        <h3>📊 Utilization Percentage by Scenario</h3>
        <ResponsiveContainer width="100%" height={350}>
          <BarChart data={comparisonChartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="scenario" />
            <YAxis
              label={{ value: 'Utilization (%)', angle: -90, position: 'insideLeft' }}
            />
            <Tooltip />
            <Legend />
            <Bar dataKey="utilization" fill="#06b6d4" name="Utilization (%)">
              {comparisonChartData.map((entry, index) => {
                const color =
                  entry.utilization > 95
                    ? '#ef4444'
                    : entry.utilization > 80
                    ? '#f59e0b'
                    : '#10b981';
                return <Cell key={`cell-${index}`} fill={color} />;
              })}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Two-column layout for weather and status */}
      <div className="charts-row">
        {/* Weather Conditions */}
        <div className="chart-section half-width">
          <h3>🌡️ Weather Conditions</h3>
          <ResponsiveContainer width="100%" height={350}>
            <BarChart data={comparisonChartData} margin={{ top: 20, right: 30, left: 20, bottom: 60 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="scenario"
                angle={-45}
                textAnchor="end"
                height={80}
                interval={0}
                tick={{ fontSize: 11 }}
              />
              <YAxis
                label={{ value: 'Value', angle: -90, position: 'insideLeft' }}
              />
              <Tooltip />
              <Legend />
              <Bar dataKey="temp" fill="#ef4444" name="Temp (°C)" />
              <Bar dataKey="wind" fill="#06b6d4" name="Wind (m/s)" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Status Distribution */}
        {statusData.length > 0 && (
          <div className="chart-section half-width">
            <h3>🎯 Status Distribution</h3>
            <ResponsiveContainer width="100%" height={350}>
              <PieChart>
                <Pie
                  data={statusData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) =>
                    `${name}: ${(percent * 100).toFixed(0)}%`
                  }
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {statusData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Comparison Table */}
      {scenarioComparison && (
        <div className="comparison-table-section">
          <h3>📋 Detailed Comparison</h3>
          <table className="comparison-table">
            <thead>
              <tr>
                <th>Scenario</th>
                <th>Temperature</th>
                <th>Wind</th>
                <th>Ampacity</th>
                <th>vs Static</th>
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
                    <td>{comp.scenario.replace('_', ' ')}</td>
                    <td>{comp.weather.temperature_c}°C</td>
                    <td>{comp.weather.wind_speed_ms} m/s</td>
                    <td>{Math.round(comp.ampacity)} A</td>
                    <td className={vsStatic >= 0 ? 'positive' : 'negative'}>
                      {vsStatic >= 0 ? '+' : ''}
                      {vsStatic.toFixed(1)}%
                    </td>
                    <td>{comp.utilization_pct.toFixed(1)}%</td>
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
    </div>
  );
};

export default Charts;
