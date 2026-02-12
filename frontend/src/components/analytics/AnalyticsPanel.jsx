/**
 * Phase 25: Analytics Panel Component
 * Advanced charting, analysis dashboard, and report builder
 */

import React, { useState, useEffect, useCallback } from 'react';

const AnalyticsPanel = ({ apiBaseUrl = 'http://localhost:5000' }) => {
  // Analysis state
  const [selectedMetric, setSelectedMetric] = useState(null);
  const [metrics, setMetrics] = useState([]);
  const [analysisType, setAnalysisType] = useState('timeseries');
  const [dateRange, setDateRange] = useState({ start: null, end: null });
  const [analysisData, setAnalysisData] = useState(null);
  const [loading, setLoading] = useState(false);
  
  // Report builder
  const [reportConfig, setReportConfig] = useState({
    name: '',
    metrics: [],
    filters: {},
    format: 'dashboard'
  });
  const [savedReports, setSavedReports] = useState([]);
  
  // Filters
  const [activeFilters, setActiveFilters] = useState({});
  const [filterOptions, setFilterOptions] = useState({});


  // ========================================================================
  // LIFECYCLE
  // ========================================================================

  useEffect(() => {
    loadMetrics();
  }, []);


  // ========================================================================
  // DATA LOADING
  // ========================================================================

  const loadMetrics = useCallback(async () => {
    try {
      setLoading(true);
      const response = await fetch(`${apiBaseUrl}/api/v1/analytics/metrics`);
      const data = await response.json();
      setMetrics(data.metrics || []);
    } catch (error) {
      console.error('Failed to load metrics:', error);
    } finally {
      setLoading(false);
    }
  }, [apiBaseUrl]);

  const runAnalysis = useCallback(async () => {
    if (!selectedMetric || !analysisType) return;
    
    try {
      setLoading(true);
      
      let url = `${apiBaseUrl}/api/v1/analytics`;
      
      switch (analysisType) {
        case 'timeseries':
          url += `/timeseries/${selectedMetric}/aggregate?aggregation=daily`;
          break;
        case 'trend':
          url += `/timeseries/${selectedMetric}/trend`;
          break;
        case 'growth':
          url += `/timeseries/${selectedMetric}/growth`;
          break;
        case 'breakdown':
          url += `/dimensions/${selectedMetric}/breakdown`;
          break;
        default:
          return;
      }
      
      const response = await fetch(url);
      const data = await response.json();
      setAnalysisData(data);
      
    } catch (error) {
      console.error('Analysis failed:', error);
    } finally {
      setLoading(false);
    }
  }, [selectedMetric, analysisType, apiBaseUrl]);


  // ========================================================================
  // FUNNEL ANALYSIS
  // ========================================================================

  const analyzeFunnel = useCallback(async (funnelId) => {
    try {
      setLoading(true);
      const response = await fetch(
        `${apiBaseUrl}/api/v1/analytics/funnels/${funnelId}/analyze`
      );
      const data = await response.json();
      setAnalysisData(data);
      setAnalysisType('funnel');
    } catch (error) {
      console.error('Funnel analysis failed:', error);
    } finally {
      setLoading(false);
    }
  }, [apiBaseUrl]);

  const getFunnelAbandonment = useCallback(async (funnelId, step) => {
    try {
      const response = await fetch(
        `${apiBaseUrl}/api/v1/analytics/funnels/${funnelId}/abandonment?step=${step}`
      );
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Failed to get abandonment data:', error);
      return null;
    }
  }, [apiBaseUrl]);


  // ========================================================================
  // RETENTION ANALYSIS
  // ========================================================================

  const getRetentionCohort = useCallback(async () => {
    try {
      setLoading(true);
      const response = await fetch(`${apiBaseUrl}/api/v1/analytics/retention/cohort`);
      const data = await response.json();
      setAnalysisData(data);
      setAnalysisType('retention');
    } catch (error) {
      console.error('Retention analysis failed:', error);
    } finally {
      setLoading(false);
    }
  }, [apiBaseUrl]);


  // ========================================================================
  // REPORT BUILDER
  // ========================================================================

  const addMetricToReport = useCallback((metricId) => {
    setReportConfig(prev => ({
      ...prev,
      metrics: [...prev.metrics, metricId]
    }));
  }, []);

  const removeMetricFromReport = useCallback((metricId) => {
    setReportConfig(prev => ({
      ...prev,
      metrics: prev.metrics.filter(m => m !== metricId)
    }));
  }, []);

  const createReport = useCallback(async () => {
    if (!reportConfig.name || reportConfig.metrics.length === 0) return;
    
    try {
      setLoading(true);
      const response = await fetch(`${apiBaseUrl}/api/v1/analytics/reports`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(reportConfig)
      });
      
      const data = await response.json();
      setSavedReports(prev => [...prev, data]);
      
      // Reset form
      setReportConfig({
        name: '',
        metrics: [],
        filters: {},
        format: 'dashboard'
      });
      
    } catch (error) {
      console.error('Failed to create report:', error);
    } finally {
      setLoading(false);
    }
  }, [reportConfig, apiBaseUrl]);

  const exportReport = useCallback(async (reportId, format) => {
    try {
      const response = await fetch(
        `${apiBaseUrl}/api/v1/analytics/reports/${reportId}/export?format=${format}`
      );
      const data = await response.json();
      window.location.href = data.download_url;
    } catch (error) {
      console.error('Failed to export report:', error);
    }
  }, [apiBaseUrl]);


  // ========================================================================
  // FILTERING
  // ========================================================================

  const applyFilter = useCallback((filterKey, filterValue) => {
    setActiveFilters(prev => ({
      ...prev,
      [filterKey]: filterValue
    }));
  }, []);

  const clearFilters = useCallback(() => {
    setActiveFilters({});
  }, []);


  // ========================================================================
  // RENDER
  // ========================================================================

  const renderChart = () => {
    if (!analysisData) {
      return (
        <div style={{ padding: '40px', textAlign: 'center', color: '#999' }}>
          Select metric and analysis type to begin
        </div>
      );
    }

    if (analysisType === 'timeseries') {
      return (
        <div style={{ padding: '20px' }}>
          <h3>Time Series Data</h3>
          <div style={{ height: '300px', backgroundColor: '#f9f9f9' }}>
            {/* Chart placeholder */}
            {analysisData.data && (
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #ddd' }}>
                    <th style={{ padding: '8px', textAlign: 'left' }}>Timestamp</th>
                    <th style={{ padding: '8px', textAlign: 'left' }}>Value</th>
                    <th style={{ padding: '8px', textAlign: 'left' }}>Count</th>
                  </tr>
                </thead>
                <tbody>
                  {analysisData.data.slice(0, 5).map((point, idx) => (
                    <tr key={idx} style={{ borderBottom: '1px solid #eee' }}>
                      <td style={{ padding: '8px' }}>{point.timestamp}</td>
                      <td style={{ padding: '8px' }}>{point.value.toFixed(2)}</td>
                      <td style={{ padding: '8px' }}>{point.count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      );
    }

    if (analysisType === 'funnel') {
      return (
        <div style={{ padding: '20px' }}>
          <h3>Funnel Analysis</h3>
          <div style={{ height: '300px' }}>
            {analysisData.steps && analysisData.steps.map((step, idx) => (
              <div key={idx} style={{ marginBottom: '15px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <div style={{ minWidth: '100px' }}>{step.name}</div>
                  <div style={{
                    width: (step.users / 1000) * 200,
                    height: '30px',
                    backgroundColor: '#8884d8',
                    borderRadius: '4px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'flex-end',
                    paddingRight: '10px',
                    color: 'white'
                  }}>
                    {step.users} users
                  </div>
                  <div>{step.conversion.toFixed(1)}%</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      );
    }

    if (analysisType === 'retention') {
      return (
        <div style={{ padding: '20px' }}>
          <h3>Retention Cohort Matrix</h3>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ backgroundColor: '#f5f5f5' }}>
                <th style={{ padding: '8px', border: '1px solid #ddd' }}>Cohort</th>
                <th style={{ padding: '8px', border: '1px solid #ddd' }}>Day 0</th>
                <th style={{ padding: '8px', border: '1px solid #ddd' }}>Day 1</th>
                <th style={{ padding: '8px', border: '1px solid #ddd' }}>Day 7</th>
              </tr>
            </thead>
            <tbody>
              {analysisData.cohorts && analysisData.cohorts.map((cohort, idx) => (
                <tr key={idx}>
                  <td style={{ padding: '8px', border: '1px solid #ddd' }}>{cohort.date}</td>
                  <td style={{ padding: '8px', border: '1px solid #ddd', backgroundColor: '#c8e6c9' }}>
                    {cohort.day_0}%
                  </td>
                  <td style={{ padding: '8px', border: '1px solid #ddd', backgroundColor: '#fff9c4' }}>
                    {cohort.day_1}%
                  </td>
                  <td style={{ padding: '8px', border: '1px solid #ddd', backgroundColor: '#ffccbc' }}>
                    {cohort.day_7}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
    }

    return <div>Analysis visualization</div>;
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'sans-serif' }}>
      <h1>Advanced Analytics Dashboard</h1>

      {/* Control Panel */}
      <div style={{ marginBottom: '20px', padding: '15px', backgroundColor: '#f5f5f5', borderRadius: '8px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '15px', marginBottom: '15px' }}>
          {/* Metric Selection */}
          <div>
            <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
              Select Metric
            </label>
            <select
              value={selectedMetric || ''}
              onChange={(e) => setSelectedMetric(e.target.value)}
              style={{ width: '100%', padding: '8px' }}
            >
              <option value="">-- Choose metric --</option>
              {metrics.map(m => (
                <option key={m.metric_id} value={m.metric_id}>
                  {m.name}
                </option>
              ))}
            </select>
          </div>

          {/* Analysis Type */}
          <div>
            <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
              Analysis Type
            </label>
            <select
              value={analysisType}
              onChange={(e) => setAnalysisType(e.target.value)}
              style={{ width: '100%', padding: '8px' }}
            >
              <option value="timeseries">Time Series</option>
              <option value="trend">Trend</option>
              <option value="growth">Growth</option>
              <option value="breakdown">Breakdown</option>
              <option value="funnel">Funnel</option>
              <option value="retention">Retention</option>
            </select>
          </div>

          {/* Date Range */}
          <div>
            <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>
              Date Range
            </label>
            <select style={{ width: '100%', padding: '8px' }}>
              <option>Last 7 days</option>
              <option>Last 30 days</option>
              <option>Last 90 days</option>
              <option>Custom</option>
            </select>
          </div>
        </div>

        <button
          onClick={runAnalysis}
          disabled={loading || !selectedMetric}
          style={{
            padding: '10px 20px',
            backgroundColor: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            opacity: loading || !selectedMetric ? 0.6 : 1
          }}
        >
          {loading ? 'Analyzing...' : 'Run Analysis'}
        </button>
      </div>

      {/* Main Chart Area */}
      <div style={{
        border: '1px solid #ddd',
        borderRadius: '8px',
        marginBottom: '20px',
        backgroundColor: 'white'
      }}>
        {renderChart()}
      </div>

      {/* Report Builder */}
      <div style={{ marginBottom: '20px', padding: '15px', backgroundColor: '#f9f9f9', borderRadius: '8px' }}>
        <h3>Report Builder</h3>
        
        <div style={{ marginBottom: '15px' }}>
          <label style={{ display: 'block', marginBottom: '5px' }}>
            Report Name
          </label>
          <input
            type="text"
            value={reportConfig.name}
            onChange={(e) => setReportConfig(prev => ({ ...prev, name: e.target.value }))}
            placeholder="Enter report name"
            style={{ width: '300px', padding: '8px' }}
          />
        </div>

        <div style={{ marginBottom: '15px' }}>
          <h4>Selected Metrics:</h4>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px', marginBottom: '10px' }}>
            {reportConfig.metrics.map(m => (
              <div key={m} style={{
                padding: '5px 10px',
                backgroundColor: '#ddd',
                borderRadius: '4px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}>
                {m}
                <button
                  onClick={() => removeMetricFromReport(m)}
                  style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '16px' }}
                >
                  ×
                </button>
              </div>
            ))}
          </div>
          
          <select onChange={(e) => {
            if (e.target.value) {
              addMetricToReport(e.target.value);
              e.target.value = '';
            }
          }} style={{ padding: '8px' }}>
            <option value="">-- Add metric to report --</option>
            {metrics.filter(m => !reportConfig.metrics.includes(m.metric_id)).map(m => (
              <option key={m.metric_id} value={m.metric_id}>
                {m.name}
              </option>
            ))}
          </select>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <button
            onClick={createReport}
            style={{
              padding: '10px 20px',
              backgroundColor: '#28a745',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Create Report
          </button>
          
          <select onChange={(e) => {
            if (e.target.value && savedReports.length > 0) {
              exportReport(savedReports[0].report_id, e.target.value);
              e.target.value = '';
            }
          }} style={{ padding: '8px' }}>
            <option value="">-- Export as --</option>
            <option value="csv">CSV</option>
            <option value="json">JSON</option>
            <option value="pdf">PDF</option>
          </select>
        </div>
      </div>

      {/* Saved Reports */}
      {savedReports.length > 0 && (
        <div style={{ padding: '15px', backgroundColor: '#f0f0f0', borderRadius: '8px' }}>
          <h3>Saved Reports ({savedReports.length})</h3>
          {savedReports.map(report => (
            <div key={report.report_id} style={{
              padding: '10px',
              backgroundColor: 'white',
              marginBottom: '10px',
              borderRadius: '4px'
            }}>
              <strong>{report.name}</strong>
              <div style={{ fontSize: '12px', color: '#666', marginTop: '5px' }}>
                Created: {report.created_at}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default AnalyticsPanel;
