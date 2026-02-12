import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  VStack,
  HStack,
  Heading,
  Button,
  Card,
  CardBody,
  CardHeader,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  Tabs,
  TabList,
  TabPanels,
  Tab,
  TabPanel,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalCloseButton,
  ModalFooter,
  useDisclosure,
  Alert,
  AlertIcon,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  Grid,
  GridItem,
  Progress,
  Divider,
  FormControl,
  FormLabel,
  Input,
  Select,
  Textarea,
  Spinner,
  Center,
  useToast
} from '@chakra-ui/react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts';
import { DeleteIcon, CheckIcon, CloseIcon, WarningIcon } from '@chakra-ui/icons';


/**
 * Model Training Dashboard Component
 * 
 * Features:
 * - Real-time training progress monitoring
 * - Metrics visualization (loss, accuracy, etc.)
 * - Job queue management
 * - Training logs and statistics
 * - Model checkpointing status
 * - Early stopping alerts
 * - Training history
 */
const ModelTrainingDashboard = ({ workspaceId }) => {
  // ========================================================================
  // State Management
  // ========================================================================
  
  const [trainingJobs, setTrainingJobs] = useState([]);
  const [selectedJob, setSelectedJob] = useState(null);
  const [jobDetails, setJobDetails] = useState(null);
  const [metrics, setMetrics] = useState([]);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState(0);
  const [autoRefresh, setAutoRefresh] = useState(true);
  
  const { isOpen, onOpen, onClose } = useDisclosure();
  const toast = useToast();
  
  // Form state for new training
  const [formData, setFormData] = useState({
    modelName: '',
    modelType: 'neural_network',
    datasetPath: '',
    epochs: 100,
    batchSize: 32,
    learningRate: 0.001,
    optimizer: 'adam',
    earlyStoppingPatience: 10,
    validationSplit: 0.2,
    description: ''
  });
  
  // ========================================================================
  // Data Fetching
  // ========================================================================
  
  useEffect(() => {
    loadTrainingJobs();
    
    // Setup auto-refresh
    const interval = autoRefresh ? setInterval(loadTrainingJobs, 5000) : null;
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [autoRefresh, workspaceId]);
  
  const loadTrainingJobs = useCallback(async () => {
    try {
      // Mock data - in production would fetch from API
      const mockJobs = [
        {
          id: 'train_001',
          modelName: 'ResNet_Classification_v3',
          modelType: 'neural_network',
          status: 'running',
          startTime: Date.now() - 3600000, // 1 hour ago
          currentEpoch: 45,
          totalEpochs: 100,
          progress: 45,
          bestEpoch: 42,
          bestAccuracy: 0.9542,
          bestLoss: 0.1234,
          estimatedTimeRemaining: 3600, // seconds
          checkpointsCount: 9,
          logs: [
            'Epoch 45/100 - loss: 0.1234, accuracy: 0.9542, val_loss: 0.1456, val_accuracy: 0.9487',
            'Epoch 44/100 - loss: 0.1245, accuracy: 0.9531, val_loss: 0.1467, val_accuracy: 0.9476',
            'Epoch 43/100 - loss: 0.1256, accuracy: 0.9520, val_loss: 0.1478, val_accuracy: 0.9465'
          ]
        },
        {
          id: 'train_002',
          modelName: 'XGBoost_TabularData_v2',
          modelType: 'xgboost',
          status: 'completed',
          startTime: Date.now() - 7200000, // 2 hours ago
          endTime: Date.now() - 3600000,
          currentEpoch: 100,
          totalEpochs: 100,
          progress: 100,
          bestEpoch: 95,
          bestAccuracy: 0.9623,
          bestLoss: 0.0987,
          checkpointsCount: 20,
          logs: [
            'Training completed successfully',
            'Best performance at Epoch 95: accuracy=0.9623, loss=0.0987'
          ]
        },
        {
          id: 'train_003',
          modelName: 'MLP_SmallDataset_v1',
          modelType: 'neural_network',
          status: 'paused',
          startTime: Date.now() - 10800000, // 3 hours ago
          currentEpoch: 32,
          totalEpochs: 100,
          progress: 32,
          bestEpoch: 32,
          bestAccuracy: 0.8934,
          bestLoss: 0.3456,
          estimatedTimeRemaining: 5400,
          checkpointsCount: 6
        },
        {
          id: 'train_004',
          modelName: 'LSTMSequence_TimeSeriesv1',
          modelType: 'lstm',
          status: 'failed',
          startTime: Date.now() - 14400000, // 4 hours ago
          endTime: Date.now() - 12600000,
          currentEpoch: 15,
          totalEpochs: 100,
          progress: 15,
          bestEpoch: 12,
          bestAccuracy: 0.7234,
          bestLoss: 0.6789,
          error: 'CUDA out of memory. Reduce batch size or model size.'
        }
      ];
      
      setTrainingJobs(mockJobs);
      if (mockJobs.length > 0 && !selectedJob) {
        setSelectedJob(mockJobs[0]);
        setJobDetails(mockJobs[0]);
      }
    } catch (error) {
      toast({
        title: 'Error loading training jobs',
        description: error.message,
        status: 'error',
        duration: 5000,
        isClosable: true
      });
    }
  }, [selectedJob, toast]);
  
  // Load metrics when job changes
  useEffect(() => {
    if (selectedJob) {
      loadJobMetrics();
    }
  }, [selectedJob?.id]);
  
  const loadJobMetrics = useCallback(() => {
    // Generate mock metrics data
    const mockMetrics = Array.from({ length: selectedJob.currentEpoch }, (_, i) => ({
      epoch: i + 1,
      loss: 0.5 - (i * 0.003) + Math.random() * 0.02,
      accuracy: 0.75 + (i * 0.002) + Math.random() * 0.01,
      val_loss: 0.52 - (i * 0.003) + Math.random() * 0.03,
      val_accuracy: 0.74 + (i * 0.0018) + Math.random() * 0.015
    }));
    
    setMetrics(mockMetrics);
  }, [selectedJob?.currentEpoch]);
  
  // ========================================================================
  // Event Handlers
  // ========================================================================
  
  const handleFormChange = useCallback((e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: ['epochs', 'batchSize', 'earlyStoppingPatience'].includes(name)
        ? parseInt(value)
        : ['learningRate', 'validationSplit'].includes(name)
        ? parseFloat(value)
        : value
    }));
  }, []);
  
  const handleCreateTraining = useCallback(async () => {
    if (!formData.modelName || !formData.datasetPath) {
      toast({
        title: 'Missing required fields',
        status: 'warning',
        duration: 3000,
        isClosable: true
      });
      return;
    }
    
    try {
      const newJob = {
        id: `train_${Date.now()}`,
        modelName: formData.modelName,
        modelType: formData.modelType,
        status: 'pending',
        startTime: Date.now(),
        currentEpoch: 0,
        totalEpochs: formData.epochs,
        progress: 0,
        bestEpoch: 0,
        checkpointsCount: 0,
        logs: []
      };
      
      setTrainingJobs(prev => [newJob, ...prev]);
      toast({
        title: 'Training job created',
        status: 'success',
        duration: 3000,
        isClosable: true
      });
      
      onClose();
      setFormData({
        modelName: '',
        modelType: 'neural_network',
        datasetPath: '',
        epochs: 100,
        batchSize: 32,
        learningRate: 0.001,
        optimizer: 'adam',
        earlyStoppingPatience: 10,
        validationSplit: 0.2,
        description: ''
      });
    } catch (error) {
      toast({
        title: 'Error creating training job',
        description: error.message,
        status: 'error',
        duration: 5000,
        isClosable: true
      });
    }
  }, [formData, onClose, toast]);
  
  const handleStartTraining = useCallback((jobId) => {
    setTrainingJobs(prev =>
      prev.map(job =>
        job.id === jobId
          ? { ...job, status: 'running', startTime: Date.now() }
          : job
      )
    );
    
    toast({
      title: 'Training started',
      status: 'success',
      duration: 2000,
      isClosable: true
    });
  }, [toast]);
  
  const handlePauseTraining = useCallback((jobId) => {
    setTrainingJobs(prev =>
      prev.map(job =>
        job.id === jobId ? { ...job, status: 'paused' } : job
      )
    );
    
    toast({
      title: 'Training paused',
      status: 'info',
      duration: 2000,
      isClosable: true
    });
  }, [toast]);
  
  const handleCancelTraining = useCallback((jobId) => {
    setTrainingJobs(prev =>
      prev.map(job =>
        job.id === jobId ? { ...job, status: 'cancelled' } : job
      )
    );
    
    toast({
      title: 'Training cancelled',
      status: 'warning',
      duration: 2000,
      isClosable: true
    });
  }, [toast]);
  
  const handleDeleteTraining = useCallback((jobId) => {
    setTrainingJobs(prev => prev.filter(job => job.id !== jobId));
    
    if (selectedJob?.id === jobId) {
      setSelectedJob(null);
      setJobDetails(null);
    }
    
    toast({
      title: 'Training job deleted',
      status: 'success',
      duration: 2000,
      isClosable: true
    });
  }, [selectedJob, toast]);
  
  // ========================================================================
  // Render Helpers
  // ========================================================================
  
  const getStatusColor = (status) => {
    const colors = {
      'running': 'blue',
      'completed': 'green',
      'paused': 'orange',
      'pending': 'cyan',
      'failed': 'red',
      'cancelled': 'gray'
    };
    return colors[status] || 'gray';
  };
  
  const getStatusIcon = (status) => {
    if (status === 'completed') return <CheckIcon />;
    if (status === 'failed') return <CloseIcon />;
    if (status === 'paused') return <WarningIcon />;
    return null;
  };
  
  const formatDuration = (seconds) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };
  
  const formatTime = (timestamp) => {
    return new Date(timestamp).toLocaleTimeString();
  };
  
  // ========================================================================
  // Render Sections
  // ========================================================================
  
  const renderJobsList = () => (
    <VStack spacing={4} align="stretch">
      <HStack justify="space-between">
        <Heading size="md">Training Jobs</Heading>
        <Button colorScheme="blue" onClick={onOpen}>
          Start New Training
        </Button>
      </HStack>
      
      <Table size="sm" variant="striped">
        <Thead>
          <Tr>
            <Th>Model</Th>
            <Th>Type</Th>
            <Th>Progress</Th>
            <Th>Status</Th>
            <Th>Accuracy</Th>
            <Th>Loss</Th>
            <Th>Started</Th>
            <Th>Actions</Th>
          </Tr>
        </Thead>
        <Tbody>
          {trainingJobs.map(job => (
            <Tr
              key={job.id}
              cursor="pointer"
              _hover={{ bg: 'gray.50' }}
              onClick={() => {
                setSelectedJob(job);
                setJobDetails(job);
              }}
            >
              <Td fontWeight="medium">{job.modelName}</Td>
              <Td fontSize="sm">{job.modelType}</Td>
              <Td>
                <VStack spacing={0}>
                  <Box fontSize="sm">{job.progress}%</Box>
                  <Progress
                    value={job.progress}
                    size="sm"
                    colorScheme={job.status === 'running' ? 'blue' : 'gray'}
                    width="80px"
                  />
                </VStack>
              </Td>
              <Td>
                <Badge colorScheme={getStatusColor(job.status)} leftIcon={getStatusIcon(job.status)}>
                  {job.status}
                </Badge>
              </Td>
              <Td>{job.bestAccuracy?.toFixed(4) || '-'}</Td>
              <Td>{job.bestLoss?.toFixed(4) || '-'}</Td>
              <Td fontSize="sm">{formatTime(job.startTime)}</Td>
              <Td>
                <HStack spacing={2}>
                  {job.status === 'pending' && (
                    <Button
                      size="xs"
                      colorScheme="green"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleStartTraining(job.id);
                      }}
                    >
                      Start
                    </Button>
                  )}
                  {job.status === 'running' && (
                    <Button
                      size="xs"
                      colorScheme="orange"
                      onClick={(e) => {
                        e.stopPropagation();
                        handlePauseTraining(job.id);
                      }}
                    >
                      Pause
                    </Button>
                  )}
                  {job.status === 'paused' && (
                    <Button
                      size="xs"
                      colorScheme="blue"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleStartTraining(job.id);
                      }}
                    >
                      Resume
                    </Button>
                  )}
                  {!['completed', 'failed'].includes(job.status) && (
                    <Button
                      size="xs"
                      colorScheme="red"
                      variant="ghost"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleCancelTraining(job.id);
                      }}
                    >
                      Cancel
                    </Button>
                  )}
                  <Button
                    size="xs"
                    colorScheme="red"
                    variant="ghost"
                    leftIcon={<DeleteIcon />}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteTraining(job.id);
                    }}
                  />
                </HStack>
              </Td>
            </Tr>
          ))}
        </Tbody>
      </Table>
    </VStack>
  );
  
  const renderJobDetails = () => {
    if (!jobDetails) {
      return (
        <Alert status="info" variant="subtle">
          <AlertIcon />
          Select a training job to view details
        </Alert>
      );
    }
    
    const job = jobDetails;
    const duration = job.endTime
      ? (job.endTime - job.startTime) / 1000
      : (Date.now() - job.startTime) / 1000;
    
    return (
      <VStack spacing={6} align="stretch">
        {/* Header */}
        <Box>
          <HStack justify="space-between" mb={3}>
            <Heading size="md">{job.modelName}</Heading>
            <Badge colorScheme={getStatusColor(job.status)}>
              {job.status}
            </Badge>
          </HStack>
          
          <Grid templateColumns="repeat(4, 1fr)" gap={4}>
            <Stat>
              <StatLabel>Epoch</StatLabel>
              <StatNumber>{job.currentEpoch}/{job.totalEpochs}</StatNumber>
              <StatHelpText>Best: {job.bestEpoch}</StatHelpText>
            </Stat>
            <Stat>
              <StatLabel>Accuracy</StatLabel>
              <StatNumber>{job.bestAccuracy?.toFixed(4)}</StatNumber>
              <StatHelpText>Best achieved</StatHelpText>
            </Stat>
            <Stat>
              <StatLabel>Loss</StatLabel>
              <StatNumber>{job.bestLoss?.toFixed(4)}</StatNumber>
              <StatHelpText>Current</StatHelpText>
            </Stat>
            <Stat>
              <StatLabel>Duration</StatLabel>
              <StatNumber>{formatDuration(duration)}</StatNumber>
              <StatHelpText>
                {job.estimatedTimeRemaining
                  ? `~${formatDuration(job.estimatedTimeRemaining)} remaining`
                  : 'Completed'
                }
              </StatHelpText>
            </Stat>
          </Grid>
        </Box>
        
        <Divider />
        
        {/* Progress */}
        <Box>
          <Heading size="sm" mb={2}>Training Progress</Heading>
          <Progress
            value={job.progress}
            colorScheme={job.status === 'running' ? 'blue' : job.status === 'completed' ? 'green' : 'gray'}
            size="lg"
            mb={2}
          />
          <Box fontSize="sm" color="gray.600">
            {job.progress}% complete • {job.checkpointsCount} checkpoints saved
          </Box>
        </Box>
        
        {/* Error if failed */}
        {job.status === 'failed' && job.error && (
          <Alert status="error">
            <AlertIcon />
            <Box>
              <Box fontWeight="bold">Training Failed</Box>
              <Box fontSize="sm">{job.error}</Box>
            </Box>
          </Alert>
        )}
        
        {/* Recent Logs */}
        {job.logs && job.logs.length > 0 && (
          <Box>
            <Heading size="sm" mb={2}>Recent Logs</Heading>
            <Box
              bg="gray.50"
              p={3}
              borderRadius="md"
              fontFamily="monospace"
              fontSize="xs"
              maxHeight="200px"
              overflowY="auto"
              whiteSpace="pre-wrap"
            >
              {job.logs.slice(-5).map((log, i) => (
                <Box key={i}>{log}</Box>
              ))}
            </Box>
          </Box>
        )}
      </VStack>
    );
  };
  
  const renderMetricsChart = () => {
    if (!metrics || metrics.length === 0) {
      return (
        <Alert status="info">
          <AlertIcon />
          No metrics available yet
        </Alert>
      );
    }
    
    return (
      <VStack spacing={6} align="stretch">
        <Box>
          <Heading size="sm" mb={3}>Training Metrics</Heading>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={metrics}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="epoch" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="loss"
                stroke="#f56565"
                name="Loss"
              />
              <Line
                type="monotone"
                dataKey="val_loss"
                stroke="#ed8936"
                name="Val Loss"
                strokeDasharray="5 5"
              />
            </LineChart>
          </ResponsiveContainer>
        </Box>
        
        <Box>
          <Heading size="sm" mb={3}>Accuracy Metrics</Heading>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={metrics}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="epoch" />
              <YAxis domain={[0.7, 1]} />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="accuracy"
                stroke="#48bb78"
                name="Accuracy"
              />
              <Line
                type="monotone"
                dataKey="val_accuracy"
                stroke="#38a169"
                name="Val Accuracy"
                strokeDasharray="5 5"
              />
            </LineChart>
          </ResponsiveContainer>
        </Box>
      </VStack>
    );
  };
  
  const renderQueueStatus = () => {
    const pendingJobs = trainingJobs.filter(j => j.status === 'pending');
    const runningJobs = trainingJobs.filter(j => j.status === 'running');
    const completedJobs = trainingJobs.filter(j => j.status === 'completed');
    
    return (
      <Grid templateColumns="repeat(2, 1fr)" gap={4}>
        <Card>
          <CardHeader>
            <Heading size="sm">Queue Status</Heading>
          </CardHeader>
          <CardBody>
            <VStack align="start" spacing={3}>
              <Stat>
                <StatLabel>Active Jobs</StatLabel>
                <StatNumber>{runningJobs.length}</StatNumber>
              </Stat>
              <Stat>
                <StatLabel>Queued Jobs</StatLabel>
                <StatNumber>{pendingJobs.length}</StatNumber>
              </Stat>
              <Stat>
                <StatLabel>Completed</StatLabel>
                <StatNumber>{completedJobs.length}</StatNumber>
              </Stat>
            </VStack>
          </CardBody>
        </Card>
        
        <Card>
          <CardHeader>
            <Heading size="sm">System Status</Heading>
          </CardHeader>
          <CardBody>
            <VStack align="start" spacing={3}>
              <HStack>
                <Box
                  width="12px"
                  height="12px"
                  borderRadius="full"
                  bg="green.400"
                />
                <Box>All services healthy</Box>
              </HStack>
              <HStack>
                <Box
                  width="12px"
                  height="12px"
                  borderRadius="full"
                  bg="blue.400"
                />
                <Box>Auto-refresh enabled</Box>
              </HStack>
              <Button
                size="sm"
                variant={autoRefresh ? 'solid' : 'outline'}
                colorScheme="blue"
                onClick={() => setAutoRefresh(!autoRefresh)}
              >
                {autoRefresh ? 'Disable' : 'Enable'} Auto-Refresh
              </Button>
            </VStack>
          </CardBody>
        </Card>
      </Grid>
    );
  };
  
  const renderCreateModal = () => (
    <Modal isOpen={isOpen} onClose={onClose} size="lg">
      <ModalOverlay />
      <ModalContent>
        <ModalHeader>Start New Training</ModalHeader>
        <ModalCloseButton />
        <ModalBody>
          <VStack spacing={4}>
            <FormControl isRequired>
              <FormLabel>Model Name</FormLabel>
              <Input
                name="modelName"
                value={formData.modelName}
                onChange={handleFormChange}
                placeholder="e.g., ResNet_Classification_v3"
              />
            </FormControl>
            
            <FormControl isRequired>
              <FormLabel>Model Type</FormLabel>
              <Select name="modelType" value={formData.modelType} onChange={handleFormChange}>
                <option value="neural_network">Neural Network</option>
                <option value="xgboost">XGBoost</option>
                <option value="lstm">LSTM</option>
                <option value="transformer">Transformer</option>
              </Select>
            </FormControl>
            
            <FormControl isRequired>
              <FormLabel>Dataset Path</FormLabel>
              <Input
                name="datasetPath"
                value={formData.datasetPath}
                onChange={handleFormChange}
                placeholder="s3://bucket/dataset"
              />
            </FormControl>
            
            <FormControl>
              <FormLabel>Epochs</FormLabel>
              <Input
                name="epochs"
                type="number"
                value={formData.epochs}
                onChange={handleFormChange}
              />
            </FormControl>
            
            <FormControl>
              <FormLabel>Batch Size</FormLabel>
              <Input
                name="batchSize"
                type="number"
                value={formData.batchSize}
                onChange={handleFormChange}
              />
            </FormControl>
            
            <FormControl>
              <FormLabel>Learning Rate</FormLabel>
              <Input
                name="learningRate"
                type="number"
                step="0.0001"
                value={formData.learningRate}
                onChange={handleFormChange}
              />
            </FormControl>
            
            <FormControl>
              <FormLabel>Description</FormLabel>
              <Textarea
                name="description"
                value={formData.description}
                onChange={handleFormChange}
                placeholder="Optional notes"
              />
            </FormControl>
          </VStack>
        </ModalBody>
        <ModalFooter>
          <Button variant="ghost" mr={3} onClick={onClose}>
            Cancel
          </Button>
          <Button colorScheme="blue" onClick={handleCreateTraining}>
            Start Training
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
  
  // ========================================================================
  // Main Render
  // ========================================================================
  
  return (
    <Box p={6} bg="white" borderRadius="lg">
      <Tabs index={activeTab} onChange={setActiveTab}>
        <TabList mb="1em">
          <Tab>Jobs</Tab>
          <Tab>Details</Tab>
          <Tab>Metrics</Tab>
          <Tab>Queue</Tab>
        </TabList>
        
        <TabPanels>
          <TabPanel>
            {renderJobsList()}
          </TabPanel>
          
          <TabPanel>
            {renderJobDetails()}
          </TabPanel>
          
          <TabPanel>
            {renderMetricsChart()}
          </TabPanel>
          
          <TabPanel>
            {renderQueueStatus()}
          </TabPanel>
        </TabPanels>
      </Tabs>
      
      {renderCreateModal()}
    </Box>
  );
};

export default ModelTrainingDashboard;
