/**
 * TimeLapse Component
 * Animated 24-hour visualization of grid utilization
 */

import { useState, useEffect, useRef } from 'react';
import apiService from '../services/api';
import './TimeLapse.css';

const TimeLapse = ({ customWeather }) => {
  const [timelapseData, setTimelapseData] = useState(null);
  const [currentHour, setCurrentHour] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState(500); // milliseconds per hour
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const animationRef = useRef(null);

  // Fetch time-lapse data
  useEffect(() => {
    fetchTimelapseData();
  }, [JSON.stringify(customWeather)]);

  // Animation loop
  useEffect(() => {
    if (isPlaying && timelapseData) {
      animationRef.current = setInterval(() => {
        setCurrentHour((prev) => {
          if (prev >= 23) {
            return 0; // Loop back to start
          }
          return prev + 1;
        });
      }, speed);
    }

    return () => {
      if (animationRef.current) {
        clearInterval(animationRef.current);
      }
    };
  }, [isPlaying, speed, timelapseData]);

  const fetchTimelapseData = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiService.get24HourTimelapse(customWeather);
      setTimelapseData(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handlePlayPause = () => {
    setIsPlaying(!isPlaying);
  };

  const handleStop = () => {
    setIsPlaying(false);
    setCurrentHour(0);
  };

  const handleSpeedChange = (newSpeed) => {
    setSpeed(newSpeed);
  };

  const handleHourChange = (hour) => {
    setCurrentHour(hour);
    setIsPlaying(false);
  };

  if (loading) {
    return (
      <div className="timelapse-loading">
        <div className="spinner"></div>
        <p>Loading 24-hour simulation...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="timelapse-error">
        <p>Error loading time-lapse: {error}</p>
        <button onClick={fetchTimelapseData}>Retry</button>
      </div>
    );
  }

  if (!timelapseData) {
    return null;
  }

  const currentSnapshot = timelapseData.snapshots[currentHour];
  const summary = currentSnapshot.summary;

  return (
    <div className="timelapse-container">
      {/* Header */}
      <div className="timelapse-header">
        <h2>24-Hour Grid Time-Lapse</h2>
        <p>Watch how line utilization changes throughout the day</p>
      </div>

      {/* Current Time Display */}
      <div className="time-display-large">
        <div className="current-time">
          <span className="time-text">{currentSnapshot.time_label}</span>
        </div>
        <div className="time-metadata">
          <span className="load-factor">
            Load Factor: <strong>{(currentSnapshot.load_factor * 100).toFixed(0)}%</strong>
          </span>
          <span className="solar-info">
            Solar: <strong>{currentSnapshot.solar_altitude}°</strong>
          </span>
        </div>
      </div>

      {/* Status Summary */}
      <div className="status-summary-large">
        <div className="summary-card critical">
          <div className="summary-count">{summary.critical}</div>
          <div className="summary-label">Critical Lines</div>
        </div>
        <div className="summary-card warning">
          <div className="summary-count">{summary.warning}</div>
          <div className="summary-label">Warning Lines</div>
        </div>
        <div className="summary-card normal">
          <div className="summary-count">{summary.normal}</div>
          <div className="summary-label">Normal Lines</div>
        </div>
      </div>

      {/* Playback Controls */}
      <div className="playback-controls">
        <button
          className={`control-btn play-btn ${isPlaying ? 'playing' : ''}`}
          onClick={handlePlayPause}
        >
          {isPlaying ? 'Pause' : 'Play'}
        </button>
        <button className="control-btn stop-btn" onClick={handleStop}>
          Stop
        </button>

        {/* Speed Control */}
        <div className="speed-control">
          <label>Speed:</label>
          <button
            className={`speed-btn ${speed === 1000 ? 'active' : ''}`}
            onClick={() => handleSpeedChange(1000)}
          >
            1x
          </button>
          <button
            className={`speed-btn ${speed === 500 ? 'active' : ''}`}
            onClick={() => handleSpeedChange(500)}
          >
            2x
          </button>
          <button
            className={`speed-btn ${speed === 250 ? 'active' : ''}`}
            onClick={() => handleSpeedChange(250)}
          >
            4x
          </button>
        </div>
      </div>

      {/* Timeline Scrubber */}
      <div className="timeline-scrubber">
        <input
          type="range"
          min="0"
          max="23"
          step="1"
          value={currentHour}
          onChange={(e) => handleHourChange(parseInt(e.target.value))}
          className="timeline-slider"
        />
        <div className="timeline-markers">
          <span onClick={() => handleHourChange(0)}>12 AM</span>
          <span onClick={() => handleHourChange(6)}>6 AM</span>
          <span onClick={() => handleHourChange(12)}>12 PM</span>
          <span onClick={() => handleHourChange(18)}>6 PM</span>
          <span onClick={() => handleHourChange(23)}>11 PM</span>
        </div>
      </div>

      {/* Line Status Grid */}
      <div className="lines-status-grid">
        <h3>Line Status at {currentSnapshot.time_label}</h3>
        <div className="grid-container">
          {currentSnapshot.lines.slice(0, 20).map((line) => (
            <div
              key={line.line_id}
              className={`line-status-box ${line.status.toLowerCase()}`}
              title={`${line.line_id}: ${line.utilization_pct}% utilization`}
            >
              <div className="line-id">{line.line_id}</div>
              <div className="line-utilization">{line.utilization_pct}%</div>
            </div>
          ))}
        </div>
        <p className="grid-note">Showing 20 of {summary.total_lines} lines</p>
      </div>

      {/* Historical Chart */}
      <div className="historical-chart">
        <h3>Line Status Throughout the Day</h3>
        <div className="chart-bars">
          {timelapseData.snapshots.map((snapshot, index) => {
            const criticalPct = (snapshot.summary.critical / snapshot.summary.total_lines) * 100;
            const warningPct = (snapshot.summary.warning / snapshot.summary.total_lines) * 100;
            const normalPct = (snapshot.summary.normal / snapshot.summary.total_lines) * 100;

            return (
              <div
                key={index}
                className={`hour-bar ${index === currentHour ? 'current' : ''}`}
                onClick={() => handleHourChange(index)}
              >
                <div className="stacked-bar">
                  <div
                    className="bar-segment critical"
                    style={{ height: `${criticalPct}%` }}
                    title={`${snapshot.summary.critical} critical`}
                  ></div>
                  <div
                    className="bar-segment warning"
                    style={{ height: `${warningPct}%` }}
                    title={`${snapshot.summary.warning} warning`}
                  ></div>
                  <div
                    className="bar-segment normal"
                    style={{ height: `${normalPct}%` }}
                    title={`${snapshot.summary.normal} normal`}
                  ></div>
                </div>
                <div className="hour-label">{index}h</div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default TimeLapse;
