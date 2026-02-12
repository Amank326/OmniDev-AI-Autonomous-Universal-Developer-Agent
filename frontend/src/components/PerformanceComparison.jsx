/**
 * Performance Comparison Component
 * Side-by-side comparison of model performance across optimization versions.
 */

import React, { useState, useEffect } from 'react'
import {
  Box,
  Button,
  Card,
  CardBody,
  Heading,
  HStack,
  VStack,
  Grid,
  GridItem,
  FormControl,
  FormLabel,
  Select,
  Badge,
  useToast,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  StatArrow,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Flex,
  Icon,
  Progress
} from '@chakra-ui/react'
import { CheckCircleIcon, WarningIcon } from '@chakra-ui/icons'
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  ScatterChart,
  Scatter,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts'

export const PerformanceComparison = ({ modelId = null }) => {
  // State
  const [models, setModels] = useState([])
  const [selectedModel, setSelectedModel] = useState(modelId)
  const [versions, setVersions] = useState([])
  const [selectedVersions, setSelectedVersions] = useState(['original', 'optimized'])
  const [comparisonData, setComparisonData] = useState(null)
  const [breakdownData, setBreakdownData] = useState([])
  const [latencyProfile, setLatencyProfile] = useState([])
  const [heatmapData, setHeatmapData] = useState([])
  const [loading, setLoading] = useState(false)
  const toast = useToast()

  const COLORS = ['#3182ce', '#ed8936', '#38a169', '#dd6b20', '#d69e2e']

  // Initialize
  useEffect(() => {
    const mockModels = [
      { model_id: 'classifier_prod', name: 'Production Classifier' },
      { model_id: 'detector_v2', name: 'Object Detector' },
      { model_id: 'nlp_model', name: 'NLP Model' }
    ]

    const mockVersions = [
      { version_id: 'original', label: 'Original', created_at: '2023-10-01' },
      { version_id: 'quantized_int8', label: 'Quantized INT8', created_at: '2024-01-01' },
      { version_id: 'quantized_int4', label: 'Quantized INT4', created_at: '2024-01-05' },
      { version_id: 'pruned_65', label: 'Pruned (65%)', created_at: '2024-01-10' },
      { version_id: 'distilled', label: 'Distilled', created_at: '2024-01-15' },
      { version_id: 'optimized', label: 'Graph Optimized', created_at: '2024-01-20' }
    ]

    const mockComparisonData = {
      original: {
        latency_p50: 250,
        latency_p95: 280,
        latency_p99: 310,
        throughput_requests_per_sec: 4,
        size_mb: 850,
        memory_peak_mb: 1200,
        accuracy_percent: 98.5,
        f1_score: 0.945,
        inference_power_w: 25
      },
      optimized: {
        latency_p50: 85,
        latency_p95: 92,
        latency_p99: 105,
        throughput_requests_per_sec: 12,
        size_mb: 85,
        memory_peak_mb: 320,
        accuracy_percent: 98.0,
        f1_score: 0.941,
        inference_power_w: 8
      }
    }

    const mockBreakdownData = [
      { name: 'Quantization', impact_percent: 35, models_affected: 3, avg_accuracy_loss: 0.3 },
      { name: 'Pruning', impact_percent: 42, models_affected: 2, avg_accuracy_loss: 0.8 },
      { name: 'Graph Opt', impact_percent: 22, models_affected: 3, avg_accuracy_loss: 0.0 },
      { name: 'Distillation', impact_percent: 45, models_affected: 1, avg_accuracy_loss: 1.2 },
      { name: 'Kernel Opt', impact_percent: 18, models_affected: 2, avg_accuracy_loss: 0.0 }
    ]

    const mockLatencyProfile = [
      { batch_size: 1, original: 250, quantized: 85, pruned: 145, distilled: 95 },
      { batch_size: 4, original: 280, quantized: 88, pruned: 150, distilled: 98 },
      { batch_size: 8, original: 310, quantized: 92, pruned: 155, distilled: 105 },
      { batch_size: 16, original: 350, quantized: 105, pruned: 170, distilled: 125 },
      { batch_size: 32, original: 420, quantized: 135, pruned: 210, distilled: 160 }
    ]

    const mockHeatmapData = [
      { layer: 'Input', original: 10, quantized: 2, pruned: 5, distilled: 3 },
      { layer: 'Conv1D-1', original: 85, quantized: 28, pruned: 40, distilled: 30 },
      { layer: 'Conv1D-2', original: 95, quantized: 32, pruned: 48, distilled: 38 },
      { layer: 'FC-1', original: 50, quantized: 18, pruned: 25, distilled: 20 },
      { layer: 'FC-2', original: 8, quantized: 5, pruned: 4, distilled: 3 }
    ]

    setModels(mockModels)
    if (!selectedModel && mockModels.length > 0) {
      setSelectedModel(mockModels[0].model_id)
    }
    setVersions(mockVersions)
    setComparisonData(mockComparisonData)
    setBreakdownData(mockBreakdownData)
    setLatencyProfile(mockLatencyProfile)
    setHeatmapData(mockHeatmapData)
  }, [])

  // Handlers
  const handleCompare = async () => {
    if (!selectedModel || selectedVersions.length !== 2) {
      toast({
        title: 'Error',
        description: 'Select one baseline and one optimized version',
        status: 'error'
      })
      return
    }

    setLoading(true)
    // Simulate API call
    setTimeout(() => {
      setLoading(false)
      toast({
        title: 'Success',
        description: 'Comparison loaded',
        status: 'success'
      })
    }, 500)
  }

  const calculateMetrics = () => {
    if (!comparisonData) return null

    const original = comparisonData.original
    const optimized = comparisonData.optimized

    return {
      latency_improvement: ((original.latency_p50 - optimized.latency_p50) / original.latency_p50 * 100),
      throughput_improvement: ((optimized.throughput_requests_per_sec - original.throughput_requests_per_sec) / original.throughput_requests_per_sec * 100),
      size_reduction: ((original.size_mb - optimized.size_mb) / original.size_mb * 100),
      memory_reduction: ((original.memory_peak_mb - optimized.memory_peak_mb) / original.memory_peak_mb * 100),
      power_reduction: ((original.inference_power_w - optimized.inference_power_w) / original.inference_power_w * 100),
      accuracy_loss: (original.accuracy_percent - optimized.accuracy_percent)
    }
  }

  // Renderers
  const renderMetricComparison = () => {
    const metrics = calculateMetrics()
    if (!metrics || !comparisonData) return null

    return (
      <Card p={4}>
        <Heading size="md" mb={4}>Key Metrics Comparison</Heading>
        <Grid templateColumns="repeat(3, 1fr)" gap={4}>
          <Box>
            <Stat>
              <StatLabel>Latency (P50)</StatLabel>
              <StatNumber>{comparisonData.optimized.latency_p50}ms</StatNumber>
              <StatHelpText>
                <StatArrow type="decrease" />
                {metrics.latency_improvement.toFixed(1)}%
              </StatHelpText>
            </Stat>
          </Box>
          <Box>
            <Stat>
              <StatLabel>Model Size</StatLabel>
              <StatNumber>{comparisonData.optimized.size_mb}MB</StatNumber>
              <StatHelpText>
                <StatArrow type="decrease" />
                {metrics.size_reduction.toFixed(1)}%
              </StatHelpText>
            </Stat>
          </Box>
          <Box>
            <Stat>
              <StatLabel>Throughput</StatLabel>
              <StatNumber>{comparisonData.optimized.throughput_requests_per_sec}x</StatNumber>
              <StatHelpText>
                <StatArrow type="increase" />
                {metrics.throughput_improvement.toFixed(1)}%
              </StatHelpText>
            </Stat>
          </Box>
          <Box>
            <Stat>
              <StatLabel>Peak Memory</StatLabel>
              <StatNumber>{comparisonData.optimized.memory_peak_mb}MB</StatNumber>
              <StatHelpText>
                <StatArrow type="decrease" />
                {metrics.memory_reduction.toFixed(1)}%
              </StatHelpText>
            </Stat>
          </Box>
          <Box>
            <Stat>
              <StatLabel>Inference Power</StatLabel>
              <StatNumber>{comparisonData.optimized.inference_power_w}W</StatNumber>
              <StatHelpText>
                <StatArrow type="decrease" />
                {metrics.power_reduction.toFixed(1)}%
              </StatHelpText>
            </Stat>
          </Box>
          <Box>
            <Stat>
              <StatLabel>Accuracy</StatLabel>
              <StatNumber>{comparisonData.optimized.accuracy_percent}%</StatNumber>
              <StatHelpText color={metrics.accuracy_loss > 1 ? 'red.600' : 'green.600'}>
                {metrics.accuracy_loss > 0 ? '-' : '+'}{Math.abs(metrics.accuracy_loss).toFixed(2)}%
              </StatHelpText>
            </Stat>
          </Box>
        </Grid>
      </Card>
    )
  }

  const renderLatencyComparison = () => (
    <Card p={4}>
      <Heading size="md" mb={4}>Latency by Batch Size</Heading>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={latencyProfile}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="batch_size" label={{ value: 'Batch Size', position: 'bottom', offset: 10 }} />
          <YAxis label={{ value: 'Latency (ms)', angle: -90, position: 'insideLeft' }} />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="original" stroke="#e53e3e" name="Original" strokeWidth={2} />
          <Line type="monotone" dataKey="quantized" stroke="#3182ce" name="Quantized" strokeWidth={2} />
          <Line type="monotone" dataKey="pruned" stroke="#ed8936" name="Pruned" strokeWidth={2} />
          <Line type="monotone" dataKey="distilled" stroke="#38a169" name="Distilled" strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </Card>
  )

  const renderOptimizationBreakdown = () => (
    <Card p={4}>
      <Heading size="md" mb={4}>Optimization Impact Breakdown</Heading>
      <Grid templateColumns="repeat(2, 1fr)" gap={4}>
        <Box>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={breakdownData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, impact_percent }) => `${name} ${impact_percent}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="impact_percent"
              >
                {breakdownData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </Box>
        <Box>
          <Table variant="simple" size="sm">
            <Thead>
              <Tr bg="gray.100">
                <Th>Optimization</Th>
                <Th>Impact</Th>
                <Th>Models</Th>
                <Th>Acc Loss</Th>
              </Tr>
            </Thead>
            <Tbody>
              {breakdownData.map((row, idx) => (
                <Tr key={idx} _hover={{ bg: 'gray.50' }}>
                  <Td fontSize="sm" fontWeight="bold">{row.name}</Td>
                  <Td>
                    <Progress value={row.impact_percent} size="sm" colorScheme="blue" />
                  </Td>
                  <Td fontSize="sm">{row.models_affected}</Td>
                  <Td fontSize="sm" color={row.avg_accuracy_loss > 1 ? 'red.600' : 'green.600'}>
                    {row.avg_accuracy_loss.toFixed(2)}%
                  </Td>
                </Tr>
              ))}
            </Tbody>
          </Table>
        </Box>
      </Grid>
    </Card>
  )

  const renderLayerWiseLatency = () => (
    <Card p={4}>
      <Heading size="md" mb={4}>Layer-wise Latency Breakdown</Heading>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart
          data={heatmapData}
          layout="vertical"
          margin={{ top: 5, right: 30, left: 100, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis type="number" label={{ value: 'Latency (ms)', position: 'bottom' }} />
          <YAxis dataKey="layer" type="category" width={90} />
          <Tooltip />
          <Legend />
          <Bar dataKey="original" fill="#e53e3e" name="Original" />
          <Bar dataKey="quantized" fill="#3182ce" name="Quantized" />
          <Bar dataKey="pruned" fill="#ed8936" name="Pruned" />
          <Bar dataKey="distilled" fill="#38a169" name="Distilled" />
        </BarChart>
      </ResponsiveContainer>
    </Card>
  )

  const renderDetailedMetrics = () => {
    if (!comparisonData) return null

    const metrics = calculateMetrics()

    return (
      <Card p={4}>
        <Heading size="md" mb={4}>Detailed Performance Metrics</Heading>
        <Grid templateColumns="repeat(2, 1fr)" gap={4}>
          <Box>
            <Heading size="sm" mb={3} color="gray.700">Original Model</Heading>
            <VStack align="stretch" spacing={2} fontSize="sm">
              <HStack justify="space-between">
                <span>P50 Latency:</span>
                <strong>{comparisonData.original.latency_p50}ms</strong>
              </HStack>
              <HStack justify="space-between">
                <span>P95 Latency:</span>
                <strong>{comparisonData.original.latency_p95}ms</strong>
              </HStack>
              <HStack justify="space-between">
                <span>P99 Latency:</span>
                <strong>{comparisonData.original.latency_p99}ms</strong>
              </HStack>
              <HStack justify="space-between">
                <span>Throughput:</span>
                <strong>{comparisonData.original.throughput_requests_per_sec} req/s</strong>
              </HStack>
              <HStack justify="space-between">
                <span>Model Size:</span>
                <strong>{comparisonData.original.size_mb}MB</strong>
              </HStack>
              <HStack justify="space-between">
                <span>Peak Memory:</span>
                <strong>{comparisonData.original.memory_peak_mb}MB</strong>
              </HStack>
              <HStack justify="space-between">
                <span>Accuracy:</span>
                <strong>{comparisonData.original.accuracy_percent}%</strong>
              </HStack>
              <HStack justify="space-between">
                <span>Power Draw:</span>
                <strong>{comparisonData.original.inference_power_w}W</strong>
              </HStack>
            </VStack>
          </Box>
          <Box>
            <Heading size="sm" mb={3} color="gray.700">Optimized Model</Heading>
            <VStack align="stretch" spacing={2} fontSize="sm">
              <HStack justify="space-between">
                <span>P50 Latency:</span>
                <strong color="green.600">{comparisonData.optimized.latency_p50}ms</strong>
              </HStack>
              <HStack justify="space-between">
                <span>P95 Latency:</span>
                <strong color="green.600">{comparisonData.optimized.latency_p95}ms</strong>
              </HStack>
              <HStack justify="space-between">
                <span>P99 Latency:</span>
                <strong color="green.600">{comparisonData.optimized.latency_p99}ms</strong>
              </HStack>
              <HStack justify="space-between">
                <span>Throughput:</span>
                <strong color="green.600">{comparisonData.optimized.throughput_requests_per_sec}x req/s</strong>
              </HStack>
              <HStack justify="space-between">
                <span>Model Size:</span>
                <strong color="green.600">{comparisonData.optimized.size_mb}MB</strong>
              </HStack>
              <HStack justify="space-between">
                <span>Peak Memory:</span>
                <strong color="green.600">{comparisonData.optimized.memory_peak_mb}MB</strong>
              </HStack>
              <HStack justify="space-between">
                <span>Accuracy:</span>
                <strong color={metrics.accuracy_loss > 1 ? 'red.600' : 'green.600'}>
                  {comparisonData.optimized.accuracy_percent}%
                </strong>
              </HStack>
              <HStack justify="space-between">
                <span>Power Draw:</span>
                <strong color="green.600">{comparisonData.optimized.inference_power_w}W</strong>
              </HStack>
            </VStack>
          </Box>
        </Grid>
      </Card>
    )
  }

  return (
    <Box p={6}>
      <Heading mb={6}>Performance Comparison</Heading>

      {/* Selection Controls */}
      <Card p={4} mb={6} bg="gray.50">
        <HStack spacing={4} mb={4}>
          <FormControl flex={1}>
            <FormLabel>Model</FormLabel>
            <Select
              value={selectedModel || ''}
              onChange={e => setSelectedModel(e.target.value)}
            >
              {models.map(m => (
                <option key={m.model_id} value={m.model_id}>
                  {m.name}
                </option>
              ))}
            </Select>
          </FormControl>
          <FormControl flex={1}>
            <FormLabel>Baseline Version</FormLabel>
            <Select>
              <option>Original</option>
              {versions.map(v => (
                <option key={v.version_id} value={v.version_id}>
                  {v.label}
                </option>
              ))}
            </Select>
          </FormControl>
          <FormControl flex={1}>
            <FormLabel>Optimized Version</FormLabel>
            <Select>
              <option>Latest Optimized</option>
              {versions.map(v => (
                <option key={v.version_id} value={v.version_id}>
                  {v.label}
                </option>
              ))}
            </Select>
          </FormControl>
          <Button colorScheme="blue" mt={8} onClick={handleCompare} isLoading={loading}>
            Compare
          </Button>
        </HStack>
      </Card>

      {/* Tabs */}
      <Tabs>
        <TabList mb={4}>
          <Tab>Key Metrics</Tab>
          <Tab>Latency Analysis</Tab>
          <Tab>Layer Breakdown</Tab>
          <Tab>Impact Analysis</Tab>
          <Tab>Detailed Metrics</Tab>
        </TabList>

        <TabPanels>
          <TabPanel>{renderMetricComparison()}</TabPanel>
          <TabPanel>{renderLatencyComparison()}</TabPanel>
          <TabPanel>{renderLayerWiseLatency()}</TabPanel>
          <TabPanel>{renderOptimizationBreakdown()}</TabPanel>
          <TabPanel>{renderDetailedMetrics()}</TabPanel>
        </TabPanels>
      </Tabs>
    </Box>
  )
}

export default PerformanceComparison
