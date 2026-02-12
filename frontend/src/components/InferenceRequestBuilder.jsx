/**
 * Inference Request Builder
 * Interactive tool for building, executing, and testing model inference requests.
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
  Textarea,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  useToast,
  Flex,
  IconButton,
  Icon,
  Code,
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  Progress,
  Spinner,
  Grid,
  GridItem,
  useDisclosure,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  NumberInput,
  NumberInputField,
  NumberInputStepper,
  NumberIncrementButton,
  NumberDecrementButton
} from '@chakra-ui/react'
import { DeleteIcon, CopyIcon, DownloadIcon, CheckCircleIcon, WarningIcon } from '@chakra-ui/icons'
import { LineChart, Line, BarChart, Bar, CartesianGrid, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts'

export const InferenceRequestBuilder = () => {
  // State
  const [endpoints, setEndpoints] = useState([])
  const [selectedEndpoint, setSelectedEndpoint] = useState(null)
  const [selectedVersion, setSelectedVersion] = useState(null)
  const [features, setFeatures] = useState({})
  const [featureInputs, setFeatureInputs] = useState([])
  const [requestMode, setRequestMode] = useState('sync')  // sync or async
  const [requestType, setBatchMode] = useState('single')  // single or batch
  const [batchRequests, setBatchRequests] = useState([])
  
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [requestHistory, setRequestHistory] = useState([])
  const [activeTab, setActiveTab] = useState(0)

  const toast = useToast()
  const { isOpen: isJsonOpen, onOpen: onJsonOpen, onClose: onJsonClose } = useDisclosure()
  const [jsonInput, setJsonInput] = useState('{}')

  // Load endpoints
  useEffect(() => {
    const mockEndpoints = [
      {
        endpoint_id: 'prod_classifier_1',
        endpoint_name: 'Production Classifier',
        status: 'serving',
        models: [
          { model_version: 4, model_id: 'classifier_prod' },
          { model_version: 3, model_id: 'classifier_prod' }
        ]
      },
      {
        endpoint_id: 'staging_classifier_1',
        endpoint_name: 'Staging Classifier',
        status: 'serving',
        models: [
          { model_version: 5, model_id: 'classifier_staging' }
        ]
      }
    ]
    
    setEndpoints(mockEndpoints)
    if (mockEndpoints.length > 0) {
      setSelectedEndpoint(mockEndpoints[0].endpoint_id)
      setSelectedVersion(mockEndpoints[0].models[0].model_version)
    }
  }, [])

  // Load feature inputs when endpoint selected
  useEffect(() => {
    if (selectedEndpoint) {
      // Mock feature definitions
      const featureDefinitions = [
        { name: 'feature_1', type: 'float', default: 0.5, description: 'Feature 1' },
        { name: 'feature_2', type: 'float', default: 0.0, description: 'Feature 2' },
        { name: 'feature_3', type: 'categorical', values: ['A', 'B', 'C'], default: 'A' },
        { name: 'feature_4', type: 'int', default: 0, description: 'Feature 4' }
      ]
      
      setFeatureInputs(featureDefinitions)
      
      // Initialize features with defaults
      const defaultFeatures = {}
      featureDefinitions.forEach(f => {
        defaultFeatures[f.name] = f.default
      })
      setFeatures(defaultFeatures)
    }
  }, [selectedEndpoint])

  // Event handlers
  const handleFeatureChange = (featureName, value) => {
    setFeatures(prev => ({
      ...prev,
      [featureName]: value
    }))
  }

  const handleBatchInputChange = (index, field, value) => {
    setBatchRequests(prev => {
      const updated = [...prev]
      updated[index] = { ...updated[index], [field]: value }
      return updated
    })
  }

  const handleAddBatchRequest = () => {
    const newRequest = {}
    featureInputs.forEach(f => {
      newRequest[f.name] = f.default
    })
    setBatchRequests(prev => [...prev, newRequest])
  }

  const handleRemoveBatchRequest = (index) => {
    setBatchRequests(prev => prev.filter((_, i) => i !== index))
  }

  const handleExecuteRequest = async () => {
    if (!selectedEndpoint) {
      toast({
        title: 'Error',
        description: 'Please select an endpoint',
        status: 'error'
      })
      return
    }

    try {
      setLoading(true)

      const endpoint = requestMode === 'sync' 
        ? `/api/v1/serving/endpoints/${selectedEndpoint}/predict`
        : `/api/v1/serving/endpoints/${selectedEndpoint}/predict-async`

      const payload = {
        features: features,
        model_version: selectedVersion,
        return_confidence: true
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

      setResult(data)
      
      // Add to history
      setRequestHistory(prev => [{
        request_id: data.request_id,
        timestamp: new Date().toISOString(),
        endpoint: selectedEndpoint,
        mode: requestMode,
        features: features,
        result: data,
        execution_time_ms: Math.random() * 100
      }, ...prev].slice(0, 50))

      toast({
        title: 'Success',
        description: `${requestMode === 'sync' ? 'Inference' : 'Request'} executed successfully`,
        status: 'success',
        duration: 3000
      })
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to execute request',
        status: 'error'
      })
    } finally {
      setLoading(false)
    }
  }

  const handleExecuteBatch = async () => {
    if (batchRequests.length === 0) {
      toast({
        title: 'Error',
        description: 'Add at least one request to batch',
        status: 'error'
      })
      return
    }

    try {
      setLoading(true)

      const response = await fetch(
        `/api/v1/serving/endpoints/${selectedEndpoint}/batch-predict`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Workspace-ID': 'workspace_123'
          },
          body: JSON.stringify({
            requests: batchRequests.map((req, idx) => ({
              request_id: `batch_${Date.now()}_${idx}`,
              features: req
            }))
          })
        }
      )

      const data = await response.json()

      toast({
        title: 'Batch submitted',
        description: `Batch ID: ${data.batch_id}`,
        status: 'success'
      })

      setResult(data)
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to submit batch',
        status: 'error'
      })
    } finally {
      setLoading(false)
    }
  }

  const handleLoadJson = () => {
    try {
      const parsed = JSON.parse(jsonInput)
      setFeatures(parsed)
      toast({
        title: 'Success',
        description: 'Features loaded from JSON',
        status: 'success'
      })
      onJsonClose()
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Invalid JSON format',
        status: 'error'
      })
    }
  }

  const handleExportJson = () => {
    const json = JSON.stringify(features, null, 2)
    navigator.clipboard.writeText(json)
    toast({
      title: 'Copied to clipboard',
      status: 'success',
      duration: 2000
    })
  }

  const handleLoadTemplate = (template) => {
    setFeatures(template.features)
    toast({
      title: 'Template loaded',
      status: 'success',
      duration: 2000
    })
  }

  // Render functions
  const renderFeatureBuilder = () => (
    <Card mb={4}>
      <CardBody>
        <Heading size="sm" mb={4}>Feature Builder</Heading>
        <Grid templateColumns="repeat(2, 1fr)" gap={4} mb={4}>
          {featureInputs.map(feature => (
            <FormControl key={feature.name}>
              <FormLabel fontSize="sm">{feature.name}</FormLabel>
              {feature.type === 'categorical' ? (
                <Select
                  value={features[feature.name] || feature.default}
                  onChange={e => handleFeatureChange(feature.name, e.target.value)}
                  size="sm"
                >
                  {feature.values.map(v => (
                    <option key={v} value={v}>{v}</option>
                  ))}
                </Select>
              ) : feature.type === 'int' ? (
                <NumberInput
                  value={features[feature.name] || feature.default}
                  onChange={val => handleFeatureChange(feature.name, parseInt(val))}
                  size="sm"
                >
                  <NumberInputField />
                  <NumberInputStepper>
                    <NumberIncrementButton />
                    <NumberDecrementButton />
                  </NumberInputStepper>
                </NumberInput>
              ) : (
                <Input
                  type="number"
                  step={0.01}
                  value={features[feature.name] || feature.default}
                  onChange={e => handleFeatureChange(feature.name, parseFloat(e.target.value))}
                  size="sm"
                />
              )}
              {feature.description && (
                <Box fontSize="xs" color="gray.500" mt={1}>
                  {feature.description}
                </Box>
              )}
            </FormControl>
          ))}
        </Grid>

        <HStack spacing={2}>
          <Button
            colorScheme="blue"
            size="sm"
            onClick={handleExecuteRequest}
            isLoading={loading}
          >
            Execute Request
          </Button>
          <Button size="sm" variant="outline" onClick={onJsonOpen}>
            Load from JSON
          </Button>
          <Button size="sm" variant="outline" onClick={handleExportJson}>
            Copy as JSON
          </Button>
        </HStack>
      </CardBody>
    </Card>
  )

  const renderBatchBuilder = () => (
    <Card>
      <CardBody>
        <Heading size="sm" mb={4}>Batch Request Builder</Heading>

        {batchRequests.length === 0 ? (
          <Box p={8} textAlign="center" color="gray.500">
            No batch requests. Click "Add Request" to create one.
          </Box>
        ) : (
          <VStack spacing={3} align="stretch" mb={4}>
            {batchRequests.map((req, idx) => (
              <Card key={idx} p={3} bg="gray.50">
                <HStack justify="space-between">
                  <Box flex={1}>
                    <Box fontSize="sm" fontWeight="bold">Request {idx + 1}</Box>
                    <Grid templateColumns="repeat(2, 1fr)" gap={2} mt={2}>
                      {Object.entries(req).map(([key, value]) => (
                        <Box key={key} fontSize="xs">
                          <Box color="gray.600">{key}:</Box>
                          <Input
                            type="text"
                            value={value}
                            onChange={e => handleBatchInputChange(idx, key, e.target.value)}
                            size="xs"
                          />
                        </Box>
                      ))}
                    </Grid>
                  </Box>
                  <IconButton
                    icon={<DeleteIcon />}
                    size="sm"
                    colorScheme="red"
                    variant="ghost"
                    onClick={() => handleRemoveBatchRequest(idx)}
                  />
                </HStack>
              </Card>
            ))}
          </VStack>
        )}

        <HStack spacing={2} mt={4}>
          <Button size="sm" onClick={handleAddBatchRequest}>
            Add Request
          </Button>
          <Button
            colorScheme="blue"
            size="sm"
            isLoading={loading}
            onClick={handleExecuteBatch}
            isDisabled={batchRequests.length === 0}
          >
            Execute Batch
          </Button>
        </HStack>
      </CardBody>
    </Card>
  )

  const renderResult = () => {
    if (!result) return null

    return (
      <Card mt={4} borderColor="green.300" borderWidth={1}>
        <CardBody>
          <HStack mb={4}>
            <CheckCircleIcon color="green.500" />
            <Heading size="sm">Result</Heading>
            {result.latency_ms && (
              <Badge colorScheme="blue">Latency: {result.latency_ms.toFixed(1)}ms</Badge>
            )}
          </HStack>

          <Code p={4} borderRadius="md" display="block" whiteSpace="pre-wrap" mb={4}>
            {JSON.stringify(result, null, 2)}
          </Code>

          {result.confidence_scores && (
            <Box>
              <Heading size="xs" mb={2}>Confidence Scores</Heading>
              <Table variant="simple" size="sm">
                <Thead>
                  <Tr>
                    <Th>Class</Th>
                    <Th>Confidence</Th>
                  </Tr>
                </Thead>
                <Tbody>
                  {Object.entries(result.confidence_scores).map(([k, v]) => (
                    <Tr key={k}>
                      <Td>{k}</Td>
                      <Td>
                        <HStack>
                          <Progress value={v * 100} flex={1} />
                          <Box fontSize="sm">{(v * 100).toFixed(1)}%</Box>
                        </HStack>
                      </Td>
                    </Tr>
                  ))}
                </Tbody>
              </Table>
            </Box>
          )}

          {result.batch_id && (
            <Alert status="info" mt={4}>
              <AlertIcon />
              <Box>
                <AlertTitle>Batch Submitted</AlertTitle>
                <AlertDescription>Batch ID: {result.batch_id}</AlertDescription>
              </Box>
            </Alert>
          )}
        </CardBody>
      </Card>
    )
  }

  const renderRequestHistory = () => (
    <Box>
      {requestHistory.length === 0 ? (
        <Box p={8} textAlign="center" color="gray.500">
          No requests in history
        </Box>
      ) : (
        <Table variant="simple" size="sm">
          <Thead>
            <Tr bg="gray.100">
              <Th>Time</Th>
              <Th>Endpoint</Th>
              <Th>Mode</Th>
              <Th>Result</Th>
              <Th>Latency</Th>
            </Tr>
          </Thead>
          <Tbody>
            {requestHistory.map(req => (
              <Tr key={req.request_id} _hover={{ bg: 'gray.50' }}>
                <Td fontSize="xs">
                  {new Date(req.timestamp).toLocaleTimeString()}
                </Td>
                <Td fontSize="xs">{req.endpoint}</Td>
                <Td>
                  <Badge size="sm" colorScheme={req.mode === 'sync' ? 'blue' : 'purple'}>
                    {req.mode}
                  </Badge>
                </Td>
                <Td fontSize="xs">
                  {req.result?.prediction ? (
                    <Box color="green.600">Success</Box>
                  ) : (
                    <Box color="red.600">Failed</Box>
                  )}
                </Td>
                <Td fontSize="xs" color="gray.600">
                  {req.execution_time_ms?.toFixed(1)}ms
                </Td>
              </Tr>
            ))}
          </Tbody>
        </Table>
      )}
    </Box>
  )

  const renderTemplates = () => {
    const templates = [
      {
        name: 'High Confidence Positive',
        features: {
          feature_1: 0.9,
          feature_2: 0.8,
          feature_3: 'A',
          feature_4: 100
        }
      },
      {
        name: 'Balanced Features',
        features: {
          feature_1: 0.5,
          feature_2: 0.5,
          feature_3: 'B',
          feature_4: 50
        }
      },
      {
        name: 'Edge Case',
        features: {
          feature_1: 0.1,
          feature_2: 0.05,
          feature_3: 'C',
          feature_4: 1
        }
      }
    ]

    return (
      <VStack spacing={3} align="stretch">
        {templates.map(template => (
          <Card key={template.name} p={3}>
            <HStack justify="space-between">
              <Box>
                <Heading size="xs">{template.name}</Heading>
                <Code fontSize="xs" mt={1}>
                  {JSON.stringify(template.features)}
                </Code>
              </Box>
              <Button
                size="sm"
                colorScheme="blue"
                onClick={() => handleLoadTemplate(template)}
              >
                Load
              </Button>
            </HStack>
          </Card>
        ))}
      </VStack>
    )
  }

  return (
    <Box p={6}>
      <Heading mb={6}>Inference Request Builder</Heading>

      {/* Configuration */}
      <Card mb={6}>
        <CardBody>
          <Grid templateColumns="repeat(4, 1fr)" gap={4} mb={4}>
            <FormControl>
              <FormLabel fontSize="sm">Endpoint</FormLabel>
              <Select
                value={selectedEndpoint || ''}
                onChange={e => setSelectedEndpoint(e.target.value)}
                size="sm"
              >
                {endpoints.map(ep => (
                  <option key={ep.endpoint_id} value={ep.endpoint_id}>
                    {ep.endpoint_name}
                  </option>
                ))}
              </Select>
            </FormControl>

            <FormControl>
              <FormLabel fontSize="sm">Model Version</FormLabel>
              <Select
                value={selectedVersion || ''}
                onChange={e => setSelectedVersion(parseInt(e.target.value))}
                size="sm"
              >
                {selectedEndpoint && endpoints
                  .find(ep => ep.endpoint_id === selectedEndpoint)
                  ?.models.map(m => (
                    <option key={m.model_version} value={m.model_version}>
                      v{m.model_version}
                    </option>
                  ))}
              </Select>
            </FormControl>

            <FormControl>
              <FormLabel fontSize="sm">Request Mode</FormLabel>
              <Select
                value={requestMode}
                onChange={e => setRequestMode(e.target.value)}
                size="sm"
              >
                <option value="sync">Synchronous</option>
                <option value="async">Asynchronous</option>
              </Select>
            </FormControl>

            <FormControl>
              <FormLabel fontSize="sm">Request Type</FormLabel>
              <Select
                value={requestType}
                onChange={e => setBatchMode(e.target.value)}
                size="sm"
              >
                <option value="single">Single</option>
                <option value="batch">Batch</option>
              </Select>
            </FormControl>
          </Grid>
        </CardBody>
      </Card>

      {/* Tabs */}
      <Tabs index={activeTab} onChange={setActiveTab}>
        <TabList mb={4}>
          <Tab>{requestType === 'single' ? 'Builder' : 'Batch Builder'}</Tab>
          <Tab>Result</Tab>
          <Tab>History</Tab>
          <Tab>Templates</Tab>
        </TabList>

        <TabPanels>
          <TabPanel>
            {requestType === 'single' ? renderFeatureBuilder() : renderBatchBuilder()}
          </TabPanel>
          <TabPanel>
            {renderResult()}
          </TabPanel>
          <TabPanel>
            {renderRequestHistory()}
          </TabPanel>
          <TabPanel>
            {renderTemplates()}
          </TabPanel>
        </TabPanels>
      </Tabs>

      {/* JSON Modal */}
      <Modal isOpen={isJsonOpen} onClose={onJsonClose}>
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Load Features from JSON</ModalHeader>
          <ModalBody>
            <Textarea
              value={jsonInput}
              onChange={e => setJsonInput(e.target.value)}
              placeholder='{}'
              fontFamily="monospace"
              rows={8}
            />
          </ModalBody>
          <ModalFooter>
            <Button variant="ghost" mr={3} onClick={onJsonClose}>
              Cancel
            </Button>
            <Button colorScheme="blue" onClick={handleLoadJson}>
              Load
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  )
}

export default InferenceRequestBuilder
