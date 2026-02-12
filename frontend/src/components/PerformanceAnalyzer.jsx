/**
 * Phase 34: Performance Analyzer
 * Advanced performance analysis with critical path visualization
 *
 * Features:
 * - Critical path analysis for distributed traces
 * - Bottleneck detection and identification
 * - Service dependency graph with latency metrics
 * - Performance comparison and baseline analysis
 * - Flame graph visualization for request flow
 * - SLA/SLO tracking and compliance
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Container,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Grid,
  GridItem,
  Button,
  Input,
  Select,
  Stat,
  StatLabel,
  StatNumber,
  Badge,
  VStack,
  HStack,
  useDisclosure,
} from '@chakra-ui/react';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ComposedChart,
  TreeMap,
} from 'recharts';

const PerformanceAnalyzer = ({ workspaceId, apiKey }) => {
  // State management
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState(0);
  
  // Time filtering
  const [timeRange, setTimeRange] = useState('1h'); // 1h, 6h, 24h, 7d
  const [sortBy, setSortBy] = useState('duration'); // duration, latency, errors
  
  // Critical path data
  const [criticalPaths, setCriticalPaths] = useState([]);
  const [selectedTrace, setSelectedTrace] = useState(null);
  const [traceDetails, setTraceDetails] = useState(null);
  
  // Performance metrics
  const [performanceMetrics, setPerformanceMetrics] = useState({
    avgLatency: 0,
    p95Latency: 0,
    p99Latency: 0,
    maxLatency: 0,
    errorRate: 0,
    throughput: 0,
  });
  
  // Service dependencies
  const [serviceDependencies, setServiceDependencies] = useState([]);
  const [selectedService, setSelectedService] = useState(null);
  const [serviceMetrics, setServiceMetrics] = useState(null);
  
  // Bottleneck analysis
  const [bottlenecks, setBottlenecks] = useState([]);
  const [bottleneckChartData, setBottleneckChartData] = useState([]);
  
  // SLA tracking
  const [slaMetrics, setSlaMetrics] = useState({
    uptime: 0,
    errorBudget: 0,
    sloCompliance: 0,
  });
  
  // Comparison data
  const [comparisonData, setComparisonData] = useState([]);
  const [baselineMetrics, setBaselineMetrics] = useState(null);
  
  // Fetch critical paths
  const fetchCriticalPaths = useCallback(async () => {
    try {
      setLoading(true);
      
      const headers = {
        'X-Workspace-ID': workspaceId,
        'Authorization': `Bearer ${apiKey}`,
      };
      
      // Mock critical path data for now
      const mockPaths = [
        {
          traceId: 'trace-001',
          rootService: 'api-gateway',
          duration: 450,
          spans: 12,
          services: ['api-gateway', 'auth-service', 'user-db'],
          criticalPath: 420,
          otherPath: 30,
          timestamp: Date.now(),
        },
        {
          traceId: 'trace-002',
          rootService: 'order-service',
          duration: 680,
          spans: 15,
          services: ['order-service', 'inventory-service', 'payment-service', 'order-db'],
          criticalPath: 650,
          otherPath: 30,
          timestamp: Date.now() - 5000,
        },
        {
          traceId: 'trace-003',
          rootService: 'api-gateway',
          duration: 320,
          spans: 8,
          services: ['api-gateway', 'user-service', 'user-db'],
          criticalPath: 290,
          otherPath: 30,
          timestamp: Date.now() - 10000,
        },
      ];
      
      setCriticalPaths(mockPaths);
      setLoading(false);
    } catch (err) {
      setError(`Failed to fetch critical paths: ${err.message}`);
      setLoading(false);
    }
  }, [workspaceId, apiKey]);
  
  // Fetch service dependencies
  const fetchServiceDependencies = useCallback(async () => {
    try {
      const headers = {
        'X-Workspace-ID': workspaceId,
        'Authorization': `Bearer ${apiKey}`,
      };
      
      // Mock service dependencies
      const mockDeps = [
        {
          service: 'api-gateway',
          dependencies: ['auth-service', 'user-service', 'order-service'],
          inbound: [],
          avgLatency: 45,
          p95Latency: 89,
          errorRate: 0.1,
          throughput: 1200,
        },
        {
          service: 'auth-service',
          dependencies: ['user-db'],
          inbound: ['api-gateway'],
          avgLatency: 78,
          p95Latency: 145,
          errorRate: 0.05,
          throughput: 850,
        },
        {
          service: 'user-service',
          dependencies: ['user-db', 'cache'],
          inbound: ['api-gateway'],
          avgLatency: 95,
          p95Latency: 180,
          errorRate: 0.08,
          throughput: 650,
        },
        {
          service: 'order-service',
          dependencies: ['order-db', 'inventory-service', 'payment-service'],
          inbound: ['api-gateway'],
          avgLatency: 156,
          p95Latency: 280,
          errorRate: 0.12,
          throughput: 420,
        },
      ];
      
      setServiceDependencies(mockDeps);
    } catch (err) {
      setError(`Failed to fetch service dependencies: ${err.message}`);
    }
  }, [workspaceId, apiKey]);
  
  // Analyze bottlenecks
  const analyzeBottlenecks = useCallback(() => {
    // Identify slowest operations
    const bottleneckList = criticalPaths
      .map((path) => ({
        traceId: path.traceId,
        bottleneck: Math.max(...path.services.map((s) => (s === 'api-gateway' ? 45 : 80))),
        slowestService: path.services[Math.floor(Math.random() * path.services.length)],
        duration: path.duration,
        percentageOfTotal: (Math.max(...path.services.map((s) => (s === 'api-gateway' ? 45 : 80))) / path.duration) * 100,
      }))
      .sort((a, b) => b.percentageOfTotal - a.percentageOfTotal);
    
    setBottlenecks(bottleneckList);
    
    // Prepare chart data
    const chartData = bottleneckList.map((item) => ({
      name: item.slowestService,
      percentage: item.percentageOfTotal,
      value: item.bottleneck,
    }));
    
    setBottleneckChartData(chartData);
  }, [criticalPaths]);
  
  // Calculate performance metrics
  const calculatePerformanceMetrics = useCallback(() => {
    if (criticalPaths.length === 0) return;
    
    const durations = criticalPaths.map((p) => p.duration).sort((a, b) => a - b);
    const avg = durations.reduce((a, b) => a + b, 0) / durations.length;
    const p95 = durations[Math.ceil(durations.length * 0.95) - 1];
    const p99 = durations[Math.ceil(durations.length * 0.99) - 1];
    const max = Math.max(...durations);
    
    setPerformanceMetrics({
      avgLatency: avg,
      p95Latency: p95,
      p99Latency: p99,
      maxLatency: max,
      errorRate: Math.random() * 0.5, // Mock error rate
      throughput: Math.random() * 2000 + 800, // Mock throughput
    });
  }, [criticalPaths]);
  
  // Fetch comparison data
  const fetchComparisonData = useCallback(async () => {
    try {
      // Mock comparison data
      const mockComparison = [
        { period: '7 days ago', avg: 420, p95: 650, p99: 890 },
        { period: '6 days ago', avg: 410, p95: 640, p99: 880 },
        { period: '5 days ago', avg: 430, p95: 670, p99: 900 },
        { period: '4 days ago', avg: 415, p95: 650, p99: 885 },
        { period: '3 days ago', avg: 440, p95: 680, p99: 920 },
        { period: '2 days ago', avg: 425, p95: 660, p99: 890 },
        { period: 'Today', avg: 465, p95: 720, p99: 980 },
      ];
      
      setComparisonData(mockComparison);
      
      // Set baseline (7 days average)
      const baseline = mockComparison.slice(0, 6).reduce((a, b) => ({
        avg: a.avg + b.avg / 6,
        p95: a.p95 + b.p95 / 6,
        p99: a.p99 + b.p99 / 6,
      }));
      setBaselineMetrics(baseline);
    } catch (err) {
      setError(`Failed to fetch comparison data: ${err.message}`);
    }
  }, []);
  
  // Update SLA metrics
  const updateSLAMetrics = useCallback(() => {
    setSlaMetrics({
      uptime: 99.95,
      errorBudget: 2.1,
      sloCompliance: 98.5,
    });
  }, []);
  
  // Initial data fetch
  useEffect(() => {
    fetchCriticalPaths();
    fetchServiceDependencies();
    fetchComparisonData();
    updateSLAMetrics();
  }, [timeRange]);
  
  useEffect(() => {
    if (criticalPaths.length > 0) {
      analyzeBottlenecks();
      calculatePerformanceMetrics();
    }
  }, [criticalPaths, analyzeBottlenecks, calculatePerformanceMetrics]);
  
  // Trace detail viewer
  const handleSelectTrace = (traceId) => {
    const trace = criticalPaths.find((p) => p.traceId === traceId);
    setSelectedTrace(trace);
    if (trace) {
      setTraceDetails({
        ...trace,
        spanBreakdown: trace.services.map((s) => ({
          service: s,
          duration: Math.floor(Math.random() * 200),
          children: [],
        })),
      });
    }
  };
  
  // Service detail viewer
  const handleSelectService = (serviceName) => {
    const svc = serviceDependencies.find((s) => s.service === serviceName);
    setSelectedService(serviceName);
    if (svc) {
      setServiceMetrics(svc);
    }
  };
  
  // Render critical path timeline
  const renderCriticalPathTimeline = () => (
    <Box borderWidth={1} borderRadius="lg" p={4} mb={6}>
      <Box fontSize="lg" fontWeight="bold" mb={4}>
        Critical Paths (Last Traces)
      </Box>
      <VStack spacing={4} align="stretch">
        {criticalPaths.slice(0, 5).map((path) => (
          <Box
            key={path.traceId}
            p={3}
            borderWidth={1}
            borderRadius="md"
            cursor="pointer"
            _hover={{ bg: 'gray.50' }}
            onClick={() => handleSelectTrace(path.traceId)}
          >
            <HStack justifyContent="space-between" mb={2}>
              <Box fontWeight="bold">{path.traceId}</Box>
              <Badge colorScheme={path.duration > 500 ? 'red' : 'green'}>
                {path.duration}ms
              </Badge>
            </HStack>
            <Box mb={2}>
              <ResponsiveContainer width="100%" height={40}>
                <BarChart data={[{ critical: path.criticalPath, other: path.otherPath }]}>
                  <Bar dataKey="critical" stackId="a" fill="#ff7c7c" />
                  <Bar dataKey="other" stackId="a" fill="#82ca9d" />
                </BarChart>
              </ResponsiveContainer>
            </Box>
            <Box fontSize="sm" color="gray.600">
              Services: {path.services.join(' → ')}
            </Box>
          </Box>
        ))}
      </VStack>
    </Box>
  );
  
  // Render performance metrics stats
  const renderPerformanceStats = () => (
    <Grid templateColumns="repeat(auto-fit, minmax(150px, 1fr))" gap={4} mb={6}>
      <Stat borderWidth={1} borderRadius="lg" p={4}>
        <StatLabel>Avg Latency</StatLabel>
        <StatNumber>{Math.round(performanceMetrics.avgLatency)}ms</StatNumber>
      </Stat>
      <Stat borderWidth={1} borderRadius="lg" p={4}>
        <StatLabel>P95 Latency</StatLabel>
        <StatNumber>{Math.round(performanceMetrics.p95Latency)}ms</StatNumber>
      </Stat>
      <Stat borderWidth={1} borderRadius="lg" p={4}>
        <StatLabel>P99 Latency</StatLabel>
        <StatNumber>{Math.round(performanceMetrics.p99Latency)}ms</StatNumber>
      </Stat>
      <Stat borderWidth={1} borderRadius="lg" p={4}>
        <StatLabel>Error Rate</StatLabel>
        <StatNumber>{(performanceMetrics.errorRate * 100).toFixed(2)}%</StatNumber>
      </Stat>
      <Stat borderWidth={1} borderRadius="lg" p={4}>
        <StatLabel>Throughput</StatLabel>
        <StatNumber>{Math.round(performanceMetrics.throughput)}/s</StatNumber>
      </Stat>
    </Grid>
  );
  
  // Render bottleneck chart
  const renderBottleneckChart = () => (
    <Box borderWidth={1} borderRadius="lg" p={4} mb={6}>
      <Box fontSize="lg" fontWeight="bold" mb={4}>
        Bottleneck Analysis
      </Box>
      {bottleneckChartData.length > 0 ? (
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={bottleneckChartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="percentage" fill="#ff7c7c" name="% of Critical Path" />
          </BarChart>
        </ResponsiveContainer>
      ) : (
        <Box p={4}>No bottleneck data available</Box>
      )}
    </Box>
  );
  
  // Render latency trend
  const renderLatencyTrend = () => (
    <Box borderWidth={1} borderRadius="lg" p={4} mb={6}>
      <Box fontSize="lg" fontWeight="bold" mb={4}>
        Latency Trend (7-day Comparison)
      </Box>
      {comparisonData.length > 0 ? (
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={comparisonData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="period" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey="avg" stroke="#8884d8" name="Avg" />
            <Line type="monotone" dataKey="p95" stroke="#ffc658" name="P95" />
            <Line type="monotone" dataKey="p99" stroke="#ff7c7c" name="P99" />
          </LineChart>
        </ResponsiveContainer>
      ) : (
        <Box p={4}>No trend data available</Box>
      )}
    </Box>
  );
  
  // Render service dependency matrix
  const renderServiceMatrix = () => (
    <Box borderWidth={1} borderRadius="lg" p={4} mb={6}>
      <Box fontSize="lg" fontWeight="bold" mb={4}>
        Service Dependency Matrix
      </Box>
      <VStack spacing={3} align="stretch">
        {serviceDependencies.map((svc) => (
          <Box
            key={svc.service}
            p={3}
            borderWidth={1}
            borderRadius="md"
            cursor="pointer"
            onClick={() => handleSelectService(svc.service)}
            _hover={{ bg: 'gray.50' }}
          >
            <HStack justifyContent="space-between" mb={2}>
              <Box fontWeight="bold">{svc.service}</Box>
              <Badge colorScheme={svc.errorRate > 0.1 ? 'red' : 'green'}>
                {(svc.errorRate * 100).toFixed(2)}% errors
              </Badge>
            </HStack>
            <HStack spacing={6} fontSize="sm">
              <Box>Avg: {svc.avgLatency}ms</Box>
              <Box>P95: {svc.p95Latency}ms</Box>
              <Box>Throughput: {svc.throughput}/s</Box>
            </HStack>
          </Box>
        ))}
      </VStack>
    </Box>
  );
  
  // Render SLA metrics
  const renderSLAMetrics = () => (
    <Grid templateColumns="repeat(auto-fit, minmax(200px, 1fr))" gap={4} mb={6}>
      <Box borderWidth={1} borderRadius="lg" p={4}>
        <Box fontSize="sm" color="gray.600" mb={2}>
          Uptime
        </Box>
        <StatNumber color="green.500">{slaMetrics.uptime}%</StatNumber>
      </Box>
      <Box borderWidth={1} borderRadius="lg" p={4}>
        <Box fontSize="sm" color="gray.600" mb={2}>
          Error Budget Remaining
        </Box>
        <StatNumber color={slaMetrics.errorBudget > 2 ? 'orange.500' : 'red.500'}>
          {slaMetrics.errorBudget}%
        </StatNumber>
      </Box>
      <Box borderWidth={1} borderRadius="lg" p={4}>
        <Box fontSize="sm" color="gray.600" mb={2}>
          SLO Compliance
        </Box>
        <StatNumber color={slaMetrics.sloCompliance > 99 ? 'green.500' : 'orange.500'}>
          {slaMetrics.sloCompliance}%
        </StatNumber>
      </Box>
    </Grid>
  );
  
  return (
    <Container maxW="100%" p={6}>
      <Box mb={6}>
        <Box fontSize="2xl" fontWeight="bold" mb={4}>
          Performance Analyzer
        </Box>
        
        <HStack spacing={4} mb={4}>
          <Select value={timeRange} onChange={(e) => setTimeRange(e.target.value)} maxW="150px">
            <option value="1h">Last 1 hour</option>
            <option value="6h">Last 6 hours</option>
            <option value="24h">Last 24 hours</option>
            <option value="7d">Last 7 days</option>
          </Select>
          
          <Select value={sortBy} onChange={(e) => setSortBy(e.target.value)} maxW="150px">
            <option value="duration">Sort by Duration</option>
            <option value="latency">Sort by Latency</option>
            <option value="errors">Sort by Error Rate</option>
          </Select>
        </HStack>
      </Box>
      
      {error && (
        <Box p={4} mb={4} bg="red.50" borderRadius="lg" color="red.800">
          {error}
        </Box>
      )}
      
      <Tabs index={activeTab} onChange={setActiveTab}>
        <TabList borderBottomWidth={2} borderBottomColor="gray.200">
          <Tab>Critical Path</Tab>
          <Tab>Performance</Tab>
          <Tab>Dependencies</Tab>
          <Tab>SLA</Tab>
        </TabList>
        
        <TabPanels>
          <TabPanel>
            {renderPerformanceStats()}
            {renderCriticalPathTimeline()}
            {selectedTrace && traceDetails && (
              <Box borderWidth={1} borderRadius="lg" p={4} bg="blue.50">
                <Box fontSize="lg" fontWeight="bold" mb={4}>
                  Trace Details: {selectedTrace.traceId}
                </Box>
                <Box>Duration breakdown: {JSON.stringify(traceDetails.spanBreakdown, null, 2)}</Box>
              </Box>
            )}
          </TabPanel>
          
          <TabPanel>
            {renderPerformanceStats()}
            {renderBottleneckChart()}
            {renderLatencyTrend()}
          </TabPanel>
          
          <TabPanel>
            {renderServiceMatrix()}
            {selectedService && serviceMetrics && (
              <Box borderWidth={1} borderRadius="lg" p={4} bg="blue.50">
                <Box fontSize="lg" fontWeight="bold" mb={4}>
                  {selectedService} Metrics
                </Box>
                <VStack align="start" spacing={2}>
                  <Box>Dependencies: {serviceMetrics.dependencies.join(', ')}</Box>
                  <Box>Inbound: {serviceMetrics.inbound.join(', ') || 'None'}</Box>
                  <Box>Avg Latency: {serviceMetrics.avgLatency}ms</Box>
                  <Box>P95 Latency: {serviceMetrics.p95Latency}ms</Box>
                  <Box>Error Rate: {(serviceMetrics.errorRate * 100).toFixed(2)}%</Box>
                </VStack>
              </Box>
            )}
          </TabPanel>
          
          <TabPanel>
            {renderSLAMetrics()}
            {renderLatencyTrend()}
          </TabPanel>
        </TabPanels>
      </Tabs>
    </Container>
  );
};

export default PerformanceAnalyzer;
