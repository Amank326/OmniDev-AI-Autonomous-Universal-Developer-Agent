/**
 * Deployment Status Dashboard Component
 * Real-time monitoring of deployments, rollouts, and health status
 * Phase 41: CI/CD Pipeline & Automated Deployment
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Grid,
  LinearProgress,
  Typography,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  Stepper,
  Step,
  StepLabel,
  IconButton,
  Tooltip,
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Settings as SettingsIcon,
  Refresh as RefreshIcon,
  GetApp as RollbackIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as ChartTooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

// Status enums
const DeploymentStatus = {
  PENDING: 'pending',
  IN_PROGRESS: 'in_progress',
  COMPLETED: 'completed',
  FAILED: 'failed',
  ROLLED_BACK: 'rolled_back',
  PAUSED: 'paused',
};

const HealthStatus = {
  HEALTHY: 'healthy',
  DEGRADED: 'degraded',
  UNHEALTHY: 'unhealthy',
  UNKNOWN: 'unknown',
};

const DeploymentStrategy = {
  BLUE_GREEN: 'blue_green',
  CANARY: 'canary',
  ROLLING: 'rolling',
  SHADOW: 'shadow',
};

// Status color mapping
const getStatusColor = (status) => {
  switch (status) {
    case DeploymentStatus.COMPLETED:
    case HealthStatus.HEALTHY:
      return '#4caf50'; // green
    case DeploymentStatus.IN_PROGRESS:
      return '#2196f3'; // blue
    case DeploymentStatus.PAUSED:
      return '#ff9800'; // orange
    case DeploymentStatus.FAILED:
    case HealthStatus.UNHEALTHY:
      return '#f44336'; // red
    case HealthStatus.DEGRADED:
      return '#ff9800'; // orange
    default:
      return '#9e9e9e'; // grey
  }
};

const getStatusIcon = (status) => {
  switch (status) {
    case DeploymentStatus.COMPLETED:
    case HealthStatus.HEALTHY:
      return <CheckCircleIcon style={{ color: getStatusColor(status) }} />;
    case DeploymentStatus.FAILED:
    case HealthStatus.UNHEALTHY:
      return <ErrorIcon style={{ color: getStatusColor(status) }} />;
    case DeploymentStatus.PAUSED:
    case HealthStatus.DEGRADED:
      return <WarningIcon style={{ color: getStatusColor(status) }} />;
    default:
      return <InfoIcon />;
  }
};

/**
 * Individual Deployment Card Component
 */
const DeploymentCard = ({ deployment, onRefresh, onRollback }) => {
  const [expanded, setExpanded] = useState(false);
  const [showDetails, setShowDetails] = useState(false);

  const getStrategyLabel = (strategy) => {
    return strategy.split('_').map((s) => s.charAt(0).toUpperCase() + s.slice(1)).join('-');
  };

  const deploymentSteps = ['Validation', 'Deployment', 'Health Check', 'Smoke Tests', 'Complete'];
  const currentStep = {
    [DeploymentStatus.PENDING]: 0,
    [DeploymentStatus.IN_PROGRESS]: 2,
    [DeploymentStatus.COMPLETED]: 4,
    [DeploymentStatus.FAILED]: -1,
    [DeploymentStatus.ROLLED_BACK]: 0,
  }[deployment.status] || 0;

  return (
    <Card style={{ marginBottom: '16px' }}>
      <CardHeader
        title={deployment.config?.service_name || 'Unknown Service'}
        subheader={`v${deployment.config?.version || 'unknown'}`}
        action={
          <Box display="flex" gap={1}>
            <Tooltip title="Refresh">
              <IconButton size="small" onClick={() => onRefresh(deployment.deployment_id)}>
                <RefreshIcon />
              </IconButton>
            </Tooltip>
            {deployment.status !== DeploymentStatus.COMPLETED && (
              <Tooltip title="Rollback">
                <IconButton size="small" onClick={() => onRollback(deployment.deployment_id)}>
                  <RollbackIcon />
                </IconButton>
              </Tooltip>
            )}
          </Box>
        }
        style={{ background: getStatusColor(deployment.status) + '22' }}
      />
      <CardContent>
        {/* Status Bar */}
        <Box display="flex" alignItems="center" gap={2} marginBottom={2}>
          {getStatusIcon(deployment.status)}
          <Chip
            label={deployment.status.toUpperCase().replace(/_/g, ' ')}
            style={{ background: getStatusColor(deployment.status), color: 'white' }}
          />
          <Typography variant="body2" color="textSecondary">
            Duration: {deployment.deployment_duration_seconds?.toFixed(1) || '0'} seconds
          </Typography>
        </Box>

        {/* Deployment Strategy and Environment */}
        <Box display="flex" gap={2} marginBottom={2}>
          <Chip
            label={getStrategyLabel(deployment.config?.strategy || 'unknown')}
            variant="outlined"
            size="small"
          />
          <Chip
            label={deployment.config?.environment || 'unknown'}
            color={['staging', 'production'].includes(deployment.config?.environment) ? 'primary' : 'default'}
            variant="outlined"
            size="small"
          />
        </Box>

        {/* Instance Status */}
        {deployment.deployed_instances && deployment.deployed_instances.length > 0 && (
          <Box marginBottom={2}>
            <Typography variant="subtitle2" gutterBottom>
              Instances ({deployment.deployed_instances.length})
            </Typography>
            <Box display="flex" gap={1} flexWrap="wrap">
              {deployment.deployed_instances.map((instance, idx) => (
                <Chip
                  key={idx}
                  label={instance.instance_id}
                  size="small"
                  style={{
                    background: getStatusColor(instance.status),
                    color: 'white',
                  }}
                />
              ))}
            </Box>
          </Box>
        )}

        {/* Progress Stepper */}
        {deployment.status === DeploymentStatus.IN_PROGRESS && (
          <Box marginBottom={2}>
            <Stepper activeStep={currentStep}>
              {deploymentSteps.map((label) => (
                <Step key={label}>
                  <StepLabel>{label}</StepLabel>
                </Step>
              ))}
            </Stepper>
          </Box>
        )}

        {/* Error Message */}
        {deployment.error_message && (
          <Alert severity="error" style={{ marginBottom: '16px' }}>
            {deployment.error_message}
          </Alert>
        )}

        {/* Details Button */}
        <Button size="small" onClick={() => setShowDetails(true)}>
          View Details
        </Button>

        {/* Details Dialog */}
        <Dialog open={showDetails} onClose={() => setShowDetails(false)} maxWidth="sm" fullWidth>
          <DialogTitle>Deployment Details</DialogTitle>
          <DialogContent>
            <Box padding={2}>
              <Typography variant="subtitle2">Deployment ID</Typography>
              <Typography variant="body2" paragraph>
                {deployment.deployment_id}
              </Typography>

              <Typography variant="subtitle2">Configuration</Typography>
              <Typography variant="body2" component="div" paragraph>
                <pre style={{ fontSize: '12px', overflow: 'auto' }}>
                  {JSON.stringify(deployment.config, null, 2)}
                </pre>
              </Typography>

              <Typography variant="subtitle2">Timeline</Typography>
              <Typography variant="body2">
                Started: {deployment.started_at}
              </Typography>
              <Typography variant="body2">
                Completed: {deployment.completed_at || 'In Progress'}
              </Typography>
            </Box>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setShowDetails(false)}>Close</Button>
          </DialogActions>
        </Dialog>
      </CardContent>
    </Card>
  );
};

/**
 * Main Deployment Status Dashboard Component
 */
const DeploymentStatusDashboard = () => {
  const [deployments, setDeployments] = useState([]);
  const [healthMetrics, setHealthMetrics] = useState([]);
  const [statistics, setStatistics] = useState({
    totalDeployments: 0,
    successRate: 0,
    avgDuration: 0,
    activeDeployments: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedEnvironment, setSelectedEnvironment] = useState('all');

  // Fetch deployment data
  const fetchDeployments = useCallback(async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/v1/deployments/status');
      if (!response.ok) throw new Error('Failed to fetch deployments');
      const data = await response.json();
      setDeployments(data.deployments || []);
      setStatistics(data.statistics || {});
      setError(null);
    } catch (err) {
      setError(err.message);
      console.error('Error fetching deployments:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch health metrics
  const fetchHealthMetrics = useCallback(async () => {
    try {
      const response = await fetch('/api/v1/deployments/health');
      if (!response.ok) throw new Error('Failed to fetch health metrics');
      const data = await response.json();
      setHealthMetrics(data.metrics || []);
    } catch (err) {
      console.error('Error fetching health metrics:', err);
    }
  }, []);

  // Refresh deployment
  const handleRefresh = useCallback(async (deploymentId) => {
    try {
      const response = await fetch(`/api/v1/deployments/${deploymentId}/refresh`, {
        method: 'POST',
      });
      if (response.ok) {
        fetchDeployments();
      }
    } catch (err) {
      console.error('Error refreshing deployment:', err);
    }
  }, [fetchDeployments]);

  // Rollback deployment
  const handleRollback = useCallback(async (deploymentId) => {
    if (window.confirm('Are you sure you want to rollback this deployment?')) {
      try {
        const response = await fetch(`/api/v1/deployments/${deploymentId}/rollback`, {
          method: 'POST',
        });
        if (response.ok) {
          fetchDeployments();
        }
      } catch (err) {
        console.error('Error rolling back deployment:', err);
      }
    }
  }, [fetchDeployments]);

  // Initial load and polling
  useEffect(() => {
    fetchDeployments();
    fetchHealthMetrics();

    const interval = setInterval(() => {
      fetchDeployments();
      fetchHealthMetrics();
    }, 30000); // Poll every 30 seconds

    return () => clearInterval(interval);
  }, [fetchDeployments, fetchHealthMetrics]);

  // Filter deployments by environment
  const filteredDeployments =
    selectedEnvironment === 'all'
      ? deployments
      : deployments.filter((d) => d.config?.environment === selectedEnvironment);

  // Prepare health metrics chart data
  const healthChartData =
    healthMetrics.length > 0
      ? healthMetrics.map((m) => ({
          name: m.name,
          healthy: m.healthy_count,
          degraded: m.degraded_count,
          unhealthy: m.unhealthy_count,
        }))
      : [];

  // Prepare status distribution pie data
  const statusDistribution = [
    {
      name: 'Completed',
      value: deployments.filter((d) => d.status === DeploymentStatus.COMPLETED).length,
    },
    {
      name: 'In Progress',
      value: deployments.filter((d) => d.status === DeploymentStatus.IN_PROGRESS).length,
    },
    {
      name: 'Failed',
      value: deployments.filter((d) => d.status === DeploymentStatus.FAILED).length,
    },
  ];

  const COLORS = ['#4caf50', '#2196f3', '#f44336'];

  return (
    <Box padding={3}>
      {/* Header */}
      <Box marginBottom={3}>
        <Typography variant="h4" gutterBottom>
          🚀 Deployment Status Dashboard
        </Typography>
        <Typography variant="body1" color="textSecondary">
          Real-time monitoring of deployments across environments
        </Typography>
      </Box>

      {/* Error Alert */}
      {error && <Alert severity="error" style={{ marginBottom: '16px' }}>{error}</Alert>}

      {/* Statistics Cards */}
      <Grid container spacing={2} marginBottom={3}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Deployments
              </Typography>
              <Typography variant="h5">{statistics.totalDeployments || 0}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Success Rate
              </Typography>
              <Typography variant="h5">{(statistics.successRate || 0).toFixed(1)}%</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Active Deployments
              </Typography>
              <Typography variant="h5" style={{ color: '#2196f3' }}>
                {statistics.activeDeployments || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Avg Duration
              </Typography>
              <Typography variant="h5">{(statistics.avgDuration || 0).toFixed(1)}s</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Status Distribution and Health Chart */}
      <Grid container spacing={2} marginBottom={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader title="Deployment Status Distribution" />
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={statusDistribution}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, value }) => `${name}: ${value}`}
                    outerRadius={100}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {statusDistribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <ChartTooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardHeader title="Instance Health Status" />
            <CardContent>
              {healthChartData.length > 0 ? (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={healthChartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <ChartTooltip />
                    <Legend />
                    <Bar dataKey="healthy" fill="#4caf50" />
                    <Bar dataKey="degraded" fill="#ff9800" />
                    <Bar dataKey="unhealthy" fill="#f44336" />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <Typography color="textSecondary">No health data available</Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Deployments List */}
      <Card>
        <CardHeader
          title="Recent Deployments"
          action={
            <Box display="flex" gap={1}>
              <select
                value={selectedEnvironment}
                onChange={(e) => setSelectedEnvironment(e.target.value)}
                style={{ padding: '8px', borderRadius: '4px', border: '1px solid #ddd' }}
              >
                <option value="all">All Environments</option>
                <option value="staging">Staging</option>
                <option value="production">Production</option>
              </select>
              <Tooltip title="Refresh">
                <IconButton onClick={fetchDeployments} size="small">
                  <RefreshIcon />
                </IconButton>
              </Tooltip>
            </Box>
          }
        />
        <CardContent>
          {loading ? (
            <Box padding={3} textAlign="center">
              <LinearProgress />
              <Typography variant="body2" marginTop={2}>
                Loading deployment data...
              </Typography>
            </Box>
          ) : filteredDeployments.length > 0 ? (
            filteredDeployments.map((deployment) => (
              <DeploymentCard
                key={deployment.deployment_id}
                deployment={deployment}
                onRefresh={handleRefresh}
                onRollback={handleRollback}
              />
            ))
          ) : (
            <Typography variant="body2" color="textSecondary" align="center" padding={3}>
              No deployments found
            </Typography>
          )}
        </CardContent>
      </Card>
    </Box>
  );
};

export default DeploymentStatusDashboard;
