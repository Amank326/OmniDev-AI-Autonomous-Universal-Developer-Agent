import React, { useState, useEffect, useCallback } from 'react';
import { AlertTriangle, CheckCircle, Clock, Zap, Database, Shield, TrendingDown, TrendingUp } from 'lucide-react';

/**
 * IntegrationHealthMonitor Component
 * Real-time monitoring of platform integration health across all phases and services
 * Phase 40: Final Integration & Platform Stabilization
 */

const IntegrationHealthMonitor = () => {
  const [healthData, setHealthData] = useState(null);
  const [selectedService, setSelectedService] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [timeRange, setTimeRange] = useState('1h');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [loading, setLoading] = useState(true);

  // Mock health data generation
  const generateMockHealthData = useCallback(() => {
    return {
      overall_status: 'healthy',
      uptime_percent: 99.98,
      last_incident: '2 days ago',
      services: [
        {
          name: 'Authentication Service',
          phase: 'Phase 1-5',
          status: 'healthy',
          latency_ms: 23.5,
          error_rate: 0.001,
          last_check: Date.now() - 5000,
          memory_mb: 245,
          cpu_percent: 12.3,
          requests_per_second: 1250
        },
        {
          name: 'Cache Manager',
          phase: 'Phase 39',
          status: 'healthy',
          latency_ms: 2.1,
          error_rate: 0.0,
          last_check: Date.now() - 5000,
          memory_mb: 512,
          cpu_percent: 5.1,
          requests_per_second: 25000
        },
        {
          name: 'Security Service',
          phase: 'Phase 39',
          status: 'healthy',
          latency_ms: 34.2,
          error_rate: 0.002,
          last_check: Date.now() - 5000,
          memory_mb: 189,
          cpu_percent: 8.7,
          requests_per_second: 2100
        },
        {
          name: 'Performance Optimizer',
          phase: 'Phase 39',
          status: 'warning',
          latency_ms: 156.8,
          error_rate: 0.015,
          last_check: Date.now() - 5000,
          memory_mb: 428,
          cpu_percent: 34.2,
          requests_per_second: 500
        },
        {
          name: 'Analytics Service',
          phase: 'Phase 26-35',
          status: 'healthy',
          latency_ms: 87.3,
          error_rate: 0.003,
          last_check: Date.now() - 5000,
          memory_mb: 650,
          cpu_percent: 18.5,
          requests_per_second: 800
        },
        {
          name: 'Data Integration',
          phase: 'Phase 16-25',
          status: 'healthy',
          latency_ms: 145.6,
          error_rate: 0.004,
          last_check: Date.now() - 5000,
          memory_mb: 890,
          cpu_percent: 22.1,
          requests_per_second: 450
        }
      ],
      alerts: [
        {
          id: 'alert_1',
          severity: 'warning',
          service: 'Performance Optimizer',
          message: 'High CPU utilization detected (34.2%)',
          timestamp: Date.now() - 300000,
          resolved: false
        },
        {
          id: 'alert_2',
          severity: 'info',
          service: 'Cache Manager',
          message: 'Cache hit ratio optimal (87.3%)',
          timestamp: Date.now() - 600000,
          resolved: false
        }
      ],
      dependency_issues: [
        {
          service: 'API Gateway',
          dependency: 'Authentication Service',
          status: 'satisfied',
          version: '1.5.0 (required: ^1.0.0)'
        },
        {
          service: 'Performance Optimizer',
          dependency: 'Cache Manager',
          status: 'satisfied',
          version: '1.0.0 (required: ^1.0.0)'
        }
      ]
    };
  }, []);

  // Load health data
  useEffect(() => {
    const loadHealth = async () => {
      setLoading(true);
      await new Promise(resolve => setTimeout(resolve, 400));
      const data = generateMockHealthData();
      setHealthData(data);
      setAlerts(data.alerts);
      if (!selectedService && data.services.length > 0) {
        setSelectedService(data.services[0]);
      }
      setLoading(false);
    };

    loadHealth();

    if (autoRefresh) {
      const interval = setInterval(loadHealth, 10000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, generateMockHealthData]);

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy':
        return { bg: 'bg-green-100', text: 'text-green-800', icon: CheckCircle };
      case 'warning':
        return { bg: 'bg-yellow-100', text: 'text-yellow-800', icon: AlertTriangle };
      case 'critical':
        return { bg: 'bg-red-100', text: 'text-red-800', icon: AlertTriangle };
      default:
        return { bg: 'bg-gray-100', text: 'text-gray-800', icon: Clock };
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-50 border-l-4 border-red-600';
      case 'warning':
        return 'bg-yellow-50 border-l-4 border-yellow-600';
      case 'info':
        return 'bg-blue-50 border-l-4 border-blue-600';
      default:
        return 'bg-gray-50 border-l-4 border-gray-300';
    }
  };

  const handleDismissAlert = (alertId) => {
    setAlerts(alerts.filter(a => a.id !== alertId));
  };

  if (loading || !healthData) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="mb-4 flex justify-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
          <p className="text-gray-600">Loading integration health data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 p-6">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <Zap className="h-8 w-8 text-blue-600" />
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Integration Health Monitor</h1>
              <p className="text-gray-600 text-sm">Real-time platform service health tracking</p>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="px-3 py-2 bg-white border border-gray-300 rounded-lg text-sm"
            >
              <option value="1h">Last 1 hour</option>
              <option value="24h">Last 24 hours</option>
              <option value="7d">Last 7 days</option>
            </select>
            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="form-checkbox h-4 w-4 text-blue-600"
              />
              <span className="text-sm text-gray-700">Auto refresh</span>
            </label>
          </div>
        </div>

        {/* Overall Status */}
        <div className="bg-white rounded-lg shadow p-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <p className="text-gray-600 text-sm font-medium">Overall Status</p>
              <div className="mt-2 flex items-center space-x-2">
                <CheckCircle className="h-6 w-6 text-green-600" />
                <p className="text-2xl font-bold text-gray-900 capitalize">
                  {healthData.overall_status}
                </p>
              </div>
            </div>
            <div>
              <p className="text-gray-600 text-sm font-medium">Uptime</p>
              <p className="mt-2 text-2xl font-bold text-green-600">{healthData.uptime_percent}%</p>
            </div>
            <div>
              <p className="text-gray-600 text-sm font-medium">Services Up</p>
              <p className="mt-2 text-2xl font-bold text-gray-900">
                {healthData.services.filter(s => s.status === 'healthy').length}/
                {healthData.services.length}
              </p>
            </div>
            <div>
              <p className="text-gray-600 text-sm font-medium">Last Incident</p>
              <p className="mt-2 text-lg font-semibold text-gray-900">{healthData.last_incident}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Alerts */}
      {alerts.length > 0 && (
        <div className="mb-8 space-y-3">
          <h3 className="text-lg font-semibold text-gray-900">Active Alerts ({alerts.length})</h3>
          {alerts.map(alert => (
            <div
              key={alert.id}
              className={`rounded-lg p-4 flex items-center justify-between ${getSeverityColor(
                alert.severity
              )}`}
            >
              <div className="flex-1">
                <p className="font-semibold text-gray-900">{alert.message}</p>
                <p className="text-sm text-gray-600 mt-1">
                  Service: {alert.service} • {new Date(alert.timestamp).toLocaleString()}
                </p>
              </div>
              <button
                onClick={() => handleDismissAlert(alert.id)}
                className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-200 rounded"
              >
                Dismiss
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Services Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* Services List */}
        <div className="lg:col-span-1">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Services</h3>
          <div className="space-y-2">
            {healthData.services.map((service, idx) => {
              const colors = getStatusColor(service.status);
              const isSelected = selectedService?.name === service.name;
              const Icon = colors.icon;

              return (
                <button
                  key={idx}
                  onClick={() => setSelectedService(service)}
                  className={`w-full text-left p-4 rounded-lg border-2 transition-all ${
                    isSelected
                      ? 'border-blue-600 bg-blue-50'
                      : `border-transparent ${colors.bg} hover:border-gray-300`
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <p className="font-medium text-gray-900">{service.name}</p>
                      <p className="text-xs text-gray-600 mt-1">{service.phase}</p>
                    </div>
                    <Icon className={`h-5 w-5 ${colors.text}`} />
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Service Details */}
        {selectedService && (
          <div className="lg:col-span-2 space-y-4">
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-2xl font-bold">{selectedService.name}</h3>
                    <p className="mt-1 opacity-90">{selectedService.phase}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm opacity-90">Status</p>
                    <p className="text-xl font-bold capitalize">{selectedService.status}</p>
                  </div>
                </div>
              </div>

              <div className="p-6 space-y-6">
                {/* Key Metrics */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-gray-600 text-sm font-medium">Latency</p>
                    <p className="mt-1 text-2xl font-bold text-gray-900">
                      {selectedService.latency_ms.toFixed(1)}ms
                    </p>
                  </div>
                  <div>
                    <p className="text-gray-600 text-sm font-medium">Error Rate</p>
                    <p className="mt-1 text-2xl font-bold text-gray-900">
                      {(selectedService.error_rate * 100).toFixed(3)}%
                    </p>
                  </div>
                  <div>
                    <p className="text-gray-600 text-sm font-medium">Memory</p>
                    <p className="mt-1 text-2xl font-bold text-gray-900">
                      {selectedService.memory_mb}MB
                    </p>
                  </div>
                  <div>
                    <p className="text-gray-600 text-sm font-medium">CPU</p>
                    <p className="mt-1 text-2xl font-bold text-gray-900">
                      {selectedService.cpu_percent.toFixed(1)}%
                    </p>
                  </div>
                </div>

                {/* Throughput */}
                <div>
                  <p className="text-gray-600 text-sm font-medium mb-2">Requests per Second</p>
                  <div className="flex items-center space-x-2">
                    <Zap className="h-5 w-5 text-yellow-600" />
                    <p className="text-xl font-semibold text-gray-900">
                      {selectedService.requests_per_second.toLocaleString()} req/s
                    </p>
                  </div>
                </div>

                {/* Health Indicators */}
                <div className="pt-4 border-t border-gray-200">
                  <p className="text-gray-600 text-sm font-medium mb-3">Health Indicators</p>
                  <div className="space-y-2">
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-gray-700">Latency Health</span>
                        <span className={selectedService.latency_ms < 100 ? 'text-green-600' : 'text-yellow-600'}>
                          {selectedService.latency_ms < 100 ? 'Excellent' : 'Good'}
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${selectedService.latency_ms < 100 ? 'bg-green-600' : 'bg-yellow-600'}`}
                          style={{ width: `${Math.min((selectedService.latency_ms / 200) * 100, 100)}%` }}
                        />
                      </div>
                    </div>
                    <div>
                      <div className="flex justify-between text-sm mb-1">
                        <span className="text-gray-700">Reliability</span>
                        <span className={selectedService.error_rate < 0.01 ? 'text-green-600' : 'text-yellow-600'}>
                          {((1 - selectedService.error_rate) * 100).toFixed(2)}%
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className={`h-2 rounded-full ${selectedService.error_rate < 0.01 ? 'bg-green-600' : 'bg-yellow-600'}`}
                          style={{ width: `${(1 - selectedService.error_rate) * 100}%` }}
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Dependency Status */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900 flex items-center space-x-2">
            <Database className="h-5 w-5" />
            <span>Dependency Status</span>
          </h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Service</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Dependency</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Status</th>
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Version</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {healthData.dependency_issues.map((dep, idx) => (
                <tr key={idx} className="hover:bg-gray-50">
                  <td className="px-6 py-4 text-sm text-gray-900">{dep.service}</td>
                  <td className="px-6 py-4 text-sm text-gray-600">{dep.dependency}</td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex items-center space-x-1 px-3 py-1 rounded-full text-sm font-medium ${
                      dep.status === 'satisfied'
                        ? 'bg-green-100 text-green-800'
                        : 'bg-red-100 text-red-800'
                    }`}>
                      <span>{dep.status === 'satisfied' ? '✓' : '✕'}</span>
                      <span className="capitalize">{dep.status}</span>
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600 font-mono">{dep.version}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default IntegrationHealthMonitor;
