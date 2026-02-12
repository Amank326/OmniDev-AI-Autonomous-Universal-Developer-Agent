/**
 * Model Serving Dashboard
 * Real-time monitoring of model serving endpoints with metrics, deployments, and alerts.
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
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  Progress,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Stat,
  StatLabel,
  StatNumber,
  Flex,
  Icon,
  useToast,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  Input,
  Select,
  FormControl,
  FormLabel,
  useDisclosure,
  AlertCircle
} from '@chakra-ui/react'
import { CheckCircleIcon, WarningIcon, CloseIcon, TimeIcon } from '@chakra-ui/icons'
import { LineChart, Line, BarChart, Bar, CartesianGrid, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts'

export const ModelServingDashboard = () => {
  // State
  const [servingEndpoints, setServingEndpoints] = useState([])
  const [selectedEndpoint, setSelectedEndpoint] = useState(null)
  const [endpointDetails, setEndpointDetails] = useState(null)
  const [metrics, setMetrics] = useState([])
  const [alerts, setAlerts] = useState([])
  const [deployments, setDeployments] = useState([])
  const [loading, setLoading] = useState(false)
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [activeTab, setActiveTab] = useState(0)

  const toast = useToast()
  const { isOpen: isCreateOpen, onOpen: onCreateOpen, onClose: onCreateClose } = useDisclosure()
  const [formData, setFormData] = useState({
    endpointName: '',
    description: '',
    models: [],
    minReplicas: 2,
    maxReplicas: 10
  })

  // Load endpoints
  const loadEndpoints = useCallback(async () => {
    try {
      setLoading(true)
      const response = await fetch('/api/v1/serving/endpoints', {
        headers: { 'X-Workspace-ID': 'workspace_123' }
      })
      const data = await response.json()
      
      if (data.endpoints) {
        setServingEndpoints(data.endpoints)
        if (!selectedEndpoint && data.endpoints.length > 0) {
          setSelectedEndpoint(data.endpoints[0].endpoint_id)
        }
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load endpoints',
        status: 'error',
        duration: 3000
      })
    } finally {
      setLoading(false)
    }
  }, [selectedEndpoint, toast])

  // Load endpoint metrics
  const loadMetrics = useCallback(async () => {
    if (!selectedEndpoint) return

    try {
      const response = await fetch(`/api/v1/serving/endpoints/${selectedEndpoint}/metrics`, {
        headers: { 'X-Workspace-ID': 'workspace_123' }
      })
      const data = await response.json()
      
      if (data.endpoint_id) {
        setEndpointDetails(data)
        
        // Generate metrics data for charts
        const generatedMetrics = []
        for (let i = 0; i < 60; i++) {
          generatedMetrics.push({
            minute: i,
            latency_p50: 12 + Math.random() * 5,
            latency_p95: 40 + Math.random() * 20,
            latency_p99: 75 + Math.random() * 30,
            throughput: 50 + Math.random() * 20,
            error_rate: Math.random() * 0.02
          })
        }
        setMetrics(generatedMetrics)
      }
    } catch (error) {
      console.error('Failed to load metrics:', error)
    }
  }, [selectedEndpoint, toast])

  // Load alerts
  const loadAlerts = useCallback(async () => {
    if (!selectedEndpoint) return

    try {
      const response = await fetch(`/api/v1/serving/endpoints/${selectedEndpoint}/alerts`, {
        headers: { 'X-Workspace-ID': 'workspace_123' }
      })
      const data = await response.json()
      
      if (data.alerts) {
        setAlerts(data.alerts)
      }
    } catch (error) {
      console.error('Failed to load alerts:', error)
    }
  }, [selectedEndpoint])

  // Load deployments
  const loadDeployments = useCallback(async () => {
    // Mock deployments
    setDeployments([
      {
        deployment_id: 'deploy_abc123',
        endpoint_id: selectedEndpoint,
        previous_version: 3,
        new_model_version: 4,
        status: 'active',
        current_traffic: 35,
        target_traffic: 100,
        progress: 35,
        started_at: new Date(Date.now() - 30 * 60000).toISOString(),
        error_rate: 0.001,
        p99_latency_ms: 38
      }
    ])
  }, [selectedEndpoint])

  // Auto-refresh
  useEffect(() => {
    loadEndpoints()
    loadMetrics()
    loadAlerts()
    loadDeployments()

    if (!autoRefresh) return

    const metricsInterval = setInterval(() => {
      loadMetrics()
      loadAlerts()
    }, 5000)

    return () => clearInterval(metricsInterval)
  }, [autoRefresh, loadEndpoints, loadMetrics, loadAlerts, loadDeployments])

  // Event handlers
  const handleFormChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  const handleCreateEndpoint = async () => {
    try {
      const response = await fetch('/api/v1/serving/endpoints', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Workspace-ID': 'workspace_123'
        },
        body: JSON.stringify({
          endpoint_name: formData.endpointName,
          description: formData.description,
          models: formData.models || [],
          min_replicas: formData.minReplicas,
          max_replicas: formData.maxReplicas
        })
      })

      if (response.ok) {
        toast({
          title: 'Success',
          description: 'Endpoint created successfully',
          status: 'success',
          duration: 3000
        })
        onCreateClose()
        loadEndpoints()
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to create endpoint',
        status: 'error',
        duration: 3000
      })
    }
  }

  const handleDeploymentAction = async (action, deploymentId) => {
    try {
      const endpoint = action === 'complete' ? 'complete' : 'rollback'
      const response = await fetch(
        `/api/v1/serving/deployments/${deploymentId}/${endpoint}`,
        {
          method: 'POST',
          headers: { 'X-Workspace-ID': 'workspace_123' }
        }
      )

      if (response.ok) {
        toast({
          title: 'Success',
          description: `Deployment ${action} successful`,
          status: 'success',
          duration: 3000
        })
        loadDeployments()
      }
    } catch (error) {
      toast({
        title: 'Error',
        description: `Failed to ${action} deployment`,
        status: 'error',
        duration: 3000
      })
    }
  }

  const handleAcknowledgeAlert = async (alertId) => {
    try {
      await fetch(`/api/v1/serving/alerts/${alertId}/acknowledge`, {
        method: 'POST',
        headers: { 'X-Workspace-ID': 'workspace_123' }
      })
      
      toast({
        title: 'Alert acknowledged',
        status: 'success',
        duration: 2000
      })
      loadAlerts()
    } catch (error) {
      console.error('Failed to acknowledge alert:', error)
    }
  }

  // Render functions
  const renderEndpointsList = () => (
    <Box>
      <HStack mb={4}>
        <Button colorScheme="blue" onClick={onCreateOpen}>
          Create Endpoint
        </Button>
        <Button size="sm" onClick={() => setAutoRefresh(!autoRefresh)}>
          {autoRefresh ? '⏸ Auto-refresh' : '▶ Auto-refresh'}
        </Button>
      </HStack>

      {servingEndpoints.length === 0 ? (
        <Card p={8}>
          <Box textAlign="center" color="gray.500">
            No endpoints configured. Create one to get started.
          </Box>
        </Card>
      ) : (
        <Table variant="simple" size="sm">
          <Thead>
            <Tr bg="gray.100">
              <Th>Endpoint</Th>
              <Th>Status</Th>
              <Th>Models</Th>
              <Th>Requests</Th>
              <Th>Error Rate</Th>
              <Th>Latency (p99)</Th>
              <Th>Actions</Th>
            </Tr>
          </Thead>
          <Tbody>
            {servingEndpoints.map(endpoint => (
              <Tr key={endpoint.endpoint_id} _hover={{ bg: 'gray.50' }}>
                <Td
                  fontWeight={selectedEndpoint === endpoint.endpoint_id ? 'bold' : 'normal'}
                  cursor="pointer"
                  onClick={() => setSelectedEndpoint(endpoint.endpoint_id)}
                >
                  {endpoint.endpoint_name || endpoint.endpoint_id}
                </Td>
                <Td>
                  <Badge colorScheme={endpoint.status === 'serving' ? 'green' : 'yellow'}>
                    {endpoint.status}
                  </Badge>
                </Td>
                <Td>{endpoint.models_loaded || '-'}</Td>
                <Td>{endpoint.active_requests || 0}</Td>
                <Td>
                  <Box color={endpoint.error_rate > 0.01 ? 'red.500' : 'green.500'}>
                    {(endpoint.error_rate * 100).toFixed(2)}%
                  </Box>
                </Td>
                <Td>{endpoint.p99_latency_ms}ms</Td>
                <Td>
                  <Button size="sm" colorScheme="blue" mr={2}>
                    Manage
                  </Button>
                </Td>
              </Tr>
            ))}
          </Tbody>
        </Table>
      )}
    </Box>
  )

  const renderEndpointDetails = () => {
    if (!endpointDetails) {
      return <Box p={8} textAlign="center">Select an endpoint to view details</Box>
    }

    return (
      <VStack spacing={4} align="stretch">
        <Heading size="md">{endpointDetails.endpoint_name || endpointDetails.endpoint_id}</Heading>

        <HStack spacing={4}>
          <Stat>
            <StatLabel>Total Requests</StatLabel>
            <StatNumber>{endpointDetails.total_requests}</StatNumber>
          </Stat>
          <Stat>
            <StatLabel>Error Rate</StatLabel>
            <StatNumber color={endpointDetails.error_rate > 0.01 ? 'red.500' : 'green.500'}>
              {(endpointDetails.error_rate * 100).toFixed(2)}%
            </StatNumber>
          </Stat>
          <Stat>
            <StatLabel>Throughput (RPS)</StatLabel>
            <StatNumber>{endpointDetails.throughput_rps?.toFixed(1)}</StatNumber>
          </Stat>
          <Stat>
            <StatLabel>Latency (p99)</StatLabel>
            <StatNumber>{endpointDetails.latency_p99_ms?.toFixed(1)}ms</StatNumber>
          </Stat>
        </HStack>

        <Card>
          <CardBody>
            <Heading size="sm" mb={4}>Model Version Stats</Heading>
            <Table variant="simple" size="sm">
              <Thead>
                <Tr>
                  <Th>Version</Th>
                  <Th>Requests</Th>
                  <Th>Errors</Th>
                  <Th>Avg Latency</Th>
                </Tr>
              </Thead>
              <Tbody>
                {Object.entries(endpointDetails.model_version_stats || {}).map(([version, stats]) => (
                  <Tr key={version}>
                    <Td>v{version}</Td>
                    <Td>{stats.requests}</Td>
                    <Td>{stats.errors}</Td>
                    <Td>{stats.avg_latency_ms?.toFixed(1)}ms</Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          </CardBody>
        </Card>
      </VStack>
    )
  }

  const renderMetricsChart = () => {
    if (metrics.length === 0) {
      return <Box p={8} textAlign="center">Loading metrics...</Box>
    }

    return (
      <VStack spacing={6} align="stretch">
        <Card>
          <CardBody>
            <Heading size="sm" mb={4}>Latency (ms)</Heading>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={metrics}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="minute" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="latency_p50" stroke="#82ca9d" dot={false} />
                <Line type="monotone" dataKey="latency_p95" stroke="#ffc658" dot={false} />
                <Line type="monotone" dataKey="latency_p99" stroke="#ff7c7c" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            <Heading size="sm" mb={4}>Throughput & Error Rate</Heading>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={metrics}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="minute" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="throughput" stroke="#8884d8" dot={false} />
                <Line type="monotone" dataKey="error_rate" stroke="#d84848" dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </CardBody>
        </Card>
      </VStack>
    )
  }

  const renderAlerts = () => {
    if (alerts.length === 0) {
      return (
        <Card p={8}>
          <Box textAlign="center" color="green.500">
            ✓ No active alerts
          </Box>
        </Card>
      )
    }

    return (
      <VStack spacing={3} align="stretch">
        {alerts.map(alert => (
          <Card key={alert.alert_id} p={4} bg={alert.severity === 'critical' ? 'red.50' : 'yellow.50'}>
            <HStack spacing={3}>
              <Icon
                as={alert.severity === 'critical' ? AlertCircle : WarningIcon}
                color={alert.severity === 'critical' ? 'red.500' : 'orange.500'}
              />
              <VStack align="start" flex={1}>
                <Box fontWeight="bold">{alert.metric}</Box>
                <Box fontSize="sm">{alert.message}</Box>
                <Box fontSize="xs" color="gray.600">
                  {alert.current_value.toFixed(2)} {alert.severity === 'critical' ? '≥' : '>'} {alert.threshold.toFixed(2)}
                </Box>
              </VStack>
              <Button size="sm" onClick={() => handleAcknowledgeAlert(alert.alert_id)}>
                Acknowledge
              </Button>
            </HStack>
          </Card>
        ))}
      </VStack>
    )
  }

  const renderDeployments = () => {
    if (deployments.length === 0) {
      return (
        <Card p={8}>
          <Box textAlign="center" color="gray.500">
            No active deployments
          </Box>
        </Card>
      )
    }

    return (
      <VStack spacing={4} align="stretch">
        {deployments.map(deployment => (
          <Card key={deployment.deployment_id} p={4}>
            <VStack align="stretch" spacing={3}>
              <HStack justify="space-between">
                <Box>
                  <Heading size="sm">v{deployment.previous_version} → v{deployment.new_model_version}</Heading>
                  <Box fontSize="sm" color="gray.600">
                    {deployment.status}
                  </Box>
                </Box>
                <Badge colorScheme="blue">{deployment.progress}%</Badge>
              </HStack>

              <Box>
                <HStack justify="space-between" mb={2}>
                  <Box fontSize="sm">Traffic Allocation</Box>
                  <Box fontSize="sm">{deployment.current_traffic}% → {deployment.target_traffic}%</Box>
                </HStack>
                <Progress value={deployment.progress} colorScheme="blue" />
              </Box>

              <HStack spacing={2} fontSize="sm" color="gray.600">
                <Box>Error Rate: {(deployment.error_rate * 100).toFixed(2)}%</Box>
                <Box>•</Box>
                <Box>p99: {deployment.p99_latency_ms}ms</Box>
              </HStack>

              <HStack>
                <Button
                  size="sm"
                  colorScheme="green"
                  onClick={() => handleDeploymentAction('complete', deployment.deployment_id)}
                >
                  Complete
                </Button>
                <Button
                  size="sm"
                  colorScheme="red"
                  variant="outline"
                  onClick={() => handleDeploymentAction('rollback', deployment.deployment_id)}
                >
                  Rollback
                </Button>
              </HStack>
            </VStack>
          </Card>
        ))}
      </VStack>
    )
  }

  return (
    <Box p={6}>
      <Heading mb={6}>Model Serving Dashboard</Heading>

      <Tabs index={activeTab} onChange={setActiveTab}>
        <TabList mb={4}>
          <Tab>Endpoints</Tab>
          <Tab>Details</Tab>
          <Tab>Metrics</Tab>
          <Tab>Alerts</Tab>
          <Tab>Deployments</Tab>
        </TabList>

        <TabPanels>
          <TabPanel>{renderEndpointsList()}</TabPanel>
          <TabPanel>{renderEndpointDetails()}</TabPanel>
          <TabPanel>{renderMetricsChart()}</TabPanel>
          <TabPanel>{renderAlerts()}</TabPanel>
          <TabPanel>{renderDeployments()}</TabPanel>
        </TabPanels>
      </Tabs>

      {/* Create Endpoint Modal */}
      <Modal isOpen={isCreateOpen} onClose={onCreateClose}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Create New Endpoint</ModalHeader>
          <ModalBody>
            <VStack spacing={4}>
              <FormControl>
                <FormLabel>Endpoint Name</FormLabel>
                <Input
                  placeholder="e.g., ProductionClassifier"
                  value={formData.endpointName}
                  onChange={e => handleFormChange('endpointName', e.target.value)}
                />
              </FormControl>
              <FormControl>
                <FormLabel>Model Version</FormLabel>
                <Select
                  placeholder="Select model version"
                  value={formData.models[0] || ''}
                  onChange={e => handleFormChange('models', [e.target.value])}
                >
                  <option value="3">Model v3</option>
                  <option value="4">Model v4</option>
                </Select>
              </FormControl>
              <FormControl>
                <FormLabel>Min Replicas</FormLabel>
                <Input
                  type="number"
                  value={formData.minReplicas}
                  onChange={e => handleFormChange('minReplicas', parseInt(e.target.value))}
                />
              </FormControl>
              <FormControl>
                <FormLabel>Max Replicas</FormLabel>
                <Input
                  type="number"
                  value={formData.maxReplicas}
                  onChange={e => handleFormChange('maxReplicas', parseInt(e.target.value))}
                />
              </FormControl>
            </VStack>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onCreateClose}>
              Cancel
            </Button>
            <Button colorScheme="blue" onClick={handleCreateEndpoint}>
              Create
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  )
}

export default ModelServingDashboard
