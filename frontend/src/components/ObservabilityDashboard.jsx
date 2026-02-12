/**
 * Observability Dashboard Component
 * Real-time metrics, logs, traces, and alerts monitoring
 * Phase 42: Observability & Monitoring Infrastructure
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Grid,
  Typography,
  Chip,
  Tabs,
  Tab,
  TextField,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Alert,
  LinearProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  Refresh as RefreshIcon,
  Search as SearchIcon,
  Download as DownloadIcon,
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as ChartTooltip,
  Legend,
  ResponsiveContainer,
  ScatterChart,
  Scatter,
} from 'recharts';

// Alert severity colors
const severityColors = {
  critical: '#f44336',
  high: '#ff9800',
  medium: '#ffc107',
  low: '#4caf50',
  info: '#2196f3',
};

const severityIcons = {
  critical: <ErrorIcon style={{ color: severityColors.critical }} />,
  high: <WarningIcon style={{ color: severityColors.high }} />,
  medium: <WarningIcon style={{ color: severityColors.medium }} />,
  low: <CheckCircleIcon style={{ color: severityColors.low }} />,
  info: <InfoIcon style={{ color: severityColors.info }} />,
};

/**
 * Metrics Panel Component
 */
const MetricsPanel = () => {
  const [metricsData, setMetricsData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedMetric, setSelectedMetric] = useState(null);

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const response = await fetch('/api/v1/observability/metrics');
        if (!response.ok) throw new Error('Failed to fetch metrics');
        const data = await response.json();
        setMetricsData(data.metrics || []);
      } catch (error) {
        console.error('Error fetching metrics:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchMetrics();
    const interval = setInterval(fetchMetrics, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <Card>
      <CardHeader
        title="📊 Metrics"
        action={
          <Tooltip title="Refresh">
            <IconButton size="small">
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        }
      />
      <CardContent>
        {loading ? (
          <LinearProgress />
        ) : (
          <Grid container spacing={2}>
            {metricsData.map((metric, idx) => (
              <Grid item xs={12} sm={6} md={4} key={idx}>
                <Card style={{ background: '#f5f5f5' }}>
                  <CardContent>
                    <Typography variant="subtitle2" color="textSecondary">
                      {metric.name}
                    </Typography>
                    <Typography variant="h5" style={{ marginTop: '8px', marginBottom: '8px' }}>
                      {metric.value?.toFixed(2) || 'N/A'} {metric.unit}
                    </Typography>
                    <Box display="flex" alignItems="center" gap={1}>
                      {metric.trend === 'up' ? (
                        <TrendingUpIcon style={{ color: '#ff9800' }} />
                      ) : (
                        <TrendingDownIcon style={{ color: '#4caf50' }} />
                      )}
                      <Typography variant="caption" color="textSecondary">
                        {metric.change?.toFixed(1) || 0}%
                      </Typography>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        )}
      </CardContent>
    </Card>
  );
};

/**
 * Alerts Panel Component
 */
const AlertsPanel = () => {
  const [alerts, setAlerts] = useState([]);
  const [statistics, setStatistics] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        const response = await fetch('/api/v1/observability/alerts');
        if (!response.ok) throw new Error('Failed to fetch alerts');
        const data = await response.json();
        setAlerts(data.alerts || []);
        setStatistics(data.statistics || {});
      } catch (error) {
        console.error('Error fetching alerts:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchAlerts();
    const interval = setInterval(fetchAlerts, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleAcknowledge = async (alertId) => {
    try {
      await fetch(`/api/v1/observability/alerts/${alertId}/acknowledge`, {
        method: 'POST',
      });
    } catch (error) {
      console.error('Error acknowledging alert:', error);
    }
  };

  const handleResolve = async (alertId) => {
    try {
      await fetch(`/api/v1/observability/alerts/${alertId}/resolve`, {
        method: 'POST',
      });
    } catch (error) {
      console.error('Error resolving alert:', error);
    }
  };

  return (
    <Card>
      <CardHeader
        title="🚨 Alerts"
        action={
          <Box display="flex" gap={1}>
            <Chip label={`Active: ${statistics.active_alerts || 0}`} color="error" />
            <Chip label={`Critical: ${statistics.critical_count || 0}`} color="error" />
            <Tooltip title="Refresh">
              <IconButton size="small">
                <RefreshIcon />
              </IconButton>
            </Tooltip>
          </Box>
        }
      />
      <CardContent>
        {loading ? (
          <LinearProgress />
        ) : alerts.length > 0 ? (
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow style={{ background: '#f5f5f5' }}>
                  <TableCell>Severity</TableCell>
                  <TableCell>Alert</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Current Value</TableCell>
                  <TableCell>Triggered At</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {alerts.map((alert) => (
                  <TableRow key={alert.id}>
                    <TableCell>{severityIcons[alert.severity]}</TableCell>
                    <TableCell>
                      <Typography variant="body2">{alert.rule}</Typography>
                      <Typography variant="caption" color="textSecondary">
                        {alert.message}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={alert.status}
                        size="small"
                        color={alert.status === 'firing' ? 'error' : alert.status === 'acknowledged' ? 'warning' : 'default'}
                      />
                    </TableCell>
                    <TableCell>{alert.current_value?.toFixed(2) || 'N/A'}</TableCell>
                    <TableCell>
                      <Typography variant="caption">
                        {new Date(alert.triggered_at).toLocaleString()}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      {alert.status === 'firing' && (
                        <>
                          <Button
                            size="small"
                            onClick={() => handleAcknowledge(alert.id)}
                            style={{ marginRight: '4px' }}
                          >
                            Ack
                          </Button>
                          <Button
                            size="small"
                            onClick={() => handleResolve(alert.id)}
                            color="primary"
                          >
                            Resolve
                          </Button>
                        </>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        ) : (
          <Typography color="textSecondary">No active alerts</Typography>
        )}
      </CardContent>
    </Card>
  );
};

/**
 * Traces Panel Component
 */
const TracesPanel = () => {
  const [traces, setTraces] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTraceId, setSearchTraceId] = useState('');

  useEffect(() => {
    const fetchTraces = async () => {
      try {
        const response = await fetch('/api/v1/observability/traces');
        if (!response.ok) throw new Error('Failed to fetch traces');
        const data = await response.json();
        setTraces(data.traces || []);
      } catch (error) {
        console.error('Error fetching traces:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchTraces();
    const interval = setInterval(fetchTraces, 60000);
    return () => clearInterval(interval);
  }, []);

  const handleSearch = async () => {
    if (!searchTraceId) return;
    try {
      const response = await fetch(`/api/v1/observability/traces/${searchTraceId}`);
      if (!response.ok) throw new Error('Trace not found');
      const data = await response.json();
      setTraces([data.trace]);
    } catch (error) {
      console.error('Error searching trace:', error);
    }
  };

  return (
    <Card>
      <CardHeader
        title="🔍 Distributed Traces"
        action={
          <Box display="flex" gap={1}>
            <TextField
              size="small"
              placeholder="Search trace ID..."
              value={searchTraceId}
              onChange={(e) => setSearchTraceId(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            />
            <Button size="small" onClick={handleSearch}>
              <SearchIcon />
            </Button>
          </Box>
        }
      />
      <CardContent>
        {loading ? (
          <LinearProgress />
        ) : traces.length > 0 ? (
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow style={{ background: '#f5f5f5' }}>
                  <TableCell>Trace ID</TableCell>
                  <TableCell>Span Count</TableCell>
                  <TableCell>Duration (ms)</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Started At</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {traces.map((trace) => (
                  <TableRow key={trace.trace_id}>
                    <TableCell>
                      <Typography variant="caption" style={{ fontFamily: 'monospace' }}>
                        {trace.trace_id.substring(0, 8)}...
                      </Typography>
                    </TableCell>
                    <TableCell>{trace.span_count}</TableCell>
                    <TableCell>{trace.duration_ms?.toFixed(2) || 'N/A'}</TableCell>
                    <TableCell>
                      <Chip
                        label={trace.status || 'completed'}
                        size="small"
                        color={trace.status === 'error' ? 'error' : 'default'}
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="caption">
                        {new Date(trace.start_time).toLocaleString()}
                      </Typography>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        ) : (
          <Typography color="textSecondary">No traces found</Typography>
        )}
      </CardContent>
    </Card>
  );
};

/**
 * Logs Panel Component
 */
const LogsPanel = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [logLevel, setLogLevel] = useState('all');
  const [searchText, setSearchText] = useState('');

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const params = new URLSearchParams();
        if (logLevel !== 'all') params.append('level', logLevel);
        if (searchText) params.append('search', searchText);

        const response = await fetch(`/api/v1/observability/logs?${params}`);
        if (!response.ok) throw new Error('Failed to fetch logs');
        const data = await response.json();
        setLogs(data.logs || []);
      } catch (error) {
        console.error('Error fetching logs:', error);
      } finally {
        setLoading(false);
      }
    };

    const timer = setTimeout(fetchLogs, 300);
    return () => clearTimeout(timer);
  }, [logLevel, searchText]);

  const getLevelColor = (level) => {
    switch (level) {
      case 'CRITICAL':
      case 'ERROR':
        return '#f44336';
      case 'WARNING':
        return '#ff9800';
      case 'INFO':
        return '#2196f3';
      default:
        return '#9e9e9e';
    }
  };

  return (
    <Card>
      <CardHeader
        title="📋 Logs"
        action={
          <Box display="flex" gap={1}>
            <select
              value={logLevel}
              onChange={(e) => setLogLevel(e.target.value)}
              style={{ padding: '8px', borderRadius: '4px', border: '1px solid #ddd' }}
            >
              <option value="all">All Levels</option>
              <option value="DEBUG">Debug</option>
              <option value="INFO">Info</option>
              <option value="WARNING">Warning</option>
              <option value="ERROR">Error</option>
              <option value="CRITICAL">Critical</option>
            </select>
            <TextField
              size="small"
              placeholder="Search logs..."
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
            />
          </Box>
        }
      />
      <CardContent>
        {loading ? (
          <LinearProgress />
        ) : logs.length > 0 ? (
          <Box style={{ maxHeight: '400px', overflow: 'auto' }}>
            {logs.map((log, idx) => (
              <Box
                key={idx}
                padding={1}
                marginBottom={1}
                style={{
                  background: '#f5f5f5',
                  borderLeft: `4px solid ${getLevelColor(log.level)}`,
                  borderRadius: '4px',
                }}
              >
                <Box display="flex" justifyContent="space-between" marginBottom={0.5}>
                  <Chip label={log.level} size="small" />
                  <Typography variant="caption" color="textSecondary">
                    {new Date(log.timestamp).toLocaleTimeString()}
                  </Typography>
                </Box>
                <Typography variant="body2">{log.message}</Typography>
                {log.trace_id && (
                  <Typography variant="caption" color="textSecondary">
                    Trace: {log.trace_id.substring(0, 8)}...
                  </Typography>
                )}
              </Box>
            ))}
          </Box>
        ) : (
          <Typography color="textSecondary">No logs found</Typography>
        )}
      </CardContent>
    </Card>
  );
};

/**
 * Main Observability Dashboard Component
 */
const ObservabilityDashboard = () => {
  const [selectedTab, setSelectedTab] = useState(0);
  const [systemStats, setSystemStats] = useState({});

  useEffect(() => {
    const fetchSystemStats = async () => {
      try {
        const response = await fetch('/api/v1/observability/system-stats');
        if (!response.ok) throw new Error('Failed to fetch system stats');
        const data = await response.json();
        setSystemStats(data);
      } catch (error) {
        console.error('Error fetching system stats:', error);
      }
    };

    fetchSystemStats();
    const interval = setInterval(fetchSystemStats, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <Box padding={3}>
      {/* Header */}
      <Box marginBottom={3}>
        <Typography variant="h4" gutterBottom>
          📊 Observability Dashboard
        </Typography>
        <Typography variant="body1" color="textSecondary">
          Real-time metrics, logs, traces, and alerts monitoring
        </Typography>
      </Box>

      {/* System Statistics Cards */}
      <Grid container spacing={2} marginBottom={3}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Uptime
              </Typography>
              <Typography variant="h5">{systemStats.uptime_hours || 0}h</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                CPU Usage
              </Typography>
              <Typography variant="h5">{systemStats.cpu_percent?.toFixed(1) || 0}%</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Memory Usage
              </Typography>
              <Typography variant="h5">{systemStats.memory_percent?.toFixed(1) || 0}%</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Active Requests
              </Typography>
              <Typography variant="h5">{systemStats.active_requests || 0}</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabs for different observability views */}
      <Card>
        <Tabs value={selectedTab} onChange={(e, newTab) => setSelectedTab(newTab)}>
          <Tab label="Metrics" />
          <Tab label="Alerts" />
          <Tab label="Traces" />
          <Tab label="Logs" />
        </Tabs>

        <Box padding={2}>
          {selectedTab === 0 && <MetricsPanel />}
          {selectedTab === 1 && <AlertsPanel />}
          {selectedTab === 2 && <TracesPanel />}
          {selectedTab === 3 && <LogsPanel />}
        </Box>
      </Card>
    </Box>
  );
};

export default ObservabilityDashboard;
