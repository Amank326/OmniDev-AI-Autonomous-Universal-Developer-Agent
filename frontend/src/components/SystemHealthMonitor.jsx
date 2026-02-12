/**
 * System Health Monitor Component
 * Real-time system health monitoring with alerts and recovery suggestions.
 */

import React, { useState, useEffect, useRef } from 'react'
import {
  Box,
  Button,
  Card,
  CardBody,
  Heading,
  HStack,
  VStack,
  Badge,
  useToast,
  Grid,
  GridItem,
  Icon,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  CloseButton,
  CircularProgress,
  CircularProgressLabel,
  Spinner,
  SimpleGrid,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  UnorderedList,
  ListItem
} from '@chakra-ui/react'
import {
  CheckCircleIcon,
  WarningIcon,
  NotAllowedIcon,
  InfoIcon,
  TimeIcon
} from '@chakra-ui/icons'

export const SystemHealthMonitor = () => {
  // State
  const [healthStatus, setHealthStatus] = useState(null)
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(true)
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [refreshInterval, setRefreshInterval] = useState(30000) // 30 seconds
  const [dismissedAlerts, setDismissedAlerts] = useState(new Set())
  const socketRef = useRef(null)
  const toast = useToast()

  // Mock health status data
  const mockHealthStatus = {
    overall_health_score: 87.5,
    status: 'healthy', // healthy, degraded, critical
    last_updated: new Date().toISOString(),
    components: [
      {
        name: 'API Gateway',
        status: 'healthy',
        health_score: 95.2,
        cpu_util: 45.3,
        memory_util: 52.1,
        latency_p99: 234.5,
        error_rate: 0.01,
        requests_per_sec: 523.4
      },
      {
        name: 'Model Serving',
        status: 'degraded',
        health_score: 78.3,
        cpu_util: 85.2,
        memory_util: 78.9,
        latency_p99: 456.2,
        error_rate: 0.23,
        requests_per_sec: 234.1,
        alerts: ['High GPU memory utilization']
      },
      {
        name: 'Storage',
        status: 'healthy',
        health_score: 92.1,
        cpu_util: 32.1,
        memory_util: 41.3,
        latency_p99: 89.3,
        error_rate: 0.001,
        requests_per_sec: 145.2
      },
      {
        name: 'Database',
        status: 'healthy',
        health_score: 88.9,
        cpu_util: 51.2,
        memory_util: 62.3,
        latency_p99: 145.2,
        error_rate: 0.002,
        requests_per_sec: 234.5,
        active_connections: 342
      },
      {
        name: 'Cache',
        status: 'degraded',
        health_score: 82.1,
        cpu_util: 72.1,
        memory_util: 85.3,
        hit_rate: 72.1,
        eviction_rate: 2.3,
        alerts: ['High eviction rate, consider increasing cache size']
      },
      {
        name: 'Monitoring',
        status: 'healthy',
        health_score: 90.0,
        cpu_util: 38.2,
        memory_util: 45.1,
        metrics_ingestion_rate: 45234,
        alerts_triggered: 3
      }
    ],
    services: [
      { name: 'Load Balancer', status: 'healthy', uptime_percent: 99.99 },
      { name: 'Message Queue', status: 'healthy', uptime_percent: 99.95 },
      { name: 'Config Server', status: 'healthy', uptime_percent: 100.0 }
    ]
  }

  const mockAlerts = [
    {
      id: 'alert_001',
      severity: 'critical',
      component: 'Model Serving',
      title: 'GPU Memory Critical',
      description: 'GPU memory utilization reached 85.2%, inference latency increased 40%',
      timestamp: new Date(Date.now() - 5 * 60000).toISOString(),
      actions: [
        'Reduce batch size from 16 to 8',
        'Enable GPU memory optimization',
        'Scale to additional GPU instance'
      ]
    },
    {
      id: 'alert_002',
      severity: 'warning',
      component: 'Cache',
      title: 'High Cache Eviction Rate',
      description: 'Cache eviction rate is 2.3% per minute, indicating insufficient cache size',
      timestamp: new Date(Date.now() - 15 * 60000).toISOString(),
      actions: [
        'Increase cache memory allocation by 50%',
        'Optimize cache key strategy',
        'Review frequently accessed data patterns'
      ]
    },
    {
      id: 'alert_003',
      severity: 'info',
      component: 'API Gateway',
      title: 'Peak Traffic Detected',
      description: 'Request rate increased to 523.4/s from baseline 450/s',
      timestamp: new Date(Date.now() - 2 * 60000).toISOString(),
      actions: [
        'Monitor for sustained high traffic',
        'Prepare scale-up plan if needed',
        'Review traffic patterns for optimization'
      ]
    }
  ]

  // Initialize
  useEffect(() => {
    // Set initial data
    setHealthStatus(mockHealthStatus)
    setAlerts(mockAlerts)
    setLoading(false)

    // Initialize WebSocket for real-time updates
    if (typeof io !== 'undefined') {
      socketRef.current = io('/analytics', {
        transports: ['websocket'],
        reconnection: true
      })

      socketRef.current.on('health:status_changed', (data) => {
        handleHealthUpdate(data)
      })

      socketRef.current.on('performance:anomaly', (data) => {
        handleNewAlert(data)
      })

      return () => {
        if (socketRef.current) {
          socketRef.current.disconnect()
        }
      }
    }
  }, [])

  // Auto-refresh
  useEffect(() => {
    if (!autoRefresh) return

    const timer = setInterval(() => {
      refreshHealthStatus()
    }, refreshInterval)

    return () => clearInterval(timer)
  }, [autoRefresh, refreshInterval])

  // Handlers
  const refreshHealthStatus = async () => {
    try {
      const response = await fetch('/api/v1/analytics/performance/system-metrics', {
        headers: {
          'X-Workspace-ID': 'workspace_123'
        }
      })
      if (response.ok) {
        const data = await response.json()
        setHealthStatus(prev => ({
          ...prev,
          ...data
        }))
      }
    } catch (error) {
      console.error('Failed to refresh health status:', error)
    }
  }

  const handleHealthUpdate = (data) => {
    setHealthStatus(prev => ({
      ...prev,
      ...data,
      last_updated: new Date().toISOString()
    }))
  }

  const handleNewAlert = (data) => {
    if (!dismissedAlerts.has(data.id)) {
      setAlerts(prev => [data, ...prev])
      toast({
        title: data.title,
        description: data.description,
        status: data.severity === 'critical' ? 'error' : 'warning',
        duration: 5000
      })
    }
  }

  const dismissAlert = (alertId) => {
    setAlerts(prev => prev.filter(a => a.id !== alertId))
    setDismissedAlerts(prev => new Set([...prev, alertId]))
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'healthy':
        return <CheckCircleIcon color="green.500" w={6} h={6} />
      case 'degraded':
        return <WarningIcon color="orange.500" w={6} h={6} />
      case 'critical':
        return <NotAllowedIcon color="red.500" w={6} h={6} />
      default:
        return <InfoIcon color="blue.500" w={6} h={6} />
    }
  }

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical':
        return 'red'
      case 'warning':
        return 'orange'
      case 'info':
        return 'blue'
      default:
        return 'gray'
    }
  }

  const getHealthColor = (score) => {
    if (score >= 90) return 'green'
    if (score >= 75) return 'orange'
    return 'red'
  }

  // Render
  if (loading) {
    return (
      <Box p={6} display="flex" justifyContent="center" alignItems="center" minH="400px">
        <Spinner size="lg" color="blue.500" />
      </Box>
    )
  }

  return (
    <Box p={6}>
      <HStack justify="space-between" mb={6}>
        <Heading>System Health Monitor</Heading>
        <HStack>
          <Button
            onClick={() => setAutoRefresh(!autoRefresh)}
            colorScheme={autoRefresh ? 'green' : 'gray'}
          >
            {autoRefresh ? 'Auto-Refresh: ON' : 'Auto-Refresh: OFF'}
          </Button>
          <Button onClick={refreshHealthStatus} colorScheme="blue">
            Refresh Now
          </Button>
        </HStack>
      </HStack>

      <Tabs>
        <TabList mb={4}>
          <Tab>Overview</Tab>
          <Tab>Components</Tab>
          <Tab>Alerts</Tab>
          <Tab>Services</Tab>
        </TabList>

        <TabPanels>
          {/* Overview Tab */}
          <TabPanel>
            <VStack spacing={6} align="stretch">
              {/* Health Score */}
              <Card p={6}>
                <HStack spacing={8} align="flex-start">
                  <Box>
                    <CircularProgress
                      value={healthStatus.overall_health_score}
                      size="200px"
                      color={getHealthColor(healthStatus.overall_health_score)}
                      thickness={4}
                    >
                      <CircularProgressLabel>
                        <VStack>
                          <Heading size="lg">
                            {healthStatus.overall_health_score.toFixed(1)}%
                          </Heading>
                          <Badge
                            colorScheme={
                              healthStatus.status === 'healthy'
                                ? 'green'
                                : healthStatus.status === 'degraded'
                                ? 'orange'
                                : 'red'
                            }
                          >
                            {healthStatus.status.toUpperCase()}
                          </Badge>
                        </VStack>
                      </CircularProgressLabel>
                    </CircularProgress>
                  </Box>
                  <VStack align="flex-start" flex={1} spacing={3}>
                    <Box>
                      <Heading size="sm">Status Summary</Heading>
                      <p style={{ color: '#666', marginTop: '8px' }}>
                        Overall system health is{' '}
                        <strong>
                          {healthStatus.status === 'healthy'
                            ? 'optimal'
                            : healthStatus.status === 'degraded'
                            ? 'degraded - attention needed'
                            : 'critical - immediate action required'}
                        </strong>
                      </p>
                    </Box>
                    <Box>
                      <Heading size="sm">Last Updated</Heading>
                      <HStack mt={2} color="gray.600">
                        <TimeIcon />
                        <span>
                          {new Date(healthStatus.last_updated).toLocaleTimeString()}
                        </span>
                      </HStack>
                    </Box>
                    <Box>
                      <Heading size="sm">Active Alerts</Heading>
                      <Badge colorScheme="red" fontSize="lg" mt={2}>
                        {alerts.length} Alert{alerts.length !== 1 ? 's' : ''}
                      </Badge>
                    </Box>
                  </VStack>
                </HStack>
              </Card>

              {/* Key Metrics */}
              <Card p={6}>
                <Heading size="md" mb={4}>Key Metrics</Heading>
                <SimpleGrid columns={3} spacing={4}>
                  <Box>
                    <Heading size="sm" color="gray.600">
                      Healthy Components
                    </Heading>
                    <Heading size="lg" mt={2} color="green.600">
                      {healthStatus.components.filter(c => c.status === 'healthy').length} /
                      {healthStatus.components.length}
                    </Heading>
                  </Box>
                  <Box>
                    <Heading size="sm" color="gray.600">
                      Avg CPU Utilization
                    </Heading>
                    <Heading size="lg" mt={2}>
                      {(
                        healthStatus.components.reduce((sum, c) => sum + (c.cpu_util || 0), 0) /
                        healthStatus.components.length
                      ).toFixed(1)}
                      %
                    </Heading>
                  </Box>
                  <Box>
                    <Heading size="sm" color="gray.600">
                      Avg Memory Utilization
                    </Heading>
                    <Heading size="lg" mt={2}>
                      {(
                        healthStatus.components.reduce((sum, c) => sum + (c.memory_util || 0), 0) /
                        healthStatus.components.length
                      ).toFixed(1)}
                      %
                    </Heading>
                  </Box>
                </SimpleGrid>
              </Card>
            </VStack>
          </TabPanel>

          {/* Components Tab */}
          <TabPanel>
            <VStack spacing={4} align="stretch">
              {healthStatus.components.map((component) => (
                <Card key={component.name} p={4} borderLeftWidth={4}
                      borderLeftColor={
                        component.status === 'healthy'
                          ? 'green.500'
                          : component.status === 'degraded'
                          ? 'orange.500'
                          : 'red.500'
                      }>
                  <VStack align="stretch" spacing={3}>
                    <HStack justify="space-between" align="start">
                      <HStack>
                        {getStatusIcon(component.status)}
                        <Box>
                          <Heading size="md">{component.name}</Heading>
                          <Badge mt={1}>{component.status.toUpperCase()}</Badge>
                        </Box>
                      </HStack>
                      <Box textAlign="right">
                        <CircularProgress
                          value={component.health_score}
                          size="80px"
                          color={getHealthColor(component.health_score)}
                        >
                          <CircularProgressLabel fontSize="sm">
                            {component.health_score.toFixed(1)}%
                          </CircularProgressLabel>
                        </CircularProgress>
                      </Box>
                    </HStack>

                    {/* Component Alerts */}
                    {component.alerts && component.alerts.length > 0 && (
                      <Alert status="warning">
                        <AlertIcon />
                        <Box>
                          {component.alerts.map((alert, idx) => (
                            <div key={idx}>{alert}</div>
                          ))}
                        </Box>
                      </Alert>
                    )}

                    {/* Metrics Table */}
                    <Table variant="simple" size="sm">
                      <Tbody>
                        <Tr>
                          <Td fontWeight="bold">CPU Utilization</Td>
                          <Td textAlign="right">
                            {component.cpu_util?.toFixed(1)}%
                          </Td>
                        </Tr>
                        <Tr bg="gray.50">
                          <Td fontWeight="bold">Memory Utilization</Td>
                          <Td textAlign="right">
                            {component.memory_util?.toFixed(1)}%
                          </Td>
                        </Tr>
                        <Tr>
                          <Td fontWeight="bold">P99 Latency</Td>
                          <Td textAlign="right">
                            {component.latency_p99?.toFixed(1)}ms
                          </Td>
                        </Tr>
                        <Tr bg="gray.50">
                          <Td fontWeight="bold">Error Rate</Td>
                          <Td textAlign="right">
                            {(component.error_rate * 100).toFixed(2)}%
                          </Td>
                        </Tr>
                        {component.requests_per_sec && (
                          <Tr>
                            <Td fontWeight="bold">Requests/Sec</Td>
                            <Td textAlign="right">
                              {component.requests_per_sec.toFixed(1)}
                            </Td>
                          </Tr>
                        )}
                      </Tbody>
                    </Table>
                  </VStack>
                </Card>
              ))}
            </VStack>
          </TabPanel>

          {/* Alerts Tab */}
          <TabPanel>
            <VStack spacing={4} align="stretch">
              {alerts.length === 0 ? (
                <Alert status="success">
                  <AlertIcon />
                  <AlertTitle>All Clear!</AlertTitle>
                  <AlertDescription>No active alerts at this time.</AlertDescription>
                </Alert>
              ) : (
                alerts.map((alert) => (
                  <Alert
                    key={alert.id}
                    status={alert.severity === 'critical' ? 'error' : 'warning'}
                    variant="left-accent"
                    borderRadius="md"
                  >
                    <VStack align="stretch" width="full" spacing={2}>
                      <HStack justify="space-between">
                        <HStack>
                          <AlertIcon />
                          <Box>
                            <AlertTitle>{alert.title}</AlertTitle>
                            <AlertDescription fontSize="sm">
                              {alert.component} •{' '}
                              {new Date(alert.timestamp).toLocaleTimeString()}
                            </AlertDescription>
                          </Box>
                        </HStack>
                        <CloseButton onClick={() => dismissAlert(alert.id)} />
                      </HStack>

                      <Box pl={6}>
                        <p>{alert.description}</p>
                        <Heading size="sm" mt={3} mb={2}>
                          Recommended Actions
                        </Heading>
                        <UnorderedList pl={4}>
                          {alert.actions.map((action, idx) => (
                            <ListItem key={idx} fontSize="sm">
                              {action}
                            </ListItem>
                          ))}
                        </UnorderedList>
                      </Box>
                    </VStack>
                  </Alert>
                ))
              )}
            </VStack>
          </TabPanel>

          {/* Services Tab */}
          <TabPanel>
            <Table variant="striped" colorScheme="gray">
              <Thead>
                <Tr bg="gray.100">
                  <Th>Service</Th>
                  <Th>Status</Th>
                  <Th>Uptime</Th>
                </Tr>
              </Thead>
              <Tbody>
                {healthStatus.services.map((service) => (
                  <Tr key={service.name}>
                    <Td fontWeight="bold">{service.name}</Td>
                    <Td>
                      <Badge colorScheme="green">{service.status.toUpperCase()}</Badge>
                    </Td>
                    <Td>{service.uptime_percent.toFixed(2)}%</Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          </TabPanel>
        </TabPanels>
      </Tabs>
    </Box>
  )
}

export default SystemHealthMonitor
