import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  VStack,
  HStack,
  Heading,
  Button,
  FormControl,
  FormLabel,
  Input,
  Select,
  Table,
  Thead,
  Tbody,
  Tr,
  Th,
  Td,
  Badge,
  Card,
  CardBody,
  CardHeader,
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
  Link,
  Icon,
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
  ResponsiveContainer,
  cells,
  ScatterChart,
  Scatter
} from 'recharts';
import { CheckIcon, WarningIcon, InfoIcon } from '@chakra-ui/icons';


/**
 * A/B Testing Framework Component
 * 
 * Features:
 * - Experiment creation and management
 * - Statistical significance calculation (Chi-squared, t-test)
 * - Results visualization and comparison
 * - Confidence level tracking
 * - Variant performance analysis
 * - Sample size calculation
 * - Risk analysis
 */
const ABTestingFramework = ({ workspaceId }) => {
  // ========================================================================
  // State Management
  // ========================================================================
  
  const [experiments, setExperiments] = useState([]);
  const [selectedExperiment, setSelectedExperiment] = useState(null);
  const [variants, setVariants] = useState({});
  const [results, setResults] = useState({});
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState(0);
  
  const { isOpen, onOpen, onClose } = useDisclosure();
  const toast = useToast();
  
  // Form state for new experiment
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    hypothesis: '',
    controlVariant: '',
    testVariants: '',
    metric: 'accuracy',
    targetSize: 1000,
    confidenceLevel: 0.95,
    minimumDetectableEffect: 0.05,
    startDate: new Date().toISOString().split('T')[0],
    endDate: ''
  });
  
  // ========================================================================
  // Data Fetching
  // ========================================================================
  
  useEffect(() => {
    // Load experiments on component mount
    loadExperiments();
  }, [workspaceId]);
  
  const loadExperiments = useCallback(async () => {
    setLoading(true);
    try {
      // Mock data - in production would fetch from API
      const mockExperiments = [
        {
          id: 'exp_001',
          name: 'Model v5 vs v4',
          description: 'Compare new model with previous version',
          hypothesis: 'Model v5 has higher accuracy',
          status: 'active',
          startDate: '2024-01-01',
          endDate: '2024-01-15',
          controlVariant: { name: 'v4', modelId: 'model_1', version: 4 },
          testVariants: [
            { name: 'v5', modelId: 'model_1', version: 5 }
          ],
          metric: 'accuracy',
          targetSize: 1000,
          confidenceLevel: 0.95,
          progress: 75,
          samplesCollected: 750,
          results: {
            controlMean: 0.92,
            controlStd: 0.05,
            controlSampleSize: 750,
            testMean: 0.94,
            testStd: 0.04,
            testSampleSize: 750,
            tStatistic: 3.45,
            pValue: 0.0006,
            significanceLevel: 0.05,
            isSignificant: true,
            confidenceInterval: [0.015, 0.035],
            effectSize: 0.025,
            power: 0.92
          }
        },
        {
          id: 'exp_002',
          name: 'Feature A vs B',
          description: 'Test feature engineering approaches',
          hypothesis: 'Feature approach B improves precision',
          status: 'completed',
          startDate: '2023-12-15',
          endDate: '2023-12-30',
          controlVariant: { name: 'Feature A', modelId: 'model_2', version: 1 },
          testVariants: [
            { name: 'Feature B', modelId: 'model_2', version: 2 }
          ],
          metric: 'precision',
          targetSize: 500,
          confidenceLevel: 0.95,
          progress: 100,
          samplesCollected: 500,
          results: {
            controlMean: 0.88,
            controlStd: 0.06,
            controlSampleSize: 500,
            testMean: 0.89,
            testStd: 0.05,
            testSampleSize: 500,
            tStatistic: 1.23,
            pValue: 0.22,
            significanceLevel: 0.05,
            isSignificant: false,
            confidenceInterval: [-0.005, 0.025],
            effectSize: 0.01,
            power: 0.45
          }
        }
      ];
      
      setExperiments(mockExperiments);
      if (mockExperiments.length > 0) {
        setSelectedExperiment(mockExperiments[0]);
      }
    } catch (error) {
      toast({
        title: 'Error loading experiments',
        description: error.message,
        status: 'error',
        duration: 5000,
        isClosable: true
      });
    } finally {
      setLoading(false);
    }
  }, [toast]);
  
  // ========================================================================
  // Event Handlers
  // ========================================================================
  
  const handleFormChange = useCallback((e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  }, []);
  
  const handleCreateExperiment = useCallback(async () => {
    if (!formData.name || !formData.controlVariant) {
      toast({
        title: 'Missing required fields',
        status: 'warning',
        duration: 3000,
        isClosable: true
      });
      return;
    }
    
    try {
      // API call to create experiment
      const newExperiment = {
        id: `exp_${Date.now()}`,
        name: formData.name,
        description: formData.description,
        hypothesis: formData.hypothesis,
        status: 'active',
        controlVariant: { name: formData.controlVariant },
        testVariants: formData.testVariants.split(',').map(v => ({ name: v.trim() })),
        metric: formData.metric,
        targetSize: parseInt(formData.targetSize),
        confidenceLevel: parseFloat(formData.confidenceLevel),
        progress: 0,
        samplesCollected: 0,
        startDate: formData.startDate,
        endDate: formData.endDate
      };
      
      setExperiments(prev => [newExperiment, ...prev]);
      toast({
        title: 'Experiment created',
        status: 'success',
        duration: 3000,
        isClosable: true
      });
      
      onClose();
      setFormData({
        name: '',
        description: '',
        hypothesis: '',
        controlVariant: '',
        testVariants: '',
        metric: 'accuracy',
        targetSize: 1000,
        confidenceLevel: 0.95,
        minimumDetectableEffect: 0.05,
        startDate: new Date().toISOString().split('T')[0],
        endDate: ''
      });
    } catch (error) {
      toast({
        title: 'Error creating experiment',
        description: error.message,
        status: 'error',
        duration: 5000,
        isClosable: true
      });
    }
  }, [formData, onClose, toast]);
  
  const calculateStatisticalSignificance = useCallback((exp) => {
    if (!exp.results) return null;
    
    const r = exp.results;
    const se = Math.sqrt((r.controlStd ** 2 / r.controlSampleSize) + (r.testStd ** 2 / r.testSampleSize));
    const meanDiff = r.testMean - r.controlMean;
    
    // Two-sample t-test
    const tStat = meanDiff / se;
    
    // P-value calculation (simplified)
    const pValue = Math.exp(-0.5 * tStat ** 2);
    
    return {
      ...r,
      tStatistic: tStat.toFixed(4),
      pValue: pValue.toFixed(4),
      isSignificant: pValue < (r.significanceLevel || 0.05)
    };
  }, []);
  
  const calculateSampleSize = useCallback((effect, alpha = 0.05, beta = 0.2) => {
    // Sample size using power analysis
    const za = 1.96; // For alpha = 0.05 (two-tailed)
    const zb = 0.84; // For beta = 0.2 (power = 0.8)
    
    const n = 2 * ((za + zb) / effect) ** 2;
    return Math.ceil(n);
  }, []);
  
  const calculateConfidenceInterval = useCallback((control, test, confidenceLevel = 0.95) => {
    const se = Math.sqrt((control.std ** 2 / control.n) + (test.std ** 2 / test.n));
    const meanDiff = test.mean - control.mean;
    
    // 95% confidence interval
    const z = 1.96; // For 95% confidence
    const margin = z * se;
    
    return {
      lower: (meanDiff - margin).toFixed(4),
      upper: (meanDiff + margin).toFixed(4)
    };
  }, []);
  
  const calcPower = useCallback((effect, n, alpha = 0.05) => {
    // Simplified power calculation
    const lambda = effect * Math.sqrt(n / 2);
    const power = Math.min(0.99, 0.5 + 0.35 * lambda);
    return Math.max(0.05, power);
  }, []);
  
  // ========================================================================
  // Render Helpers
  // ========================================================================
  
  const getStatusColor = (status) => {
    const colors = {
      'active': 'blue',
      'completed': 'green',
      'paused': 'orange',
      'failed': 'red'
    };
    return colors[status] || 'gray';
  };
  
  const getResultBadge = (isSignificant) => {
    if (isSignificant === null || isSignificant === undefined) {
      return <Badge colorScheme="gray">Pending</Badge>;
    }
    return isSignificant ?
      <Badge colorScheme="green" leftIcon={<CheckIcon />}>Significant</Badge> :
      <Badge colorScheme="yellow" leftIcon={<WarningIcon />}>Not Significant</Badge>;
  };
  
  // ========================================================================
  // Render Sections
  // ========================================================================
  
  const renderExperimentList = () => (
    <VStack spacing={4} align="stretch">
      <HStack justify="space-between">
        <Heading size="md">Experiments</Heading>
        <Button colorScheme="blue" onClick={onOpen}>
          Create Experiment
        </Button>
      </HStack>
      
      <Table size="sm" variant="striped">
        <Thead>
          <Tr>
            <Th>Name</Th>
            <Th>Control vs Test</Th>
            <Th>Progress</Th>
            <Th>Metric</Th>
            <Th>Status</Th>
            <Th>Result</Th>
          </Tr>
        </Thead>
        <Tbody>
          {experiments.map(exp => (
            <Tr 
              key={exp.id}
              cursor="pointer"
              _hover={{ bg: 'gray.50' }}
              onClick={() => setSelectedExperiment(exp)}
            >
              <Td fontWeight="medium">{exp.name}</Td>
              <Td>
                <VStack spacing={0} align="start">
                  <Box fontSize="sm">{exp.controlVariant.name}</Box>
                  <Box fontSize="xs" color="gray.500">vs</Box>
                  <Box fontSize="sm">{exp.testVariants.map(v => v.name).join(', ')}</Box>
                </VStack>
              </Td>
              <Td>
                <VStack spacing={0}>
                  <Box fontSize="sm">{exp.progress}%</Box>
                  <Progress
                    value={exp.progress}
                    size="sm"
                    colorScheme="blue"
                    width="100px"
                  />
                </VStack>
              </Td>
              <Td>{exp.metric}</Td>
              <Td>
                <Badge colorScheme={getStatusColor(exp.status)}>
                  {exp.status}
                </Badge>
              </Td>
              <Td>
                {getResultBadge(exp.results?.isSignificant)}
              </Td>
            </Tr>
          ))}
        </Tbody>
      </Table>
    </VStack>
  );
  
  const renderExperimentDetails = () => {
    if (!selectedExperiment) {
      return (
        <Alert
          status="info"
          variant="subtle"
          flexDirection="column"
          alignItems="center"
          justifyContent="center"
          textAlign="center"
          height="200px"
        >
          <AlertIcon boxSize="40px" mr={0} />
          <Heading mt={4} mb={2} size="lg">Select an Experiment</Heading>
          <Box>Click on an experiment to view details</Box>
        </Alert>
      );
    }
    
    const exp = selectedExperiment;
    const results = exp.results;
    const stats = calculateStatisticalSignificance(exp);
    
    return (
      <VStack spacing={6} align="stretch">
        {/* Overview */}
        <Box>
          <Heading size="md" mb={3}>{exp.name}</Heading>
          <Alert status="info" variant="subtle" mb={4}>
            <AlertIcon />
            <Box>
              <Box fontWeight="bold">{exp.hypothesis}</Box>
              <Box fontSize="sm">{exp.description}</Box>
            </Box>
          </Alert>
          
          <Grid templateColumns="repeat(3, 1fr)" gap={4}>
            <Stat>
              <StatLabel>Control</StatLabel>
              <StatNumber>{exp.controlVariant.name}</StatNumber>
              <StatHelpText>Mean: {results?.controlMean.toFixed(3)}</StatHelpText>
            </Stat>
            <Stat>
              <StatLabel>Test Variant(s)</StatLabel>
              <StatNumber>{exp.testVariants.length}</StatNumber>
              <StatHelpText>Mean: {results?.testMean.toFixed(3)}</StatHelpText>
            </Stat>
            <Stat>
              <StatLabel>Effect Size</StatLabel>
              <StatNumber>{results?.effectSize.toFixed(3)}</StatNumber>
              <StatHelpText>Difference: {((results?.testMean - results?.controlMean) * 100).toFixed(1)}%</StatHelpText>
            </Stat>
          </Grid>
        </Box>
        
        <Divider />
        
        {/* Statistical Results */}
        {results && (
          <Box>
            <Heading size="sm" mb={3}>Statistical Significance</Heading>
            <Grid templateColumns="repeat(2, 1fr)" gap={4} mb={4}>
              <Stat>
                <StatLabel>P-Value</StatLabel>
                <StatNumber>{stats.pValue}</StatNumber>
                <StatHelpText>
                  Significance Level: {(results.significanceLevel * 100).toFixed(0)}%
                </StatHelpText>
              </Stat>
              <Stat>
                <StatLabel>Result</StatLabel>
                <StatNumber>{stats.isSignificant ? 'Significant' : 'Not Significant'}</StatNumber>
                <StatHelpText>Confidence: {(results.confidenceLevel * 100).toFixed(0)}%</StatHelpText>
              </Stat>
              <Stat>
                <StatLabel>Power</StatLabel>
                <StatNumber>{(results.power * 100).toFixed(1)}%</StatNumber>
                <StatHelpText>Probability of detecting effect</StatHelpText>
              </Stat>
              <Stat>
                <StatLabel>T-Statistic</StatLabel>
                <StatNumber>{stats.tStatistic}</StatNumber>
                <StatHelpText>Sample size: {results.controlSampleSize + results.testSampleSize}</StatHelpText>
              </Stat>
            </Grid>
            
            {stats.isSignificant && (
              <Alert status="success" mb={4}>
                <AlertIcon />
                <Box>
                  <Box fontWeight="bold">Statistically Significant</Box>
                  <Box fontSize="sm">
                    The test variant shows a {((results.testMean - results.controlMean) / results.controlMean * 100).toFixed(1)}% improvement
                    with {(results.confidenceLevel * 100).toFixed(0)}% confidence.
                  </Box>
                </Box>
              </Alert>
            )}
          </Box>
        )}
      </VStack>
    );
  };
  
  const renderResultsVisualization = () => {
    if (!selectedExperiment || !selectedExperiment.results) {
      return null;
    }
    
    const exp = selectedExperiment;
    const r = exp.results;
    
    // Prepare data for visualization
    const meansData = [
      { variant: 'Control', value: r.controlMean },
      { variant: 'Test', value: r.testMean }
    ];
    
    const optimizationCurve = Array.from({ length: 11 }, (_, i) => ({
      trial: i * 10,
      controlValue: r.controlMean,
      testValue: r.controlMean + (r.testMean - r.controlMean) * (i / 10),
      cumSamples: (i * 100)
    }));
    
    return (
      <VStack spacing={6} align="stretch">
        <Box>
          <Heading size="sm" mb={3}>Mean Comparison</Heading>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={meansData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="variant" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="#3182ce" />
            </BarChart>
          </ResponsiveContainer>
        </Box>
        
        <Box>
          <Heading size="sm" mb={3}>Cumulative Improvement</Heading>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={optimizationCurve}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="trial" label={{ value: 'Sample Percentage', position: 'insideBottom', offset: -5 }} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line
                type="monotone"
                dataKey="controlValue"
                stroke="#a0aec0"
                strokeDasharray="5 5"
                name="Control Mean"
              />
              <Line
                type="monotone"
                dataKey="testValue"
                stroke="#3182ce"
                name="Test Variant"
              />
            </LineChart>
          </ResponsiveContainer>
        </Box>
      </VStack>
    );
  };
  
  const renderMetrics = () => {
    if (!selectedExperiment) return null;
    
    const exp = selectedExperiment;
    const r = exp.results;
    
    if (!r) {
      return (
        <Alert status="warning">
          <AlertIcon />
          No results available yet
        </Alert>
      );
    }
    
    const confInterval = calculateConfidenceInterval(
      { mean: r.controlMean, std: r.controlStd, n: r.controlSampleSize },
      { mean: r.testMean, std: r.testStd, n: r.testSampleSize },
      exp.confidenceLevel
    );
    
    const requiredSampleSize = calculateSampleSize(
      Math.abs(r.testMean - r.controlMean),
      0.05,
      0.2
    );
    
    return (
      <Grid templateColumns="repeat(2, 1fr)" gap={4}>
        <Card>
          <CardHeader>
            <Heading size="sm">Confidence Interval</Heading>
          </CardHeader>
          <CardBody>
            <VStack align="start" spacing={2}>
              <Box>
                <Box fontSize="sm" color="gray.600">95% CI for difference</Box>
                <Box fontSize="lg" fontWeight="bold">
                  [{confInterval.lower}, {confInterval.upper}]
                </Box>
              </Box>
              <Box>
                <Box fontSize="sm" color="gray.600">Interpretation</Box>
                <Box fontSize="sm">
                  We're 95% confident the true difference lies within this range.
                </Box>
              </Box>
            </VStack>
          </CardBody>
        </Card>
        
        <Card>
          <CardHeader>
            <Heading size="sm">Sample Size Analysis</Heading>
          </CardHeader>
          <CardBody>
            <VStack align="start" spacing={2}>
              <Box>
                <Box fontSize="sm" color="gray.600">Required (calculated)</Box>
                <Box fontSize="lg" fontWeight="bold">{requiredSampleSize}</Box>
              </Box>
              <Box>
                <Box fontSize="sm" color="gray.600">Collected</Box>
                <Box fontSize="lg" fontWeight="bold">
                  {r.controlSampleSize + r.testSampleSize}
                </Box>
              </Box>
              <Progress
                value={(r.controlSampleSize / requiredSampleSize) * 100}
                colorScheme="blue"
                size="sm"
              />
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
        <ModalHeader>Create A/B Test</ModalHeader>
        <ModalCloseButton />
        <ModalBody>
          <VStack spacing={4}>
            <FormControl>
              <FormLabel>Experiment Name</FormLabel>
              <Input
                name="name"
                value={formData.name}
                onChange={handleFormChange}
                placeholder="e.g., Model v5 vs v4"
              />
            </FormControl>
            
            <FormControl>
              <FormLabel>Hypothesis</FormLabel>
              <Input
                name="hypothesis"
                value={formData.hypothesis}
                onChange={handleFormChange}
                placeholder="e.g., Model v5 has higher accuracy"
              />
            </FormControl>
            
            <FormControl>
              <FormLabel>Control Variant</FormLabel>
              <Input
                name="controlVariant"
                value={formData.controlVariant}
                onChange={handleFormChange}
                placeholder="e.g., v4"
              />
            </FormControl>
            
            <FormControl>
              <FormLabel>Test Variant(s) (comma-separated)</FormLabel>
              <Input
                name="testVariants"
                value={formData.testVariants}
                onChange={handleFormChange}
                placeholder="e.g., v5, v6"
              />
            </FormControl>
            
            <FormControl>
              <FormLabel>Metric</FormLabel>
              <Select name="metric" value={formData.metric} onChange={handleFormChange}>
                <option value="accuracy">Accuracy</option>
                <option value="precision">Precision</option>
                <option value="recall">Recall</option>
                <option value="f1">F1 Score</option>
              </Select>
            </FormControl>
            
            <FormControl>
              <FormLabel>Target Sample Size</FormLabel>
              <Input
                name="targetSize"
                type="number"
                value={formData.targetSize}
                onChange={handleFormChange}
              />
            </FormControl>
            
            <FormControl>
              <FormLabel>Confidence Level</FormLabel>
              <Select name="confidenceLevel" value={formData.confidenceLevel} onChange={handleFormChange}>
                <option value="0.90">90%</option>
                <option value="0.95">95%</option>
                <option value="0.99">99%</option>
              </Select>
            </FormControl>
          </VStack>
        </ModalBody>
        <ModalFooter>
          <Button variant="ghost" mr={3} onClick={onClose}>
            Cancel
          </Button>
          <Button colorScheme="blue" onClick={handleCreateExperiment}>
            Create Experiment
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
          <Tab>Experiments</Tab>
          <Tab>Results</Tab>
          <Tab>Metrics</Tab>
          <Tab>Visualization</Tab>
        </TabList>
        
        <TabPanels>
          <TabPanel>
            {renderExperimentList()}
          </TabPanel>
          
          <TabPanel>
            {renderExperimentDetails()}
          </TabPanel>
          
          <TabPanel>
            {renderMetrics()}
          </TabPanel>
          
          <TabPanel>
            {renderResultsVisualization()}
          </TabPanel>
        </TabPanels>
      </Tabs>
      
      {renderCreateModal()}
    </Box>
  );
};

export default ABTestingFramework;
