import React, { useState, useEffect, useCallback } from 'react';
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, 
         Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { AlertCircle, Activity, Server, TrendingUp, Download, RefreshCw } from 'lucide-react';

/**
 * PlatformDashboard Component
 * Comprehensive platform overview dashboard showing system health, services, and integration metrics
 * Phase 40: Final Integration & Platform Stabilization
 */

const PlatformDashboard = () => {
  const [platformMetrics, setPlatformMetrics] = useState(null);
  const [servicesHealth, setServicesHealth] = useState([]);
  const [integrationStatus, setIntegrationStatus] = useState(null);
  const [selectedTab, setSelectedTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [lastRefresh, setLastRefresh] = useState(new Date());

  // Mock data generation for demonstration
  const generateMockMetrics = useCallback(() => {
    return {
      total_services: 47,
      healthy_services: 45,
      services_with_warnings: 2,
      critical_services: 0,
      offline_services: 0,
      average_latency_ms: 52.3,
      error_rate: 0.018,
      total_requests: 2450000,
      failed_requests: 44100,
      dependency_violations: 0,
      last_updated: new Date().toISOString()
    };
  }, []);

  const generateMockServicesHealth = useCallback(() => {
    const phases = [
      { phase: 'Phase 1-5: Core', services: 8, healthy: 8, status: 'healthy' },
      { phase: 'Phase 6-15: Advanced', services: 10, healthy: 10, status: 'healthy' },
      { phase: 'Phase 16-25: Data', services: 9, healthy: 9, status: 'healthy' },
      { phase: 'Phase 26-35: Analytics', services: 8, healthy: 7, status: 'warning' },
      { phase: 'Phase 36-40: Integration', services: 12, healthy: 11, status: 'warning' }
    ];
    return phases;
  }, []);

  const generateMockIntegrationStatus = useCallback(() => {
    return {
      build_status: 'passing',
      last_build: '2026-02-09T14:32:00Z',
      test_coverage: 87.5,
      total_tests: 2847,
      passing_tests: 2824,
      failing_tests: 23,
      deployment_ready: true,
      cumulative_loc: 113550,
      total_phases_complete: 39,
      current_phase: 40
    };
  }, []);

  // Fetch dashboard data
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        // Simulate API call delay
        await new Promise(resolve => setTimeout(resolve, 300));
        
        setPlatformMetrics(generateMockMetrics());
        setServicesHealth(generateMockServicesHealth());
        setIntegrationStatus(generateMockIntegrationStatus());
        setLastRefresh(new Date());
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, [generateMockMetrics, generateMockServicesHealth, generateMockIntegrationStatus]);

  const handleRefresh = useCallback(async () => {
    setLoading(true);
    await new Promise(resolve => setTimeout(resolve, 500));
    setPlatformMetrics(generateMockMetrics());
    setServicesHealth(generateMockServicesHealth());
    setIntegrationStatus(generateMockIntegrationStatus());
    setLastRefresh(new Date());
    setLoading(false);
  }, [generateMockMetrics, generateMockServicesHealth, generateMockIntegrationStatus]);

  const handleExportData = () => {
    const exportData = {
      timestamp: lastRefresh.toISOString(),
      platform_metrics: platformMetrics,
      services_health: servicesHealth,
      integration_status: integrationStatus
    };
    
    const dataStr = JSON.stringify(exportData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `platform-dashboard-${lastRefresh.getTime()}.json`;
    link.click();
  };

  const HealthStatusBadge = ({ status }) => {
    const statusConfig = {
      healthy: { bg: 'bg-green-100', text: 'text-green-800', badge: '✓' },
      warning: { bg: 'bg-yellow-100', text: 'text-yellow-800', badge: '⚠' },
      critical: { bg: 'bg-red-100', text: 'text-red-800', badge: '✕' },
      offline: { bg: 'bg-gray-100', text: 'text-gray-800', badge: '—' }
    };
    
    const config = statusConfig[status] || statusConfig.offline;
    return (
      <span className={`px-3 py-1 rounded-full text-sm font-medium ${config.bg} ${config.text}`}>
        {config.badge} {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    );
  };

  if (loading && !platformMetrics) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-50">
        <div className="text-center">
          <RefreshCw className="mx-auto h-12 w-12 text-blue-500 animate-spin" />
          <p className="mt-4 text-lg font-medium text-gray-700">Loading Platform Dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-50 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Server className="h-8 w-8 text-blue-600" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Platform Dashboard</h1>
                <p className="text-sm text-gray-500">
                  Last updated: {lastRefresh.toLocaleTimeString()}
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={handleRefresh}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                title="Refresh data"
              >
                <RefreshCw className={`h-5 w-5 text-gray-600 ${loading ? 'animate-spin' : ''}`} />
              </button>
              <button
                onClick={handleExportData}
                className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                <Download className="h-4 w-4" />
                <span>Export</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Tabs */}
        <div className="flex space-x-4 mb-6 border-b border-gray-200">
          {['overview', 'services', 'integration', 'phases'].map(tab => (
            <button
              key={tab}
              onClick={() => setSelectedTab(tab)}
              className={`px-4 py-2 font-medium border-b-2 transition-colors ${
                selectedTab === tab
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {selectedTab === 'overview' && platformMetrics && (
          <div className="space-y-6">
            {/* Key Metrics Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-gray-500 text-sm font-medium">Total Services</p>
                    <p className="mt-2 text-3xl font-bold text-gray-900">
                      {platformMetrics.total_services}
                    </p>
                  </div>
                  <Server className="h-12 w-12 text-blue-100" />
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-gray-500 text-sm font-medium">Healthy Services</p>
                    <p className="mt-2 text-3xl font-bold text-green-600">
                      {platformMetrics.healthy_services}/{platformMetrics.total_services}
                    </p>
                  </div>
                  <Activity className="h-12 w-12 text-green-100" />
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-gray-500 text-sm font-medium">Avg Latency</p>
                    <p className="mt-2 text-3xl font-bold text-gray-900">
                      {platformMetrics.average_latency_ms.toFixed(1)}ms
                    </p>
                  </div>
                  <TrendingUp className="h-12 w-12 text-purple-100" />
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-gray-500 text-sm font-medium">Error Rate</p>
                    <p className="mt-2 text-3xl font-bold text-red-600">
                      {(platformMetrics.error_rate * 100).toFixed(2)}%
                    </p>
                  </div>
                  <AlertCircle className="h-12 w-12 text-red-100" />
                </div>
              </div>
            </div>

            {/* Requests Chart */}
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Request Metrics</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={[
                  {
                    name: 'Requests',
                    total: platformMetrics.total_requests / 1000,
                    failed: platformMetrics.failed_requests / 1000
                  }
                ]}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip formatter={(value) => `${(value * 1000).toLocaleString()}`} />
                  <Legend />
                  <Bar dataKey="total" fill="#3b82f6" name="Total Requests" />
                  <Bar dataKey="failed" fill="#ef4444" name="Failed Requests" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {selectedTab === 'services' && servicesHealth && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Services by Phase</h3>
            {servicesHealth.map((phase, idx) => (
              <div key={idx} className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <h4 className="font-semibold text-gray-900">{phase.phase}</h4>
                    <p className="text-sm text-gray-500 mt-1">
                      {phase.healthy}/{phase.services} services healthy
                    </p>
                  </div>
                  <HealthStatusBadge status={phase.status} />
                </div>
                <div className="mt-4 w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${
                      phase.status === 'healthy' ? 'bg-green-600' : 'bg-yellow-600'
                    }`}
                    style={{ width: `${(phase.healthy / phase.services) * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        )}

        {selectedTab === 'integration' && integrationStatus && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div className="bg-white rounded-lg shadow p-6">
                <p className="text-gray-500 text-sm font-medium">Build Status</p>
                <p className="mt-2 text-2xl font-bold">
                  <span className={integrationStatus.build_status === 'passing' 
                    ? 'text-green-600' : 'text-red-600'}>
                    {integrationStatus.build_status.charAt(0).toUpperCase() + 
                     integrationStatus.build_status.slice(1)}
                  </span>
                </p>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <p className="text-gray-500 text-sm font-medium">Test Coverage</p>
                <p className="mt-2 text-2xl font-bold text-blue-600">
                  {integrationStatus.test_coverage}%
                </p>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <p className="text-gray-500 text-sm font-medium">Cumulative LOC</p>
                <p className="mt-2 text-2xl font-bold text-purple-600">
                  {integrationStatus.cumulative_loc.toLocaleString()}
                </p>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <h4 className="font-semibold text-gray-900 mb-4">Test Results</h4>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={[
                      { name: 'Passing', value: integrationStatus.passing_tests },
                      { name: 'Failing', value: integrationStatus.failing_tests }
                    ]}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, value }) => `${name}: ${value}`}
                    outerRadius={100}
                  >
                    <Cell fill="#10b981" />
                    <Cell fill="#ef4444" />
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
              <p className="text-center text-sm text-gray-500 mt-4">
                {integrationStatus.passing_tests}/{integrationStatus.total_tests} tests passing
              </p>
            </div>
          </div>
        )}

        {selectedTab === 'phases' && integrationStatus && (
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Platform Phases</h3>
            {[...Array(40)].map((_, idx) => {
              const phaseNum = idx + 1;
              const isComplete = phaseNum <= integrationStatus.total_phases_complete;
              const isCurrent = phaseNum === integrationStatus.current_phase;
              
              return (
                <div
                  key={phaseNum}
                  className={`rounded-lg shadow p-4 ${
                    isComplete ? 'bg-green-50 border-l-4 border-green-600' :
                    isCurrent ? 'bg-blue-50 border-l-4 border-blue-600' :
                    'bg-white border-l-4 border-gray-300'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="font-semibold text-gray-900">Phase {phaseNum}</h4>
                      <p className="text-sm text-gray-500">
                        {isComplete && '✓ Complete'}
                        {isCurrent && '→ Current'}
                        {!isComplete && !isCurrent && '○ Pending'}
                      </p>
                    </div>
                    <span className={`text-sm font-medium ${
                      isComplete ? 'text-green-600' :
                      isCurrent ? 'text-blue-600' :
                      'text-gray-500'
                    }`}>
                      {!isComplete ? `${100 - (phaseNum - integrationStatus.total_phases_complete) * 5}%` : '100%'}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default PlatformDashboard;
