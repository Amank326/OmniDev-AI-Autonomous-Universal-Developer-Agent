/**
 * Model Optimization Dashboard
 * Comprehensive monitoring and control dashboard for model optimization operations.
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
  Input,
  Select,
  Badge,
  useToast,
  Flex,
  Icon,
  Alert,
  AlertIcon,
  Progress,
  Spinner,
  Grid,
  GridItem,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  useDisclosure,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  StatArrow
} from '@chakra-ui/react'
import { CheckCircleIcon, WarningIcon, TimeIcon, DownloadIcon } from '@chakra-ui/icons'
import { LineChart, Line, BarChart, Bar, CartesianGrid, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts'

export const ModelOptimizationDashboard = () => {
  // State
  const [models, setModels] = useState([])
  const [selectedModel, setSelectedModel] = useState(null)
  const [optimizations, setOptimizations] = useState([])
  const [activeJobs, setActiveJobs] = useState([])
  const [recommendations, setRecommendations] = useState([])
  const [optimizationId, setOptimizationId] = useState('')
  const [optimizationType, setOptimizationType] = useState('quantization')
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState(0)
  const [performanceHistory, setPerformanceHistory] = useState([])

  const toast = useToast()
  const { isOpen: isModalOpen, onOpen: onModalOpen, onClose: onModalClose } = useDisclosure()

  // Load initial data
  useEffect(() => {
    const mockModels = [
      {
        model_id: 'classifier_prod',
        model_name: 'Production Classifier',
        model_version: 3,
        current_latency_ms: 120,
        original_latency_ms: 250,
        current_size_mb: 85,
        original_size_mb: 850
      },
      {
        model_id: 'detector_v2',
        model_name: 'Object Detector',
        model_version: 2,
        current_latency_ms: 450,
        original_latency_ms: 1200,
        current_size_mb: 250,
        original_size_mb: 2100
      }
    ]

    const mockOptimizations = [
      {
        optimization_id: 'opt_1',
        model_id: 'classifier_prod',
        optimization_type: 'quantization_int8',
        status: 'completed',
        compression_ratio: 4.0,
        accuracy_drop_percent: 0.5,
        latency_improvement_percent: 35,
        created_at: '2024-01-15T10:00:00Z'
      },
      {
        optimization_id: 'opt_2',
        model_id: 'classifier_prod',
        optimization_type: 'pruning',
        status: 'completed',
        sparsity_achieved: 0.65,
        accuracy_drop_percent: 0.8,
        latency_improvement_percent: 42,
        created_at: '2024-01-14T14:30:00Z'
      },
      {
        optimization_id: 'opt_3',
        model_id: 'detector_v2',
        optimization_type: 'distillation',
        status: 'in_progress',
        progress_percent: 65,
        created_at: '2024-01-15T09:00:00Z'
      }
    ]

    const mockActiveJobs = [
      {
        job_id: 'job_1',
        model_id: 'detector_v2',
        optimization_type: 'distillation',
        status: 'processing',
        progress_percent: 65,
        teacher_model_version: 2,
        temperature: 4.0,
        estimated_completion_seconds: 120
      }
    ]

    const mockRecommendations = [
      {
        recommendation_id: 'rec_1',
        model_id: 'detector_v2',
        optimization: 'quantization_int8',
        priority: 'critical',
        expected_improvement_percent: 40,
        expected_accuracy_drop_percent: 0.5,
        effort: 'medium'
      },
      {
        recommendation_id: 'rec_2',
        model_id: 'detector_v2',
        optimization: 'graph_optimization',
        priority: 'high',
        expected_improvement_percent: 22,
        expected_accuracy_drop_percent: 0.0,
        effort: 'low'
      }
    ]

    const mockHistory = [
      { timestamp: '10:00', latency_ms: 250, size_mb: 850, optimizations: 0 },
      { timestamp: '11:00', latency_ms: 180, size_mb: 580, optimizations: 1 },
      { timestamp: '12:00', latency_ms: 120, size_mb: 85, optimizations: 3 },
      { timestamp: '13:00', latency_ms: 120, size_mb: 85, optimizations: 3 },
      { timestamp: '14:00', latency_ms: 119, size_mb: 85, optimizations: 3 }
    ]

    setModels(mockModels)
    if (mockModels.length > 0) {
      setSelectedModel(mockModels[0].model_id)
    }
    setOptimizations(mockOptimizations)
    setActiveJobs(mockActiveJobs)
    setRecommendations(mockRecommendations)
    setPerformanceHistory(mockHistory)
  }, [])

  // Event handlers
  const handleStartOptimization = async () => {
    if (!selectedModel) {
      toast({ title: 'Error', description: 'Select a model', status: 'error' })
      return
    }

    try {
      setLoading(true)

      const endpoint = `/api/v1/optimization/models/${selectedModel}/${optimizationType === 'quantization' ? 'quantize' : optimizationType === 'pruning' ? 'prune' : 'distill'}`

      const payload = {
        model_version: 1,
        [optimizationType === 'quantization' ? 'quantization_type' : 'pruning_strategy' || 'distillation_method']: 'int8',
        sparsity_target: 0.5,
        teacher_model_id: selectedModel
      }

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Workspace-ID': 'workspace_123'
        },
        body: JSON.stringify(payload)
      })

      const data = await response.json()

      setOptimizationId(data.job_id || data.optimization_id)

      toast({
        title: 'Success',
        description: `${optimizationType} optimization started`,
        status: 'success'
      })

      onModalClose()
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to start optimization',
        status: 'error'
      })
    } finally {
      setLoading(false)
    }
  }

  // Render functions
  const renderModelOverview = () => (
    <Grid templateColumns="repeat(4, 1fr)" gap={4}>
      {models.map(model => {
        const latencyImprovement = ((model.original_latency_ms - model.current_latency_ms) / model.original_latency_ms * 100)
        const sizeReduction = ((model.original_size_mb - model.current_size_mb) / model.original_size_mb * 100)

        return (
          <Card
            key={model.model_id}
            p={4}
            border="1px"
            borderColor={selectedModel === model.model_id ? 'blue.500' : 'gray.200'}
            cursor="pointer"
            onClick={() => setSelectedModel(model.model_id)}
          >
            <Heading size="sm" mb={3}>{model.model_name}</Heading>
            <VStack align="stretch" spacing={2}>
              <Stat>
                <StatLabel fontSize="xs">Latency Improvement</StatLabel>
                <StatNumber fontSize="md">{latencyImprovement.toFixed(0)}%</StatNumber>
                <StatHelpText>
                  <StatArrow type="decrease" />
                  {model.current_latency_ms}ms
                </StatHelpText>
              </Stat>
              <Stat>
                <StatLabel fontSize="xs">Size Reduction</StatLabel>
                <StatNumber fontSize="md">{sizeReduction.toFixed(0)}%</StatNumber>
                <StatHelpText>
                  {model.current_size_mb}MB
                </StatHelpText>
              </Stat>
            </VStack>
          </Card>
        )
      })}
    </Grid>
  )

  const renderActiveJobs = () => (
    <VStack spacing={3} align="stretch">
      {activeJobs.length === 0 ? (
        <Box p={8} textAlign="center" color="gray.500">
          No active optimization jobs
        </Box>
      ) : (
        activeJobs.map(job => (
          <Card key={job.job_id} p={4} bg="blue.50">
            <HStack justify="space-between" mb={2}>
              <Box>
                <Heading size="sm">{job.optimization_type}</Heading>
                <Badge colorScheme="blue" mt={1}>{job.status}</Badge>
              </Box>
              <Box textAlign="right">
                <Box fontSize="sm" color="gray.600">
                  Model: {job.model_id}
                </Box>
                <Box fontSize="sm" color="gray.600">
                  ETA: {job.estimated_completion_seconds}s
                </Box>
              </Box>
            </HStack>
            <Progress value={job.progress_percent} size="sm" colorScheme="blue" />
            <Box fontSize="xs" color="gray.600" mt={1}>{job.progress_percent}% complete</Box>
          </Card>
        ))
      )}
    </VStack>
  )

  const renderOptimizations = () => (
    <Table variant="simple" size="sm">
      <Thead>
        <Tr bg="gray.100">
          <Th>Optimization</Th>
          <Th>Model</Th>
          <Th>Status</Th>
          <Th>Improvement</Th>
          <Th>Accuracy Loss</Th>
          <Th>Date</Th>
        </Tr>
      </Thead>
      <Tbody>
        {optimizations.map(opt => (
          <Tr key={opt.optimization_id} _hover={{ bg: 'gray.50' }}>
            <Td fontSize="sm" fontWeight="bold">{opt.optimization_type}</Td>
            <Td fontSize="sm">{opt.model_id}</Td>
            <Td>
              <Badge colorScheme={opt.status === 'completed' ? 'green' : 'yellow'}>
                {opt.status}
              </Badge>
            </Td>
            <Td fontSize="sm">
              {opt.latency_improvement_percent ? `${opt.latency_improvement_percent}%` : `${opt.compression_ratio}x`}
            </Td>
            <Td fontSize="sm" color={opt.accuracy_drop_percent > 1 ? 'red.600' : 'green.600'}>
              {opt.accuracy_drop_percent.toFixed(2)}%
            </Td>
            <Td fontSize="xs" color="gray.500">
              {new Date(opt.created_at).toLocaleDateString()}
            </Td>
          </Tr>
        ))}
      </Tbody>
    </Table>
  )

  const renderRecommendations = () => (
    <VStack spacing={3} align="stretch">
      {recommendations.map(rec => (
        <Card key={rec.recommendation_id} p={4}>
          <HStack justify="space-between" mb={2}>
            <Box>
              <Heading size="sm">{rec.optimization}</Heading>
              <Badge
                colorScheme={
                  rec.priority === 'critical' ? 'red' :
                  rec.priority === 'high' ? 'orange' : 'blue'
                }
                mt={1}
              >
                {rec.priority}
              </Badge>
            </Box>
            <Button
              size="sm"
              colorScheme="blue"
              onClick={onModalOpen}
            >
              Apply
            </Button>
          </HStack>
          <Grid templateColumns="repeat(3, 1fr)" gap={3}>
            <Box>
              <Box fontSize="xs" color="gray.600">Expected Improvement</Box>
              <Box fontSize="sm" fontWeight="bold">{rec.expected_improvement_percent}%</Box>
            </Box>
            <Box>
              <Box fontSize="xs" color="gray.600">Accuracy Loss</Box>
              <Box fontSize="sm" fontWeight="bold">{rec.expected_accuracy_drop_percent}%</Box>
            </Box>
            <Box>
              <Box fontSize="xs" color="gray.600">Effort</Box>
              <Box fontSize="sm" fontWeight="bold">{rec.effort}</Box>
            </Box>
          </Grid>
        </Card>
      ))}
    </VStack>
  )

  const renderPerformancePlot = () => (
    <Card p={4}>
      <Heading size="sm" mb={4}>Performance History</Heading>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={performanceHistory}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="timestamp" />
          <YAxis yAxisId="left" label={{ value: 'Latency (ms)', angle: -90, position: 'insideLeft' }} />
          <YAxis yAxisId="right" orientation="right" label={{ value: 'Size (MB)', angle: 90, position: 'insideRight' }} />
          <Tooltip />
          <Legend />
          <Line yAxisId="left" type="monotone" dataKey="latency_ms" stroke="#3182ce" name="Latency (ms)" />
          <Line yAxisId="right" type="monotone" dataKey="size_mb" stroke="#ed8936" name="Size (MB)" />
        </LineChart>
      </ResponsiveContainer>
    </Card>
  )

  return (
    <Box p={6}>
      <Heading mb={6}>Model Optimization Dashboard</Heading>

      {/* Model Overview */}
      <Box mb={6}>
        <Heading size="md" mb={4}>Models</Heading>
        {renderModelOverview()}
      </Box>

      {/* Tabs */}
      <Tabs index={activeTab} onChange={setActiveTab}>
        <TabList mb={4}>
          <Tab>Active Jobs</Tab>
          <Tab>Completed Optimizations</Tab>
          <Tab>Recommendations</Tab>
          <Tab>Performance</Tab>
        </TabList>

        <TabPanels>
          <TabPanel>
            {renderActiveJobs()}
          </TabPanel>
          <TabPanel>
            {renderOptimizations()}
          </TabPanel>
          <TabPanel>
            {renderRecommendations()}
          </TabPanel>
          <TabPanel>
            {renderPerformancePlot()}
          </TabPanel>
        </TabPanels>
      </Tabs>

      {/* Action Button */}
      <Box mt={6}>
        <Button colorScheme="blue" onClick={onModalOpen}>
          Start Optimization
        </Button>
      </Box>

      {/* Modal */}
      <Modal isOpen={isModalOpen} onClose={onModalClose}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Start Optimization</ModalHeader>
          <ModalBody>
            <VStack spacing={4}>
              <FormControl>
                <FormLabel>Model</FormLabel>
                <Select
                  value={selectedModel || ''}
                  onChange={e => setSelectedModel(e.target.value)}
                >
                  {models.map(m => (
                    <option key={m.model_id} value={m.model_id}>
                      {m.model_name}
                    </option>
                  ))}
                </Select>
              </FormControl>
              <FormControl>
                <FormLabel>Optimization Type</FormLabel>
                <Select
                  value={optimizationType}
                  onChange={e => setOptimizationType(e.target.value)}
                >
                  <option value="quantization">Quantization (INT8)</option>
                  <option value="pruning">Pruning</option>
                  <option value="distillation">Distillation</option>
                  <option value="graph_optimization">Graph Optimization</option>
                </Select>
              </FormControl>
            </VStack>
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onModalClose}>
              Cancel
            </Button>
            <Button
              colorScheme="blue"
              onClick={handleStartOptimization}
              isLoading={loading}
            >
              Start
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  )
}

export default ModelOptimizationDashboard
