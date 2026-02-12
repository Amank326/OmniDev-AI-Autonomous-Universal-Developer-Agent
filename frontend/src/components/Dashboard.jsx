/**
 * Phase 23: Dashboard Component
 * Dynamic dashboard with drag-drop widgets, real-time updates, filtering
 */

import React, { useState, useEffect, useCallback } from 'react';
import PropTypes from 'prop-types';
import './Dashboard.css';

const Dashboard = ({ dashboardId, onWidgetUpdate, onDashboardSave }) => {
  const [dashboard, setDashboard] = useState(null);
  const [widgets, setWidgets] = useState([]);
  const [filters, setFilters] = useState({});
  const [isEditMode, setIsEditMode] = useState(false);
  const [draggedWidget, setDraggedWidget] = useState(null);
  const [gridLayout, setGridLayout] = useState([]);
  const [theme, setTheme] = useState('light');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch dashboard on mount
  useEffect(() => {
    loadDashboard();
    const interval = setInterval(refreshWidgets, 60000); // Auto-refresh every minute
    return () => clearInterval(interval);
  }, [dashboardId]);

  const loadDashboard = useCallback(async () => {
    try {
      setIsLoading(true);
      const response = await fetch(`/api/v1/bi/dashboards/${dashboardId}`);
      if (!response.ok) throw new Error('Failed to load dashboard');
      
      const data = await response.json();
      setDashboard(data);
      setWidgets(data.widgets || []);
      setGridLayout(data.layout || []);
      setTheme(data.theme || 'light');
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, [dashboardId]);

  const refreshWidgets = useCallback(() => {
    // Refresh data for all widgets
    widgets.forEach(widget => {
      if (widget.refresh_interval > 0) {
        refreshWidget(widget.id);
      }
    });
  }, [widgets]);

  const refreshWidget = async (widgetId) => {
    try {
      const response = await fetch(
        `/api/v1/bi/dashboards/${dashboardId}/widgets/${widgetId}/refresh`,
        { method: 'POST' }
      );
      if (response.ok) {
        const data = await response.json();
        setWidgets(prev => prev.map(w => 
          w.id === widgetId ? { ...w, ...data } : w
        ));
      }
    } catch (err) {
      console.error(`Failed to refresh widget ${widgetId}:`, err);
    }
  };

  const handleAddWidget = useCallback(() => {
    const newWidget = {
      id: `widget_${Date.now()}`,
      type: 'metric',
      title: 'New Widget',
      size: { width: 2, height: 1 },
      position: { x: 0, y: 0 },
      config: {},
      refresh_interval: 300,
    };
    setWidgets([...widgets, newWidget]);
  }, [widgets]);

  const handleRemoveWidget = useCallback((widgetId) => {
    setWidgets(widgets.filter(w => w.id !== widgetId));
  }, [widgets]);

  const handleWidgetDragStart = (widget) => {
    if (!isEditMode) return;
    setDraggedWidget(widget);
  };

  const handleWidgetDragOver = (e) => {
    e.preventDefault();
  };

  const handleWidgetDrop = (e, position) => {
    e.preventDefault();
    if (!draggedWidget || !isEditMode) return;

    setWidgets(widgets.map(w => 
      w.id === draggedWidget.id 
        ? { ...w, position }
        : w
    ));
    setDraggedWidget(null);
  };

  const handleResizeWidget = (widgetId, newSize) => {
    setWidgets(widgets.map(w => 
      w.id === widgetId ? { ...w, size: newSize } : w
    ));
  };

  const handleWidgetConfig = (widgetId, config) => {
    setWidgets(widgets.map(w => 
      w.id === widgetId ? { ...w, config } : w
    ));
    if (onWidgetUpdate) {
      onWidgetUpdate(widgetId, config);
    }
  };

  const handleFilterChange = (filterId, value) => {
    setFilters({ ...filters, [filterId]: value });
    applyFiltersToWidgets();
  };

  const applyFiltersToWidgets = () => {
    // Apply active filters to all widgets
    widgets.forEach(widget => {
      if (widget.filter_linking && widget.filter_linking.length > 0) {
        // Update widget data based on filters
        refreshWidget(widget.id);
      }
    });
  };

  const handleSaveDashboard = async () => {
    try {
      const payload = {
        name: dashboard.name,
        widgets,
        layout: gridLayout,
        filters: Object.keys(filters).map(filterId => ({
          id: filterId,
          value: filters[filterId],
        })),
        theme,
      };

      const response = await fetch(
        `/api/v1/bi/dashboards/${dashboardId}`,
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        }
      );

      if (!response.ok) throw new Error('Failed to save dashboard');
      
      setIsEditMode(false);
      if (onDashboardSave) {
        onDashboardSave(dashboardId);
      }
    } catch (err) {
      setError(err.message);
    }
  };

  const handleExportDashboard = async (format = 'pdf') => {
    try {
      const response = await fetch(
        `/api/v1/bi/dashboards/${dashboardId}/export`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ format }),
        }
      );

      if (response.ok) {
        const data = await response.json();
        window.location.href = data.download_url;
      }
    } catch (err) {
      setError(err.message);
    }
  };

  const handleShareDashboard = async () => {
    const recipients = prompt('Enter recipient emails (comma-separated):');
    if (!recipients) return;

    try {
      const response = await fetch(
        `/api/v1/bi/dashboards/${dashboardId}/share`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            recipients: recipients.split(',').map(e => e.trim()),
            access_level: 'view',
          }),
        }
      );

      if (response.ok) {
        alert('Dashboard shared successfully!');
      }
    } catch (err) {
      setError(err.message);
    }
  };

  if (isLoading) {
    return (
      <div className={`dashboard dashboard--${theme}`}>
        <div className="dashboard__loader">Loading dashboard...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`dashboard dashboard--${theme}`}>
        <div className="dashboard__error">{error}</div>
      </div>
    );
  }

  return (
    <div className={`dashboard dashboard--${theme}`}>
      {/* Header */}
      <div className="dashboard__header">
        <div className="dashboard__title-section">
          <h1 className="dashboard__title">{dashboard?.name}</h1>
          <button
            className={`dashboard__edit-btn ${isEditMode ? 'active' : ''}`}
            onClick={() => setIsEditMode(!isEditMode)}
          >
            {isEditMode ? '✓ Done' : '✎ Edit'}
          </button>
        </div>

        <div className="dashboard__controls">
          <button
            className="dashboard__control-btn"
            onClick={() => refreshWidgets()}
            title="Refresh all widgets"
          >
            ↻ Refresh
          </button>
          <select
            className="dashboard__theme-selector"
            value={theme}
            onChange={(e) => setTheme(e.target.value)}
          >
            <option value="light">Light</option>
            <option value="dark">Dark</option>
            <option value="contrast">High Contrast</option>
          </select>
          <button
            className="dashboard__control-btn"
            onClick={() => handleExportDashboard('pdf')}
            title="Export as PDF"
          >
            📄 Export
          </button>
          <button
            className="dashboard__control-btn"
            onClick={handleShareDashboard}
            title="Share dashboard"
          >
            🔗 Share
          </button>
          {isEditMode && (
            <button
              className="dashboard__save-btn"
              onClick={handleSaveDashboard}
            >
              💾 Save
            </button>
          )}
        </div>
      </div>

      {/* Filters */}
      <div className="dashboard__filters">
        {dashboard?.filters?.map(filter => (
          <div key={filter.id} className="dashboard__filter">
            <label className="dashboard__filter-label">{filter.name}</label>
            {filter.type === 'dropdown' && (
              <select
                className="dashboard__filter-input"
                value={filters[filter.id] || ''}
                onChange={(e) => handleFilterChange(filter.id, e.target.value)}
              >
                <option value="">All</option>
                {filter.options?.map(opt => (
                  <option key={opt} value={opt}>{opt}</option>
                ))}
              </select>
            )}
            {filter.type === 'date' && (
              <input
                type="date"
                className="dashboard__filter-input"
                value={filters[filter.id] || ''}
                onChange={(e) => handleFilterChange(filter.id, e.target.value)}
              />
            )}
            {filter.type === 'text' && (
              <input
                type="text"
                className="dashboard__filter-input"
                placeholder="Search..."
                value={filters[filter.id] || ''}
                onChange={(e) => handleFilterChange(filter.id, e.target.value)}
              />
            )}
            {filter.type === 'range' && (
              <input
                type="range"
                className="dashboard__filter-input"
                min={filter.min}
                max={filter.max}
                value={filters[filter.id] || filter.min}
                onChange={(e) => handleFilterChange(filter.id, e.target.value)}
              />
            )}
          </div>
        ))}
      </div>

      {/* Widgets Grid */}
      <div className="dashboard__grid">
        {widgets.map(widget => (
          <DashboardWidget
            key={widget.id}
            widget={widget}
            isEditMode={isEditMode}
            onRemove={() => handleRemoveWidget(widget.id)}
            onResize={(size) => handleResizeWidget(widget.id, size)}
            onConfig={(config) => handleWidgetConfig(widget.id, config)}
            onDragStart={() => handleWidgetDragStart(widget)}
            onDragOver={handleWidgetDragOver}
            onDrop={(e, pos) => handleWidgetDrop(e, pos)}
          />
        ))}

        {isEditMode && (
          <button
            className="dashboard__add-widget-btn"
            onClick={handleAddWidget}
          >
            + Add Widget
          </button>
        )}
      </div>
    </div>
  );
};

Dashboard.propTypes = {
  dashboardId: PropTypes.string.isRequired,
  onWidgetUpdate: PropTypes.func,
  onDashboardSave: PropTypes.func,
};

/**
 * DashboardWidget Component
 * Represents a single widget in the dashboard
 */
const DashboardWidget = ({
  widget,
  isEditMode,
  onRemove,
  onResize,
  onConfig,
  onDragStart,
  onDragOver,
  onDrop,
}) => {
  const [showConfig, setShowConfig] = useState(false);
  const [configData, setConfigData] = useState(widget.config || {});

  const handleResize = (direction, e) => {
    e.preventDefault();
    const startX = e.clientX;
    const startY = e.clientY;
    const startWidth = widget.size.width;
    const startHeight = widget.size.height;

    const handleMouseMove = (moveEvent) => {
      const deltaX = moveEvent.clientX - startX;
      const deltaY = moveEvent.clientY - startY;

      const newSize = {
        width: Math.max(1, startWidth + deltaX / 100),
        height: Math.max(1, startHeight + deltaY / 100),
      };
      onResize(newSize);
    };

    const handleMouseUp = () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
  };

  const handleConfigSubmit = () => {
    onConfig(configData);
    setShowConfig(false);
  };

  return (
    <div
      className={`widget ${isEditMode ? 'widget--editable' : ''}`}
      style={{
        gridColumn: `span ${Math.floor(widget.size.width)}`,
        gridRow: `span ${Math.floor(widget.size.height)}`,
      }}
      draggable={isEditMode}
      onDragStart={onDragStart}
      onDragOver={onDragOver}
      onDrop={onDrop}
    >
      {/* Widget Header */}
      <div className="widget__header">
        <h3 className="widget__title">{widget.title}</h3>
        <div className="widget__actions">
          <button
            className="widget__btn widget__config-btn"
            onClick={() => setShowConfig(!showConfig)}
            title="Configure widget"
          >
            ⚙️
          </button>
          {isEditMode && (
            <button
              className="widget__btn widget__delete-btn"
              onClick={onRemove}
              title="Remove widget"
            >
              ✕
            </button>
          )}
        </div>
      </div>

      {/* Widget Content */}
      <div className="widget__content">
        {widget.type === 'chart' && (
          <div className="widget__chart">Chart: {widget.config.chart_type}</div>
        )}
        {widget.type === 'metric' && (
          <div className="widget__metric">
            <div className="widget__metric-value">—</div>
            <div className="widget__metric-label">{widget.config.metric_name}</div>
          </div>
        )}
        {widget.type === 'table' && (
          <div className="widget__table">Data Table</div>
        )}
        {widget.type === 'alert' && (
          <div className="widget__alert">Active Alerts: 0</div>
        )}
        {widget.type === 'filter' && (
          <div className="widget__filter">Filter Widget</div>
        )}
        {widget.type === 'gauge' && (
          <div className="widget__gauge">0%</div>
        )}
        {widget.type === 'card' && (
          <div className="widget__card">{widget.config.content}</div>
        )}
      </div>

      {/* Widget Config Panel */}
      {showConfig && (
        <div className="widget__config-panel">
          <div className="widget__config-field">
            <label>Refresh Interval (seconds)</label>
            <input
              type="number"
              value={configData.refresh_interval || 300}
              onChange={(e) => setConfigData({
                ...configData,
                refresh_interval: parseInt(e.target.value),
              })}
            />
          </div>
          <div className="widget__config-field">
            <label>Title</label>
            <input
              type="text"
              value={configData.title || widget.title}
              onChange={(e) => setConfigData({
                ...configData,
                title: e.target.value,
              })}
            />
          </div>
          <button
            className="widget__config-save"
            onClick={handleConfigSubmit}
          >
            Save
          </button>
        </div>
      )}

      {/* Resize Handle */}
      {isEditMode && (
        <div
          className="widget__resize-handle"
          onMouseDown={(e) => handleResize('southeast', e)}
        />
      )}
    </div>
  );
};

DashboardWidget.propTypes = {
  widget: PropTypes.object.isRequired,
  isEditMode: PropTypes.bool,
  onRemove: PropTypes.func,
  onResize: PropTypes.func,
  onConfig: PropTypes.func,
  onDragStart: PropTypes.func,
  onDragOver: PropTypes.func,
  onDrop: PropTypes.func,
};

export default Dashboard;
