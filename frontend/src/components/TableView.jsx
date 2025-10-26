/**
 * TableView Component
 * Detailed table view of all transmission lines with sorting and filtering
 */

import { useState, useEffect } from 'react';
import apiService from '../services/api';
import './TableView.css';

const TableView = ({ onLineSelect, selectedScenario, customWeather }) => {
  const [lines, setLines] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sortField, setSortField] = useState('utilization_pct');
  const [sortDirection, setSortDirection] = useState('desc');
  const [filterStatus, setFilterStatus] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchData();
  }, [selectedScenario, JSON.stringify(customWeather)]);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Determine weather source
      const weatherSource = customWeather ? 'manual' : 'scenario';

      const data = await apiService.getAllLinesWithWeather(
        weatherSource,
        selectedScenario,
        null, // Get all lines
        customWeather
      );

      setLines(data.lines || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const getSortedAndFilteredLines = () => {
    let filtered = lines;

    // Filter by status
    if (filterStatus !== 'all') {
      filtered = filtered.filter((line) => line.status === filterStatus);
    }

    // Filter by search term
    if (searchTerm) {
      filtered = filtered.filter(
        (line) =>
          line.line_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
          line.line_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          line.conductor.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Sort
    filtered.sort((a, b) => {
      let aVal = a[sortField];
      let bVal = b[sortField];

      if (typeof aVal === 'string') {
        aVal = aVal.toLowerCase();
        bVal = bVal.toLowerCase();
      }

      if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });

    return filtered;
  };

  const getStatusBadge = (status) => {
    const classes = {
      Critical: 'badge-critical',
      Warning: 'badge-warning',
      Normal: 'badge-normal',
    };
    return <span className={`status-badge ${classes[status]}`}>{status}</span>;
  };

  const getSortIcon = (field) => {
    if (sortField !== field) return '↕️';
    return sortDirection === 'asc' ? '↑' : '↓';
  };

  const filteredLines = getSortedAndFilteredLines();

  if (loading) {
    return <div className="table-loading">Loading data...</div>;
  }

  if (error) {
    return (
      <div className="table-error">
        <p>Error: {error}</p>
        <button onClick={fetchData}>Retry</button>
      </div>
    );
  }

  return (
    <div className="table-view">
      <div className="table-controls">
        <div className="search-box">
          <input
            type="text"
            placeholder="Search lines..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        <div className="filter-buttons">
          <button
            className={filterStatus === 'all' ? 'active' : ''}
            onClick={() => setFilterStatus('all')}
          >
            All ({lines.length})
          </button>
          <button
            className={filterStatus === 'Critical' ? 'active critical' : ''}
            onClick={() => setFilterStatus('Critical')}
          >
            Critical ({lines.filter((l) => l.status === 'Critical').length})
          </button>
          <button
            className={filterStatus === 'Warning' ? 'active warning' : ''}
            onClick={() => setFilterStatus('Warning')}
          >
            Warning ({lines.filter((l) => l.status === 'Warning').length})
          </button>
          <button
            className={filterStatus === 'Normal' ? 'active normal' : ''}
            onClick={() => setFilterStatus('Normal')}
          >
            Normal ({lines.filter((l) => l.status === 'Normal').length})
          </button>
        </div>

        <button onClick={fetchData} className="refresh-btn">
          Refresh
        </button>
      </div>

      <div className="table-container">
        <table className="lines-table">
          <thead>
            <tr>
              <th onClick={() => handleSort('line_id')}>
                Line ID {getSortIcon('line_id')}
              </th>
              <th onClick={() => handleSort('line_name')}>
                Name {getSortIcon('line_name')}
              </th>
              <th onClick={() => handleSort('voltage_kv')}>
                Voltage {getSortIcon('voltage_kv')}
              </th>
              <th onClick={() => handleSort('conductor')}>
                Conductor {getSortIcon('conductor')}
              </th>
              <th onClick={() => handleSort('static_rating_mva')}>
                Static Rating (MVA) {getSortIcon('static_rating_mva')}
              </th>
              <th onClick={() => handleSort('ampacity_mva')}>
                Dynamic Rating (MVA) {getSortIcon('ampacity_mva')}
              </th>
              <th onClick={() => handleSort('predicted_load_mw')}>
                Current Load (MW) {getSortIcon('predicted_load_mw')}
              </th>
              <th onClick={() => handleSort('utilization_pct')}>
                Utilization % {getSortIcon('utilization_pct')}
              </th>
              <th onClick={() => handleSort('status')}>
                Status {getSortIcon('status')}
              </th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredLines.map((line) => (
              <tr key={line.line_id} className={`row-${line.status.toLowerCase()}`}>
                <td className="line-id-col">{line.line_id}</td>
                <td className="line-name-col" title={line.line_name}>
                  {line.line_name.length > 40
                    ? line.line_name.substring(0, 40) + '...'
                    : line.line_name}
                </td>
                <td>{line.voltage_kv} kV</td>
                <td title={line.conductor}>{line.conductor.substring(0, 20)}...</td>
                <td className="rating-col">
                  <strong>{line.static_rating_mva?.toFixed(1) || 'N/A'}</strong>
                  <div className="rating-note">CSV s_nom</div>
                </td>
                <td className="rating-col">
                  <strong>{line.ampacity_mva?.toFixed(1) || 'N/A'}</strong>
                  {line.capacity_increase_pct && (
                    <div className="rating-note" style={{ color: line.capacity_increase_pct > 0 ? '#10b981' : '#6b7280' }}>
                      {line.capacity_increase_pct > 0 ? '+' : ''}{line.capacity_increase_pct.toFixed(1)}%
                    </div>
                  )}
                </td>
                <td>{line.predicted_load_mw?.toFixed(1) || 'N/A'}</td>
                <td>
                  <div className="utilization-cell">
                    <span className="utilization-value">
                      {line.utilization_pct?.toFixed(1) || '0.0'}%
                    </span>
                    <div className="mini-bar">
                      <div
                        className={`mini-bar-fill ${line.status.toLowerCase()}`}
                        style={{ width: `${Math.min(line.utilization_pct || 0, 100)}%` }}
                      ></div>
                    </div>
                  </div>
                </td>
                <td>{getStatusBadge(line.status)}</td>
                <td>
                  <button
                    className="view-btn"
                    onClick={() => onLineSelect && onLineSelect(line.line_id)}
                  >
                    View Details
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {filteredLines.length === 0 && (
          <div className="no-results">
            No lines found matching your filters.
          </div>
        )}
      </div>

      <div className="table-footer">
        Showing {filteredLines.length} of {lines.length} lines
      </div>
    </div>
  );
};

export default TableView;
