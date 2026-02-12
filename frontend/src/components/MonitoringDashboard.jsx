/**
 * Phase 34: Monitoring Dashboard
 * Comprehensive unified monitoring dashboard with real-time updates
 *
 * Features:
 * - Log viewer with search, filter, and aggregation
 * - Trace timeline and critical path visualization
 * - Metrics charts and comparison
 * - Real-time alerts management
 * - Service dependency visualization
 * - Performance metrics and baselines
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import io from 'socket.io-client';
import {
  Box,
  Container,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Stat,
  StatLabel,
  StatNumber,
  StatGroup,
  Grid,
  GridItem,
  useDisclosure,
  Spinners,
} from '@chakra-ui/react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

// Sub-components
import LogViewer from './monitoring/LogViewer';
import TraceViewer from './monitoring/TraceViewer';
import MetricsViewer from './monitoring/MetricsViewer';
import AlertsManager from './monitoring/AlertsManager';
import ServiceDependencyGraph from './monitoring/ServiceDependencyGraph';

const MonitoringDashboard = ({ workspaceId, apiKey }) => {
  // State management
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // WebSocket connection
  const [wsConnected, setWsConnected] = useState(false);
  const socketRef = useRef(null);
  
  // Monitoring data
  const [dashboardStats, setDashboardStats] = useState({
    totalLogs: 0,
    errorLogs: 0,
    totalTraces: 0,
    errorTraces: 0,
    totalMetrics: 0,
    activeAlerts: 0,
  });
  
  const [recentLogs, setRecentLogs] = useState([]);
  const [recentTraces, setRecentTraces] = useState([]);
  const [recentMetrics, setRecentMetrics] = useState([]);
  const [activeAlerts, setActiveAlerts] = useState([]);
  
  const [metricsChartData, setMetricsChartData] = useState([]);
  const [performanceData, setPerformanceData] = useState([]);
  
  const [serviceDependencies, setServiceDependencies] = useState([]);
  
  // Initialize WebSocket connection
  useEffect(() => {
    const initWebSocket = () => {
      const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
      const wsUrl = `${protocol}://${window.location.host}`;
      
      socketRef.current = io(wsUrl, {
        namespace: '/monitoring',
        extraHeaders: {
          'X-Workspace-ID': workspaceId,
        },
        reconnection: true,
        reconnectionDelay: 1000,
        reconnectionDelayMax: 5000,
        reconnectionAttempts: 5,
      });
      
      // Connection handlers
      socketRef.current.on('connect', () => {
        setWsConnected(true);
        console.log('Connected to monitoring WebSocket');
        
        // Subscribe to all event types
        socketRef.current.emit('subscribe', {
          events: ['logs', 'traces', 'metrics', 'alerts'],
        });
      });
      
      socketRef.current.on('disconnect', () => {
        setWsConnected(false);
        console.log('Disconnected from monitoring WebSocket');
      });
      
      socketRef.current.on('connect_error', (error) => {
        setError(`WebSocket connection error: ${error.message}`);
      });
      
      // Event handlers
      socketRef.current.on('log_event', (data) => {
        handleLogEvent(data);
      });
      
      socketRef.current.on('trace_event', (data) => {
        handleTraceEvent(data);
      });
      
      socketRef.current.on('metric_update', (data) => {
        handleMetricUpdate(data);
      });
      
      socketRef.current.on('metric_aggregation', (data) => {
        handleMetricAggregation(data);
      });
      
      socketRef.current.on('alert_notification', (data) => {
        handleAlertNotification(data);
      });
      
      socketRef.current.on('dashboard_update', (data) => {
        handleDashboardUpdate(data);
      });
    };
    
    initWebSocket();
    
    return () => {
      if (socketRef.current) {
        socketRef.current.disconnect();
      }
    };
  }, [workspaceId]);
  
  // Log event handler
  const handleLogEvent = useCallback((data) => {
    setRecentLogs((prev) => [data.log, ...prev].slice(0, 50));
    setDashboardStats((prev) => ({
      ...prev,
      totalLogs: prev.totalLogs + 1,
      errorLogs: data.log.level === 'ERROR' ? prev.errorLogs + 1 : prev.errorLogs,
    }));
  }, []);
  
  // Trace event handler
  const handleTraceEvent = useCallback((data) => {
    setRecentTraces((prev) => [data.trace, ...prev].slice(0, 30));
    setDashboardStats((prev) => ({
      ...prev,
      totalTraces: prev.totalTraces + 1,
      errorTraces: data.trace.status === 'ERROR' ? prev.errorTraces + 1 : prev.errorTraces,
    }));
  }, []);
  
  // Metric update handler
  const handleMetricUpdate = useCallback((data) => {
    const newMetric = {
      name: data.metric_name,
      value: data.value,
      timestamp: data.timestamp,
      labels: data.labels,
    };
    
    setRecentMetrics((prev) => [newMetric, ...prev].slice(0, 100));
    setMetricsChartData((prev) => {
      const updated = [...prev, { timestamp: new Date(data.timestamp), value: data.value }];
      return updated.slice(-30);
    });
  }, []);
  
  // Metric aggregation handler
  const handleMetricAggregation = useCallback((data) => {
    setPerformanceData((prev) => [
      ...prev,
      {
        metric: data.metric_name,
        period: data.period,
        aggregation: data.aggregation,
        timestamp: data.timestamp,
      },
    ].slice(0, 50));
  }, []);
  
  // Alert notification handler
  const handleAlertNotification = useCallback((data) => {
    setActiveAlerts((prev) => [data.alert, ...prev].slice(0, 50));
    setDashboardStats((prev) => ({
      ...prev,
      activeAlerts: prev.activeAlerts + 1,
    }));
  }, []);
  
  // Dashboard update handler
  const handleDashboardUpdate = useCallback((data) => {
    setDashboardStats((prev) => ({
      ...prev,
      ...data.dashboard,
    }));
  }, []);
  
  // Fetch service dependencies
  useEffect(() => {
    const fetchServiceDependencies = async () => {
      try {
        setLoading(true);
        
        // TODO: Integrate with actual API endpoint
        // For now, using mock data
        const mockDependencies = [
          { source: 'api-gateway', target: 'auth-service', latency: 45 },
          { source: 'auth-service', target: 'user-db', latency: 120 },
          { source: 'api-gateway', target: 'user-service', latency: 78 },
          { source: 'user-service', target: 'user-db', latency: 95 },
          { source: 'api-gateway', target: 'order-service', latency: 156 },
          { source: 'order-service', target: 'order-db', latency: 180 },
        ];
        
        setServiceDependencies(mockDependencies);
        setLoading(false);
      } catch (err) {
        setError(`Failed to fetch service dependencies: ${err.message}`);
        setLoading(false);
      }
    };
    
    fetchServiceDependencies();
  }, [workspaceId]);
  
  // Fetch initial data
  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        setLoading(true);
        
        const headers = {
          'X-Workspace-ID': workspaceId,
          'Authorization': `Bearer ${apiKey}`,
        };
        
        // Fetch logs
        const logsRes = await fetch(`/api/v1/monitoring/logs/get?limit=10`, { headers });
        if (logsRes.ok) {
          const logsData = await logsRes.json();
          setRecentLogs(logsData.logs || []);
          setDashboardStats((prev) => ({
            ...prev,
            totalLogs: logsData.total || 0,
          }));
        }
        
        // Fetch traces
        const tracesRes = await fetch(`/api/v1/monitoring/traces/search`, {
          method: 'POST',
          headers,
          body: JSON.stringify({ limit: 10 }),
        });
        if (tracesRes.ok) {
          const tracesData = await tracesRes.json();
          setRecentTraces(tracesData.traces || []);
          setDashboardStats((prev) => ({
            ...prev,
            totalTraces: tracesData.total || 0,
          }));
        }
        
        // Fetch metrics
        const metricsRes = await fetch(`/api/v1/monitoring/metrics/get`, { headers });
        if (metricsRes.ok) {
          const metricsData = await metricsRes.json();
          setRecentMetrics(metricsData.metrics || []);
          setDashboardStats((prev) => ({
            ...prev,
            totalMetrics: metricsData.total || 0,
          }));
        }
        
        // Fetch alerts
        const alertsRes = await fetch(`/api/v1/monitoring/alerts/get`, { headers });
        if (alertsRes.ok) {
          const alertsData = await alertsRes.json();
          setActiveAlerts(alertsData.alerts || []);
          setDashboardStats((prev) => ({
            ...prev,
            activeAlerts: alertsData.total || 0,
          }));
        }
        
        setLoading(false);
      } catch (err) {
        setError(`Failed to fetch initial data: ${err.message}`);
        setLoading(false);
      }
    };
    
    fetchInitialData();
  }, [workspaceId, apiKey]);
  
  // Dashboard Stats Grid
  const renderStatsPanel = () => (
    <StatGroup>
      <Grid templateColumns="repeat(auto-fit, minmax(200px, 1fr))" gap={4} mb={6}>
        <Stat>
          <StatLabel>Total Logs</StatLabel>
          <StatNumber>{dashboardStats.totalLogs}</StatNumber>
          <Box fontSize="sm" color="red.500">
            {dashboardStats.errorLogs} errors
          </Box>
        </Stat>
        
        <Stat>
          <StatLabel>Total Traces</StatLabel>
          <StatNumber>{dashboardStats.totalTraces}</StatNumber>
          <Box fontSize="sm" color="red.500">
            {dashboardStats.errorTraces} errors
          </Box>
        </Stat>
        
        <Stat>
          <StatLabel>Total Metrics</StatLabel>
          <StatNumber>{dashboardStats.totalMetrics}</StatNumber>
          <Box fontSize="sm" color="gray.500">
            Real-time tracking
          </Box>
        </Stat>
        
        <Stat>
          <StatLabel>Active Alerts</StatLabel>
          <StatNumber color={dashboardStats.activeAlerts > 0 ? 'red.500' : 'green.500'}>
            {dashboardStats.activeAlerts}
          </StatNumber>
          <Box fontSize="sm" color="gray.500">
            Requires attention
          </Box>
        </Stat>
      </Grid>
    </StatGroup>
  );
  
  // Metrics Chart Panel
  const renderMetricsChart = () => {
    if (metricsChartData.length === 0) {
      return <Box p={4}>No metrics data available</Box>;
    }
    
    return (
      <Box p={4} borderWidth={1} borderRadius="lg" mb={6}>
        <Box mb={4} fontSize="lg" fontWeight="bold">
          Metrics Timeline (Last 30 Points)
        </Box>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={metricsChartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="timestamp" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="value" stroke="#8884d8" />
          </LineChart>
        </ResponsiveContainer>
      </Box>
    );
  };
  
  // Performance Data Chart
  const renderPerformanceChart = () => {
    if (performanceData.length === 0) {
      return <Box p={4}>No performance data available</Box>;
    }
    
    const chartData = performanceData.slice(-15).map((item) => ({
      metric: item.metric,
      avg: item.aggregation.avg_value || 0,
      p95: item.aggregation.p95 || 0,
      p99: item.aggregation.p99 || 0,
    }));
    
    return (
      <Box p={4} borderWidth={1} borderRadius="lg" mb={6}>
        <Box mb={4} fontSize="lg" fontWeight="bold">
          Performance Metrics (p95, p99)
        </Box>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="metric" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="avg" fill="#82ca9d" />
            <Bar dataKey="p95" fill="#ffc658" />
            <Bar dataKey="p99" fill="#ff7c7c" />
          </BarChart>
        </ResponsiveContainer>
      </Box>
    );
  };
  
  // Main render
  return (
    <Container maxW="100%" p={6}>
      <Box mb={6}>
        <Box fontSize="2xl" fontWeight="bold" mb={2}>
          Monitoring Dashboard
        </Box>
        <Box fontSize="sm" color={wsConnected ? 'green.500' : 'red.500'}>
          {wsConnected ? '🟢 Connected' : '🔴 Disconnected'} to real-time monitoring
        </Box>
      </Box>
      
      {error && (
        <Box p={4} mb={4} bg="red.50" borderRadius="lg" color="red.800">
          {error}
        </Box>
      )}
      
      {renderStatsPanel()}
      
      {renderMetricsChart()}
      
      {renderPerformanceChart()}
      
      <Tabs index={activeTab} onChange={setActiveTab}>
        <TabList borderBottomWidth={2} borderBottomColor="gray.200">
          <Tab>Logs</Tab>
          <Tab>Traces</Tab>
          <Tab>Metrics</Tab>
          <Tab>Alerts</Tab>
          <Tab>Services</Tab>
        </TabList>
        
        <TabPanels>
          <TabPanel>
            <LogViewer logs={recentLogs} workspaceId={workspaceId} apiKey={apiKey} />
          </TabPanel>
          
          <TabPanel>
            <TraceViewer traces={recentTraces} workspaceId={workspaceId} apiKey={apiKey} />
          </TabPanel>
          
          <TabPanel>
            <MetricsViewer
              metrics={recentMetrics}
              chartData={metricsChartData}
              workspaceId={workspaceId}
              apiKey={apiKey}
            />
          </TabPanel>
          
          <TabPanel>
            <AlertsManager alerts={activeAlerts} workspaceId={workspaceId} apiKey={apiKey} />
          </TabPanel>
          
          <TabPanel>
            <ServiceDependencyGraph dependencies={serviceDependencies} />
          </TabPanel>
        </TabPanels>
      </Tabs>
    </Container>
  );
};

export default MonitoringDashboard;
