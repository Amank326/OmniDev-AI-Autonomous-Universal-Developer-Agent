/**
 * Advanced Analytics Dashboard
 * Comprehensive analytics visualization and monitoring dashboard.
 */

import React, { useState, useEffect, useCallback } from 'react'
import {
  Box,
  Button,
  Card,
  CardBody,
  Heading,
  HStack,
  VStack,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  FormControl,
  FormLabel,
  Select,
  Badge,
  useToast,
  Grid,
  GridItem,
  Flex,
  Icon,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Alert,
  AlertIcon,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  StatArrow,
  Progress
} from '@chakra-ui/react'
import { DownloadIcon, CheckCircleIcon, WarningIcon } from '@chakra-ui/icons'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts'

export const AdvancedAnalyticsDashboard = () => {
  // State
  const [workspaceId, setWorkspaceId] = useState('workspace_123')
  const [selectedModel, setSelectedModel] = useState('classifier_prod')
  const [timeRange, setTimeRange] = useState('7days')
  const [analyticsData, setAnalyticsData] = useState(null)
  const [performanceData, setPerformanceData] = useState(null)
  const [costData, setCostData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState(0)

  const toast = useToast()
  const COLORS = ['#3182ce', '#ed8936', '#38a169', '#dd6b20', '#d69e2e']

  // Load analytics data
  useEffect(() => {
    const mockAnalytics = {
      models: [
        { id: 'classifier_prod', name: 'Production Classifier', inferences: 15847, error_rate: 0.23 },
        { id: 'detector_v2', name: 'Object Detector', inferences: 8234, error_rate: 0.45 },
        { id: 'nlp_model', name: 'NLP Model', inferences: 12456, error_rate: 0.15 }
      ],
      model_details: {
        total_inferences: 15847,
        error_rate_percent: 0.23,
        avg_latency_ms: 127.5,
        cache_hit_rate: 42.1,
        quality_metrics: {
          accuracy: 0.987,
          precision: 0.982,
          recall: 0.979,
          f1_score: 0.9805
        },
        trends: [
          { date: '2026-02-02', inferences: 450, latency_ms: 130 },
          { date: '2026-02-03', inferences: 480, latency_ms: 128 },
          { date: '2026-02-04', inferences: 520, latency_ms: 126 },
          { date: '2026-02-05', inferences: 510, latency_ms: 127 },
          { date: '2026-02-06', inferences: 570, latency_ms: 125 },
          { date: '2026-02-07', inferences: 620, latency_ms: 129 },
          { date: '2026-02-08', inferences: 687, latency_ms: 127 }
        ]
      },
      performance: {
        system_cpu: 62.1,
        system_memory: 71.3,
        api_latency: 12.3,
        error_rate: 0.01,
        latency_breakdown: {
          preprocessing: 12.3,
          inference: 98.5,
          postprocessing: 8.2,
          overhead: 8.5
        },
        latency_by_batch: [
          { batch: 1, latency: 115 },
          { batch: 4, latency: 128 },
          { batch: 8, latency: 145 },
          { batch: 16, latency: 187 }
        ]
      },
      costs: {
        total_monthly: 4562.34,
        daily_avg: 152.08,
        breakdown: {
          compute: 2145.67,
          storage: 892.45,
          network: 345.23,
          other: 179.00
        },
        forecast: [
          { date: '2026-02-09', cost: 155.30 },
          { date: '2026-02-10', cost: 158.20 },
          { date: '2026-02-11', cost: 161.50 },
          { date: '2026-02-12', cost: 164.80 },
          { date: '2026-02-13', cost: 167.30 }
        ]
      }
    }

    setAnalyticsData(mockAnalytics)
    setPerformanceData(mockAnalytics.performance)
    setCostData(mockAnalytics.costs)
  }, [])

  // Handlers
  const handleExportReport = async () => {
    try {
      const response = await fetch('/api/v1/analytics/reports/comprehensive', {
        headers: {
          'X-Workspace-ID': workspaceId
        }
      })
      const data = await response.json()

      // Create and download CSV/JSON
      const dataStr = JSON.stringify(data, null, 2)
      const dataBlob = new Blob([dataStr], { type: 'application/json' })
      const url = URL.createObjectURL(dataBlob)
      const link = document.createElement('a')
      link.href = url
      link.download = `analytics-${new Date().toISOString()}.json`
      link.click()

      toast({
        title: 'Success',
        description: 'Report exported successfully',
        status: 'success'
      })
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to export report',
        status: 'error'
      })
    }
  }

  // Render functions

  const renderModelAnalytics = () => {
    if (!analyticsData) return null

    return (
      <VStack spacing={6} align="stretch">
        {/* Model Selection */}
        <Card p={4} bg="gray.50">
          <HStack>
            <FormControl flex={1}>
              <FormLabel>Select Model</FormLabel>
              <Select value={selectedModel} onChange={e => setSelectedModel(e.target.value)}>
                {analyticsData.models.map(m => (
                  <option key={m.id} value={m.id}>{m.name}</option>
                ))}
              </Select>
            </FormControl>
            <Button colorScheme="blue" mt={8}>Refresh</Button>
          </HStack>
        </Card>

        {/* Key Metrics */}
        <Card p={4}>
          <Heading size="md" mb={4}>Model Performance</Heading>
          <Grid templateColumns="repeat(4, 1fr)" gap={4}>
            <Stat>
              <StatLabel>Total Inferences</StatLabel>
              <StatNumber>{analyticsData.model_details.total_inferences.toLocaleString()}</StatNumber>
              <StatHelpText>Last 7 days</StatHelpText>
            </Stat>
            <Stat>
              <StatLabel>Error Rate</StatLabel>
              <StatNumber>{analyticsData.model_details.error_rate_percent.toFixed(2)}%</StatNumber>
              <StatHelpText color={analyticsData.model_details.error_rate_percent > 0.5 ? 'red.600' : 'green.600'}>
                {analyticsData.model_details.error_rate_percent > 0.5 ? 'Above target' : 'On target'}
              </StatHelpText>
            </Stat>
            <Stat>
              <StatLabel>Avg Latency</StatLabel>
              <StatNumber>{analyticsData.model_details.avg_latency_ms.toFixed(1)}ms</StatNumber>
              <StatHelpText>Model only</StatHelpText>
            </Stat>
            <Stat>
              <StatLabel>Cache Hit Rate</StatLabel>
              <StatNumber>{analyticsData.model_details.cache_hit_rate.toFixed(1)}%</StatNumber>
              <StatHelpText>
                <StatArrow type="increase" />
                5.3%
              </StatHelpText>
            </Stat>
          </Grid>
        </Card>

        {/* Quality Metrics */}
        <Card p={4}>
          <Heading size="md" mb={4}>Quality Metrics</Heading>
          <Grid templateColumns="repeat(4, 1fr)" gap={4}>
            {Object.entries(analyticsData.model_details.quality_metrics).map(([key, value]) => (
              <Stat key={key}>
                <StatLabel fontSize="sm">{key.charAt(0).toUpperCase() + key.slice(1)}</StatLabel>
                <StatNumber fontSize="lg">{(value * 100).toFixed(2)}%</StatNumber>
              </Stat>
            ))}
          </Grid>
        </Card>

        {/* Usage Trends */}
        <Card p={4}>
          <Heading size="md" mb={4}>Usage & Latency Trends</Heading>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={analyticsData.model_details.trends}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis yAxisId="left" label={{ value: 'Inferences', angle: -90, position: 'insideLeft' }} />
              <YAxis yAxisId="right" orientation="right" label={{ value: 'Latency (ms)', angle: 90, position: 'insideRight' }} />
              <Tooltip />
              <Legend />
              <Line yAxisId="left" type="monotone" dataKey="inferences" stroke="#3182ce" name="Inferences" />
              <Line yAxisId="right" type="monotone" dataKey="latency_ms" stroke="#ed8936" name="Latency (ms)" />
            </LineChart>
          </ResponsiveContainer>
        </Card>
      </VStack>
    )
  }

  const renderPerformanceAnalytics = () => {
    if (!performanceData) return null

    return (
      <VStack spacing={6} align="stretch">
        {/* System Health */}
        <Card p={4}>
          <Heading size="md" mb={4}>System Health</Heading>
          <Grid templateColumns="repeat(2, 1fr)" gap={4}>
            <Box>
              <Heading size="sm" mb={2}>CPU Utilization</Heading>
              <Progress value={performanceData.system_cpu} colorScheme="blue" mb={2} />
              <HStack justify="space-between">
                <span>{performanceData.system_cpu.toFixed(1)}%</span>
                <Badge colorScheme={performanceData.system_cpu > 80 ? 'red' : 'green'}>
                  {performanceData.system_cpu > 80 ? 'High' : 'Normal'}
                </Badge>
              </HStack>
            </Box>
            <Box>
              <Heading size="sm" mb={2}>Memory Utilization</Heading>
              <Progress value={performanceData.system_memory} colorScheme="orange" mb={2} />
              <HStack justify="space-between">
                <span>{performanceData.system_memory.toFixed(1)}%</span>
                <Badge colorScheme={performanceData.system_memory > 80 ? 'red' : 'yellow'}>
                  {performanceData.system_memory > 80 ? 'Critical' : 'Warning'}
                </Badge>
              </HStack>
            </Box>
          </Grid>
        </Card>

        {/* Service Metrics */}
        <Card p={4}>
          <Heading size="md" mb={4}>Service Latencies</Heading>
          <Table variant="simple" size="sm">
            <Thead>
              <Tr bg="gray.100">
                <Th>Component</Th>
                <Th>Latency (ms)</Th>
                <Th>Status</Th>
              </Tr>
            </Thead>
            <Tbody>
              {Object.entries(performanceData.latency_breakdown).map(([component, latency]) => (
                <Tr key={component}>
                  <Td fontSize="sm" fontWeight="bold">{component}</Td>
                  <Td>{latency.toFixed(1)}</Td>
                  <Td>
                    <Badge colorScheme={latency > 20 ? 'yellow' : 'green'}>
                      {latency > 20 ? 'Warning' : 'Normal'}
                    </Badge>
                  </Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        </Card>

        {/* Latency by Batch Size */}
        <Card p={4}>
          <Heading size="md" mb={4}>Latency by Batch Size</Heading>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={performanceData.latency_by_batch}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="batch" label={{ value: 'Batch Size', position: 'bottom' }} />
              <YAxis label={{ value: 'Latency (ms)', angle: -90, position: 'insideLeft' }} />
              <Tooltip />
              <Bar dataKey="latency" fill="#3182ce" name="Latency (ms)" />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </VStack>
    )
  }

  const renderCostAnalytics = () => {
    if (!costData) return null

    const totalCost = Object.values(costData.breakdown).reduce((a, b) => a + b, 0)

    return (
      <VStack spacing={6} align="stretch">
        {/* Cost Summary */}
        <Card p={4}>
          <Heading size="md" mb={4}>Cost Summary</Heading>
          <Grid templateColumns="repeat(3, 1fr)" gap={4}>
            <Stat>
              <StatLabel>Current Monthly</StatLabel>
              <StatNumber>${costData.total_monthly.toFixed(2)}</StatNumber>
            </Stat>
            <Stat>
              <StatLabel>Daily Average</StatLabel>
              <StatNumber>${costData.daily_avg.toFixed(2)}</StatNumber>
            </Stat>
            <Stat>
              <StatLabel>Projected Monthly</StatLabel>
              <StatNumber>${(costData.daily_avg * 30).toFixed(2)}</StatNumber>
              <StatHelpText>Based on current burn</StatHelpText>
            </Stat>
          </Grid>
        </Card>

        {/* Cost Breakdown */}
        <Card p={4}>
          <Heading size="md" mb={4}>Cost Breakdown</Heading>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={Object.entries(costData.breakdown).map(([name, value]) => ({
                  name: name.charAt(0).toUpperCase() + name.slice(1),
                  value
                }))}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name} $${value.toFixed(0)}`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {Object.entries(costData.breakdown).map((_, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(value) => `$${value.toFixed(2)}`} />
            </PieChart>
          </ResponsiveContainer>
        </Card>

        {/* Cost Forecast */}
        <Card p={4}>
          <Heading size="md" mb={4}>30-Day Cost Forecast</Heading>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={costData.forecast}>
              <defs>
                <linearGradient id="colorCost" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3182ce" stopOpacity={0.8} />
                  <stop offset="95%" stopColor="#3182ce" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis label={{ value: 'Daily Cost ($)', angle: -90, position: 'insideLeft' }} />
              <Tooltip formatter={(value) => `$${value.toFixed(2)}`} />
              <Area
                type="monotone"
                dataKey="cost"
                stroke="#3182ce"
                fillOpacity={1}
                fill="url(#colorCost)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </Card>
      </VStack>
    )
  }

  const renderDiagnostics = () => {
    return (
      <VStack spacing={6} align="stretch">
        <Alert status="info">
          <AlertIcon />
          <Box>
            <strong>Data Quality Score: 94.2%</strong>
            <br />
            All metrics are being tracked successfully with minimal gaps. Last update: 5 minutes ago.
          </Box>
        </Alert>

        <Card p={4}>
          <Heading size="md" mb={4}>Data Freshness</Heading>
          <Table variant="simple" size="sm">
            <Thead>
              <Tr bg="gray.100">
                <Th>Data Type</Th>
                <Th>Last Updated</Th>
                <Th>Status</Th>
              </Tr>
            </Thead>
            <Tbody>
              <Tr>
                <Td>Model Analytics</Td>
                <Td>5 minutes ago</Td>
                <Td><Badge colorScheme="green">Fresh</Badge></Td>
              </Tr>
              <Tr>
                <Td>Performance Metrics</Td>
                <Td>1 minute ago</Td>
                <Td><Badge colorScheme="green">Fresh</Badge></Td>
              </Tr>
              <Tr>
                <Td>Cost Data</Td>
                <Td>1 hour ago</Td>
                <Td><Badge colorScheme="yellow">Stale</Badge></Td>
              </Tr>
            </Tbody>
          </Table>
        </Card>

        <Card p={4}>
          <Heading size="md" mb={4}>Active Alerts</Heading>
          <VStack spacing={2} align="stretch">
            <HStack p={3} bg="red.50" borderRadius="md">
              <Icon as={WarningIcon} color="red.600" />
              <Box flex={1}>
                <strong>GPU Memory High</strong>
                <br />
                <span style={{ fontSize: '0.9em', color: '#666' }}>Utilization at 85.2%, recommend reducing batch size</span>
              </Box>
            </HStack>
            <HStack p={3} bg="yellow.50" borderRadius="md">
              <Icon as={WarningIcon} color="orange.600" />
              <Box flex={1}>
                <strong>Memory Usage Warning</strong>
                <br />
                <span style={{ fontSize: '0.9em', color: '#666' }}>System memory at 71.3%, nearing recommended threshold</span>
              </Box>
            </HStack>
          </VStack>
        </Card>
      </VStack>
    )
  }

  return (
    <Box p={6}>
      <HStack justify="space-between" mb={6}>
        <Heading>Advanced Analytics Dashboard</Heading>
        <Button leftIcon={<DownloadIcon />} colorScheme="blue" onClick={handleExportReport}>
          Export Report
        </Button>
      </HStack>

      {/* Global Controls */}
      <Card p={4} mb={6} bg="gray.50">
        <HStack spacing={4}>
          <FormControl flex={1}>
            <FormLabel>Workspace</FormLabel>
            <Select value={workspaceId} onChange={e => setWorkspaceId(e.target.value)}>
              <option value="workspace_123">Workspace 1</option>
              <option value="workspace_456">Workspace 2</option>
            </Select>
          </FormControl>
          <FormControl flex={1}>
            <FormLabel>Time Range</FormLabel>
            <Select value={timeRange} onChange={e => setTimeRange(e.target.value)}>
              <option value="1day">Last 24 Hours</option>
              <option value="7days">Last 7 Days</option>
              <option value="30days">Last 30 Days</option>
              <option value="90days">Last 90 Days</option>
            </Select>
          </FormControl>
        </HStack>
      </Card>

      {/* Tabs */}
      <Tabs index={activeTab} onChange={setActiveTab}>
        <TabList mb={4}>
          <Tab>Model Analytics</Tab>
          <Tab>Performance</Tab>
          <Tab>Costs</Tab>
          <Tab>Diagnostics</Tab>
        </TabList>

        <TabPanels>
          <TabPanel>{renderModelAnalytics()}</TabPanel>
          <TabPanel>{renderPerformanceAnalytics()}</TabPanel>
          <TabPanel>{renderCostAnalytics()}</TabPanel>
          <TabPanel>{renderDiagnostics()}</TabPanel>
        </TabPanels>
      </Tabs>
    </Box>
  )
}

export default AdvancedAnalyticsDashboard
