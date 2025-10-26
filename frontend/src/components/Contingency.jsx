/**
 * Contingency Component
 * N-1 Analysis: What happens if a transmission line fails?
 */

import { useState, useEffect } from 'react';
import apiService from '../services/api';
import './Contingency.css';

const Contingency = ({ customWeather }) => {
  const [selectedLine, setSelectedLine] = useState('L0');
  const [contingencyData, setContingencyData] = useState(null);
  const [allLines, setAllLines] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Fetch available lines on mount
  useEffect(() => {
    fetchAllLines();
  }, []);

  const fetchAllLines = async () => {
    try {
      const data = await apiService.getAllLinesWithWeather('manual', 'normal_midday', null, customWeather);
      setAllLines(data.lines || []);
    } catch (err) {
      console.error('Error fetching lines:', err);
    }
  };

  // Fetch contingency analysis when line selected
  const analyzeContingency = async (lineId) => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiService.getN1Contingency(lineId, customWeather);
      setContingencyData(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleLineSelect = (lineId) => {
    setSelectedLine(lineId);
    analyzeContingency(lineId);
  };

  // Initial analysis
  useEffect(() => {
    if (selectedLine) {
      analyzeContingency(selectedLine);
    }
  }, [JSON.stringify(customWeather)]);

  const getStatusClass = (status) => {
    return status.toLowerCase();
  };

  return (
    <div className="contingency-container">
      {/* Header */}
      <div className="contingency-header">
        <h2>N-1 Contingency Analysis</h2>
        <p>Simulate transmission line outage and analyze grid impact</p>
      </div>

      {/* Line Selector */}
      <div className="line-selector-section">
        <h3>Select Line to Fail:</h3>
        <select
          value={selectedLine}
          onChange={(e) => handleLineSelect(e.target.value)}
          className="line-selector"
        >
          {allLines.map((line) => (
            <option key={line.line_id} value={line.line_id}>
              {line.line_id} - {line.line_name} ({line.utilization_pct}% utilized)
            </option>
          ))}
        </select>
      </div>

      {loading && (
        <div className="contingency-loading">
          <div className="spinner"></div>
          <p>Analyzing contingency scenario...</p>
        </div>
      )}

      {error && (
        <div className="contingency-error">
          <p>Error: {error}</p>
          <button onClick={() => analyzeContingency(selectedLine)}>Retry</button>
        </div>
      )}

      {contingencyData && !loading && (
        <>
          {/* Failed Line Info */}
          <div className="failed-line-card">
            <h3>Failed Line</h3>
            <div className="failed-line-info">
              <div className="info-row">
                <span className="label">Line:</span>
                <span className="value">{contingencyData.failed_line.line_id} - {contingencyData.failed_line.line_name}</span>
              </div>
              <div className="info-row">
                <span className="label">Power Flow:</span>
                <span className="value critical-value">{contingencyData.failed_line.flow_mw} MW</span>
              </div>
              <div className="info-row">
                <span className="label">Connection:</span>
                <span className="value">Bus {contingencyData.failed_line.bus0} → Bus {contingencyData.failed_line.bus1}</span>
              </div>
            </div>
          </div>

          {/* Impact Summary */}
          <div className="impact-summary">
            <h3>System Impact Summary</h3>
            <div className="summary-grid">
              <div className="summary-card">
                <div className="card-label">Affected Lines</div>
                <div className="card-value">{contingencyData.summary.total_affected_lines}</div>
              </div>
              <div className="summary-card overload">
                <div className="card-label">Overloaded (≥100%)</div>
                <div className="card-value">{contingencyData.summary.overloaded_lines}</div>
              </div>
              <div className="summary-card critical">
                <div className="card-label">Critical (≥95%)</div>
                <div className="card-value">{contingencyData.summary.critical_lines}</div>
              </div>
              <div className="summary-card warning">
                <div className="card-label">Warning (≥80%)</div>
                <div className="card-value">{contingencyData.summary.warning_lines || 0}</div>
              </div>
              <div className="summary-card">
                <div className="card-label">Redistributed Power</div>
                <div className="card-value">{contingencyData.summary.redistributed_power_mw} MW</div>
              </div>
            </div>
          </div>

          {/* Affected Lines Table */}
          <div className="affected-lines-section">
            <h3>Power Redistribution Analysis</h3>
            <p className="section-note">Lines sorted by utilization increase (most affected first)</p>

            {contingencyData.affected_lines.length === 0 ? (
              <div className="no-impact">
                <p>No significant impact detected</p>
                <p className="no-impact-detail">
                  This line appears to be isolated or has no parallel paths for power redistribution.
                </p>
              </div>
            ) : (
              <div className="affected-lines-table">
                <table>
                  <thead>
                    <tr>
                      <th>Line</th>
                      <th>Baseline Flow</th>
                      <th>Contingency Flow</th>
                      <th>Increase</th>
                      <th>Baseline Util%</th>
                      <th>Contingency Util%</th>
                      <th>Util Change</th>
                      <th>Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {contingencyData.affected_lines.map((line) => (
                      <tr key={line.line_id} className={`row-${getStatusClass(line.status)}`}>
                        <td className="line-id-col">
                          <strong>{line.line_id}</strong>
                          <div className="line-detail">{line.line_name.substring(0, 30)}...</div>
                        </td>
                        <td>{line.baseline_flow_mw} MW</td>
                        <td className="contingency-flow">
                          <strong>{line.contingency_flow_mw} MW</strong>
                        </td>
                        <td className="flow-increase">
                          +{line.flow_increase_mw} MW
                          <div className="increase-pct">(+{line.flow_increase_pct}%)</div>
                        </td>
                        <td>{line.baseline_utilization_pct}%</td>
                        <td className={`util-${getStatusClass(line.status)}`}>
                          <strong>{line.contingency_utilization_pct}%</strong>
                        </td>
                        <td className={line.utilization_increase_pct > 20 ? 'util-increase-high' : 'util-increase'}>
                          +{line.utilization_increase_pct}%
                        </td>
                        <td>
                          <span className={`status-badge badge-${getStatusClass(line.status)}`}>
                            {line.status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Risk Assessment */}
          {contingencyData.summary.overloaded_lines > 0 && (
            <div className="risk-assessment critical">
              <h3>CRITICAL RISK DETECTED</h3>
              <p>
                <strong>{contingencyData.summary.overloaded_lines}</strong> line(s) would become overloaded if{' '}
                <strong>{contingencyData.failed_line.line_id}</strong> fails.
              </p>
              <p className="risk-action">
                <strong>Recommended Actions:</strong>
                <ul>
                  <li>Reduce load on affected lines before maintenance</li>
                  <li>Consider dynamic line rating (DLR) to increase capacity</li>
                  <li>Schedule outage during low-load periods (early morning)</li>
                  <li>Have generation redispatch plan ready</li>
                </ul>
              </p>
            </div>
          )}

          {contingencyData.summary.critical_lines > 0 && contingencyData.summary.overloaded_lines === 0 && (
            <div className="risk-assessment warning">
              <h3>WARNING: Close to Limits</h3>
              <p>
                <strong>{contingencyData.summary.critical_lines}</strong> line(s) would operate at 95%+ capacity.
              </p>
              <p className="risk-action">
                <strong>Recommended Actions:</strong>
                <ul>
                  <li>Monitor weather conditions closely</li>
                  <li>Enable DLR monitoring for affected lines</li>
                  <li>Prepare load shedding procedures</li>
                </ul>
              </p>
            </div>
          )}

          {contingencyData.summary.warning_lines > 0 && contingencyData.summary.overloaded_lines === 0 && contingencyData.summary.critical_lines === 0 && (
            <div className="risk-assessment warning">
              <h3>CAUTION: Elevated Utilization</h3>
              <p>
                <strong>{contingencyData.summary.warning_lines}</strong> line(s) would operate at 80-95% capacity.
              </p>
              <p className="risk-action">
                <strong>Recommended Actions:</strong>
                <ul>
                  <li>Monitor line loading during peak hours</li>
                  <li>Consider enabling DLR for improved visibility</li>
                  <li>Plan for demand response if conditions worsen</li>
                  <li>Safe to proceed with scheduled maintenance</li>
                </ul>
              </p>
            </div>
          )}

          {contingencyData.summary.overloaded_lines === 0 && contingencyData.summary.critical_lines === 0 && contingencyData.summary.warning_lines === 0 && (
            <div className="risk-assessment normal">
              <h3>System Stable</h3>
              <p>
                All lines remain within safe operating limits after <strong>{contingencyData.failed_line.line_id}</strong> outage.
              </p>
              <p className="risk-action">
                This line can be safely taken out of service for maintenance without grid reliability concerns.
              </p>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default Contingency;
