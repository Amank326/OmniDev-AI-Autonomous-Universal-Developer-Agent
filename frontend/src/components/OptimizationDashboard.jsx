import React, { useState, useEffect, useCallback } from 'react';
import {
  AreaChart, Area, BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  ScatterChart, Scatter
} from 'recharts';
import { AlertCircle, Zap, TrendingDown, Layers, CheckCircle2, Clock } from 'lucide-react';

const OptimizationDashboard = ({ workspaceId, socket }) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [expandedRec, setExpandedRec] = useState(null);
  const [forecastData, setForecastData] = useState(null);

  // Fetch resource analysis
  const fetchAnalysis = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/optimization/resources/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Workspace-ID': workspaceId,
        },
        body: JSON.stringify({
          metrics: {
            cpu_utilization_percent: 68.5,
            memory_utilization_percent: 72.1,
            bandwidth_utilization_percent: 45.3,
            disk_utilization_percent: 38.9,
          },
          allocations: {
            cpu_cores: 16,
            memory_gb: 64,
            bandwidth_mbps: 1000,
            disk_gb: 2000,
          },
        }),
      });

      if (!response.ok) throw new Error('Analysis failed');
      const data = await response.json();
      setAnalysis(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [workspaceId]);

  // Fetch capacity forecast
  const fetchForecast = useCallback(async () => {
    try {
      const response = await fetch(`/api/optimization/resources/forecast-capacity`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Workspace-ID': workspaceId,
        },
        body: JSON.stringify({
          growth_rate: 0.02,
          current_allocation: {
            cpu_cores: 16,
            memory_gb: 64,
            bandwidth_mbps: 1000,
          },
          months_ahead: 12,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        
        // Transform to chart data
        const months = ['Month 1', 'Month 3', 'Month 6', 'Month 9', 'Month 12'];
        const baseAlloc = data.forecast[Object.keys(data.forecast)[0]];
        
        const chartData = months.map((month, idx) => ({
          month,
          forecast: typeof baseAlloc === 'number' ? baseAlloc * Math.pow(1.02, (idx + 1) * 3) : 50,
          current: typeof baseAlloc === 'number' ? baseAlloc : 50,
        }));
        
        setForecastData(chartData);
      }
    } catch (err) {
      console.error('Forecast error:', err);
    }
  }, [workspaceId]);

  // Listen for WebSocket updates
  useEffect(() => {
    if (!socket) return;

    socket.on('analysis_complete', (data) => {
      if (data.workspace_id === workspaceId) {
        setAnalysis({
          ...analysis,
          current_utilization: {
            ...analysis?.current_utilization,
            ...data.utilization,
          },
          efficiency_score: data.efficiency_score,
        });
      }
    });

    return () => {
      socket.off('analysis_complete');
    };
  }, [socket, workspaceId, analysis]);

  // Load on mount
  useEffect(() => {
    fetchAnalysis();
    fetchForecast();
  }, [fetchAnalysis, fetchForecast]);

  // ==================== Overview Tab ====================
  const renderOverviewTab = () => (
    <div className="space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Overall Efficiency</p>
              <p className="text-2xl font-bold">
                {analysis?.efficiency_score ? (analysis.efficiency_score * 100).toFixed(1) : '--'}%
              </p>
            </div>
            <Zap className="w-8 h-8 text-blue-500" />
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Potential Savings</p>
              <p className="text-2xl font-bold">
                ${analysis?.total_potential_savings ? analysis.total_potential_savings.toFixed(0) : 0}
              </p>
            </div>
            <TrendingDown className="w-8 h-8 text-green-500" />
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Recommendations</p>
              <p className="text-2xl font-bold">
                {analysis?.recommendations?.length || 0}
              </p>
            </div>
            <Layers className="w-8 h-8 text-purple-500" />
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Quick Wins</p>
              <p className="text-2xl font-bold">
                {analysis?.quick_wins || 0}
              </p>
            </div>
            <CheckCircle2 className="w-8 h-8 text-emerald-500" />
          </div>
        </div>
      </div>

      {/* Utilization Gauge */}
      <div className="bg-white p-6 rounded-lg border border-gray-200">
        <h3 className="text-lg font-semibold mb-4">Current Resource Utilization</h3>
        <div className="grid grid-cols-4 gap-4">
          {analysis?.current_utilization && [
            { label: 'CPU', value: analysis.current_utilization.cpu_percent, color: 'from-blue-500' },
            { label: 'Memory', value: analysis.current_utilization.memory_percent, color: 'from-purple-500' },
            { label: 'Bandwidth', value: analysis.current_utilization.bandwidth_percent, color: 'from-orange-500' },
            { label: 'Disk', value: analysis.current_utilization.disk_percent, color: 'from-pink-500' },
          ].map((resource) => (
            <div key={resource.label} className="text-center">
              <div className={`w-24 h-24 mx-auto rounded-full bg-gradient-to-br ${resource.color} to-transparent flex items-center justify-center mb-2`}>
                <div className="text-center">
                  <div className="text-2xl font-bold text-white">{resource.value}%</div>
                </div>
              </div>
              <p className="text-sm font-medium">{resource.label}</p>
              <p className="text-xs text-gray-500">
                {resource.value > 80 ? '⚠️ High' : resource.value > 60 ? '→ Moderate' : '✓ Good'}
              </p>
            </div>
          ))}
        </div>
        {analysis?.current_utilization?.bottleneck && (
          <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded flex items-start gap-2">
            <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-yellow-800">Bottleneck Detected</p>
              <p className="text-xs text-yellow-700">{analysis.current_utilization.bottleneck} is your limiting resource</p>
            </div>
          </div>
        )}
      </div>

      {/* Efficiency Score Trend */}
      {forecastData && (
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <h3 className="text-lg font-semibold mb-4">Capacity Forecast (12 Months)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={forecastData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="current" stroke="#3b82f6" name="Current" />
              <Line type="monotone" dataKey="forecast" stroke="#ef4444" name="Forecast (2% Growth)" strokeDasharray="5 5" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );

  // ==================== Recommendations Tab ====================
  const renderRecommendationsTab = () => (
    <div className="space-y-4">
      {analysis?.recommendations?.length ? (
        analysis.recommendations.map((rec, idx) => (
          <div key={rec.recommendation_id || idx} className="bg-white border border-gray-200 rounded-lg overflow-hidden">
            <button
              onClick={() => setExpandedRec(expandedRec === idx ? null : idx)}
              className="w-full p-4 hover:bg-gray-50 flex items-center justify-between"
            >
              <div className="flex items-start gap-3 flex-1">
                <div className={`w-10 h-10 rounded flex items-center justify-center flex-shrink-0 ${
                  rec.type === 'CPU' ? 'bg-blue-100' :
                  rec.type === 'MEMORY' ? 'bg-purple-100' :
                  rec.type === 'BANDWIDTH' ? 'bg-orange-100' : 'bg-gray-100'
                }`}>
                  <Layers className="w-5 h-5" />
                </div>
                <div className="text-left flex-1">
                  <h4 className="font-semibold">{rec.type} Optimization</h4>
                  <p className="text-sm text-gray-600">{rec.description}</p>
                  <div className="flex gap-4 mt-2 text-xs">
                    <span>Current: {rec.current}</span>
                    <span>→ Recommended: {rec.recommended}</span>
                    <span className="font-semibold text-green-600">Save ${rec.estimated_savings.toFixed(2)}</span>
                  </div>
                </div>
                <div className="text-right flex-shrink-0">
                  <p className="text-lg font-bold text-green-600">{rec.savings_percentage}%</p>
                  <p className="text-xs text-gray-500">savings</p>
                </div>
              </div>
              <div className="ml-4 text-gray-400">
                {expandedRec === idx ? '▼' : '▶'}
              </div>
            </button>

            {expandedRec === idx && (
              <div className="px-4 py-4 bg-gray-50 border-t border-gray-200 space-y-3">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-xs font-medium text-gray-600 uppercase">Confidence</p>
                    <div className="flex items-center gap-2 mt-1">
                      <div className="flex-1 h-2 bg-gray-300 rounded overflow-hidden">
                        <div 
                          className="h-full bg-green-500" 
                          style={{ width: `${rec.confidence * 100}%` }}
                        />
                      </div>
                      <span className="text-sm font-semibold">{(rec.confidence * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                  <div>
                    <p className="text-xs font-medium text-gray-600 uppercase">Implementation</p>
                    <p className="text-sm font-semibold mt-1">{rec.complexity} ({rec.implementation_hours}h)</p>
                  </div>
                </div>

                <div className="pt-3 border-t border-gray-200">
                  <button className="w-full px-3 py-2 bg-blue-600 text-white rounded text-sm font-medium hover:bg-blue-700">
                    Apply Recommendation
                  </button>
                </div>
              </div>
            )}
          </div>
        ))
      ) : (
        <div className="text-center py-8 text-gray-500">
          <p>No recommendations available. Your resources are well-optimized!</p>
        </div>
      )}
    </div>
  );

  // ==================== Forecast Tab ====================
  const renderForecastTab = () => (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg border border-gray-200">
        <h3 className="text-lg font-semibold mb-4">Resource Capacity Forecast</h3>
        {forecastData ? (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={forecastData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="current" stroke="#3b82f6" strokeWidth={2} name="Current Allocation" />
              <Line type="monotone" dataKey="forecast" stroke="#ef4444" strokeDasharray="5 5" strokeWidth={2} name="Projected (2% growth)" />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-64 flex items-center justify-center text-gray-400">
            Loading forecast...
          </div>
        )}
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
          <p className="text-sm text-gray-600">Current Status</p>
          <p className="text-lg font-semibold mt-1">Healthy</p>
          <p className="text-xs text-gray-500 mt-1">✓ Resources sufficient for next 3 months</p>
        </div>
        <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-200">
          <p className="text-sm text-gray-600">3-Month Outlook</p>
          <p className="text-lg font-semibold mt-1">Monitor</p>
          <p className="text-xs text-gray-500 mt-1">→ Consider gradual scaling</p>
        </div>
        <div className="bg-orange-50 p-4 rounded-lg border border-orange-200">
          <p className="text-sm text-gray-600">12-Month Outlook</p>
          <p className="text-lg font-semibold mt-1">Plan</p>
          <p className="text-xs text-gray-500 mt-1">⚠️ Schedule scaling review</p>
        </div>
      </div>
    </div>
  );

  // ==================== History Tab ====================
  const renderHistoryTab = () => (
    <div className="bg-white p-6 rounded-lg border border-gray-200">
      <h3 className="text-lg font-semibold mb-4">Utilization History</h3>
      <div className="h-64 text-gray-400 flex items-center justify-center">
        <p>Historical data will appear here as metrics are collected</p>
      </div>
    </div>
  );

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Optimization Dashboard</h1>
            <p className="text-gray-600 mt-1">Resource utilization and cost optimization</p>
          </div>
          <button
            onClick={() => {
              fetchAnalysis();
              fetchForecast();
            }}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
            disabled={loading}
          >
            <Clock className="w-4 h-4" />
            {loading ? 'Analyzing...' : 'Refresh Analysis'}
          </button>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mx-6 mt-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold text-red-800">Error loading data</p>
            <p className="text-sm text-red-700">{error}</p>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 mb-0 px-6 mt-4 border-b border-gray-200">
        {[
          { id: 'overview', label: 'Overview', icon: '📊' },
          { id: 'recommendations', label: 'Recommendations', icon: '💡' },
          { id: 'forecast', label: 'Forecast', icon: '📈' },
          { id: 'history', label: 'History', icon: '📋' },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-3 flex items-center gap-2 font-medium text-sm border-b-2 transition ${
              activeTab === tab.id
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-600 hover:text-gray-800'
            }`}
          >
            <span>{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {activeTab === 'overview' && renderOverviewTab()}
        {activeTab === 'recommendations' && renderRecommendationsTab()}
        {activeTab === 'forecast' && renderForecastTab()}
        {activeTab === 'history' && renderHistoryTab()}
      </div>
    </div>
  );
};

export default OptimizationDashboard;
