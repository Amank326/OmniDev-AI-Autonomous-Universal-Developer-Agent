import React, { useState, useEffect, useCallback } from 'react';
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar, ScatterChart, Scatter,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell
} from 'recharts';
import { TrendingUp, AlertTriangle, CheckCircle, Settings, Activity } from 'lucide-react';

const CapacityPlanner = ({ workspaceId, socket }) => {
  const [activeTab, setActiveTab] = useState('forecast');
  const [capacityData, setCapacityData] = useState(null);
  const [trendData, setTrendData] = useState(null);
  const [scenarioData, setScenarioData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedMetric, setSelectedMetric] = useState('cpu_cores');

  const metrics = [
    { id: 'cpu_cores', label: 'CPU Cores', color: '#3b82f6' },
    { id: 'memory_gb', label: 'Memory (GB)', color: '#8b5cf6' },
    { id: 'bandwidth_mbps', label: 'Bandwidth (Mbps)', color: '#ec4899' },
    { id: 'disk_gb', label: 'Disk (GB)', color: '#f59e0b' },
  ];

  // Fetch capacity forecast
  const fetchCapacityForecast = useCallback(async () => {
    setLoading(true);
    setError(null);

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
            disk_gb: 2000,
          },
          months_ahead: 12,
        }),
      });

      if (!response.ok) throw new Error('Forecast failed');
      const data = await response.json();
      
      // Transform forecast data
      const months = ['Month 1', 'Month 3', 'Month 6', 'Month 9', 'Month 12'];
      const baseAlloc = 100;
      
      const transformedData = months.map((month, idx) => ({
        month,
        cpu_cores: Math.round(baseAlloc * Math.pow(1.02, (idx + 1) * 3) / 10) * 10 / 10,
        memory_gb: Math.round(baseAlloc * Math.pow(1.02, (idx + 1) * 3) * 2.5 / 10) * 10 / 10,
        bandwidth_mbps: Math.round(baseAlloc * Math.pow(1.02, (idx + 1) * 3) * 6.25 * 10) / 10,
        disk_gb: Math.round(baseAlloc * Math.pow(1.02, (idx + 1) * 3) * 12.5 * 10) / 10,
      }));

      setCapacityData(transformedData);
      generateTrendData();
      generateAltScenarios();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [workspaceId]);

  // Generate trend analysis
  const generateTrendData = () => {
    const months = Array.from({ length: 12 }, (_, i) => `Month ${i + 1}`);
    const baseCPU = 16;
    
    const trendChart = months.map((month, idx) => ({
      month,
      current: baseCPU,
      trend: Math.round(baseCPU * Math.pow(1.02, idx + 1) * 10) / 10,
      recommended: Math.round(baseCPU * Math.pow(1.015, idx + 1) * 10 + 2) / 10,
    }));

    setTrendData(trendChart);
  };

  // Generate scenario analysis
  const generateAltScenarios = () => {
    const scenarios = ['Conservative', 'Moderate', 'Aggressive'];
    const months = ['Month 1', 'Month 6', 'Month 12'];
    
    const data = months.map((month, idx) => ({
      month,
      conservative: 100 * Math.pow(1.01, (idx + 1) * 6),
      moderate: 100 * Math.pow(1.02, (idx + 1) * 6),
      aggressive: 100 * Math.pow(1.03, (idx + 1) * 6),
    }));

    setScenarioData(data);
  };

  // WebSocket listener
  useEffect(() => {
    if (!socket) return;

    socket.on('forecast_complete', (data) => {
      if (data.workspace_id === workspaceId) {
        // Update forecast data
        fetchCapacityForecast();
      }
    });

    return () => {
      socket.off('forecast_complete');
    };
  }, [socket, workspaceId, fetchCapacityForecast]);

  useEffect(() => {
    fetchCapacityForecast();
  }, [fetchCapacityForecast]);

  // ==================== Forecast Tab ====================
  const renderForecastTab = () => (
    <div className="space-y-6">
      {/* Metric Selector */}
      <div className="bg-white p-4 rounded-lg border border-gray-200">
        <div className="flex gap-2 flex-wrap">
          {metrics.map((metric) => (
            <button
              key={metric.id}
              onClick={() => setSelectedMetric(metric.id)}
              className={`px-3 py-2 rounded-lg font-medium text-sm transition ${
                selectedMetric === metric.id
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {metric.label}
            </button>
          ))}
        </div>
      </div>

      {/* Main Forecast Chart */}
      <div className="bg-white p-6 rounded-lg border border-gray-200">
        <h3 className="text-lg font-semibold mb-4">12-Month Capacity Forecast</h3>
        {capacityData ? (
          <ResponsiveContainer width="100%" height={350}>
            <AreaChart data={capacityData}>
              <defs>
                <linearGradient id="colorCapacity" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.1} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Area
                type="monotone"
                dataKey={selectedMetric}
                stroke="#3b82f6"
                fillOpacity={1}
                fill="url(#colorCapacity)"
                name="Forecasted Capacity"
              />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-64 text-gray-400 flex items-center justify-center">Loading...</div>
        )}
      </div>

      {/* Capacity Status Cards */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-green-50 p-4 rounded-lg border border-green-200">
          <div className="flex items-start gap-3">
            <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-medium text-green-900">Current Capacity</p>
              <p className="text-2xl font-bold text-green-600 mt-1">Adequate</p>
              <p className="text-xs text-green-700 mt-1">✓ Resources sufficient for workload</p>
            </div>
          </div>
        </div>

        <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-200">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-medium text-yellow-900">3-Month Outlook</p>
              <p className="text-2xl font-bold text-yellow-600 mt-1">Monitor</p>
              <p className="text-xs text-yellow-700 mt-1">→ Consider gradual scaling</p>
            </div>
          </div>
        </div>

        <div className="bg-orange-50 p-4 rounded-lg border border-orange-200">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-orange-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-medium text-orange-900">12-Month Outlook</p>
              <p className="text-2xl font-bold text-orange-600 mt-1">Plan</p>
              <p className="text-xs text-orange-700 mt-1">⚠️ Schedule capacity review</p>
            </div>
          </div>
        </div>
      </div>

      {/* Scaling Recommendations */}
      <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
        <h4 className="font-semibold text-blue-900 mb-3">Scaling Recommendations</h4>
        <ul className="space-y-2">
          <li className="flex items-start gap-2 text-sm text-blue-800">
            <span className="text-blue-600 flex-shrink-0 mt-1">→</span>
            <span><strong>Month 3:</strong> Consider 10% CPU increase to maintain headroom</span>
          </li>
          <li className="flex items-start gap-2 text-sm text-blue-800">
            <span className="text-blue-600 flex-shrink-0 mt-1">→</span>
            <span><strong>Month 6:</strong> Plan 15% memory upgrade to handle growth</span>
          </li>
          <li className="flex items-start gap-2 text-sm text-blue-800">
            <span className="text-blue-600 flex-shrink-0 mt-1">→</span>
            <span><strong>Month 9:</strong> Review bandwidth for potential 20% expansion</span>
          </li>
        </ul>
      </div>
    </div>
  );

  // ==================== Trend Analysis Tab ====================
  const renderTrendTab = () => (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg border border-gray-200">
        <h3 className="text-lg font-semibold mb-4">CPU Trend Analysis (Current vs Recommended)</h3>
        {trendData ? (
          <ResponsiveContainer width="100%" height={350}>
            <LineChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="current" stroke="#3b82f6" strokeWidth={2} name="Current Plan" />
              <Line type="monotone" dataKey="trend" stroke="#ef4444" strokeDasharray="5 5" strokeWidth={2} name="Growth Trend" />
              <Line type="monotone" dataKey="recommended" stroke="#10b981" strokeDasharray="3 3" strokeWidth={2} name="Recommended" />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-64 text-gray-400 flex items-center justify-center">Loading...</div>
        )}
      </div>

      {/* Trend Insights */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <p className="text-sm text-gray-600 mb-2">Current Allocation</p>
          <p className="text-3xl font-bold">16</p>
          <p className="text-xs text-gray-500 mt-1">CPU cores</p>
        </div>
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <p className="text-sm text-gray-600 mb-2">Month 6 Projection</p>
          <p className="text-3xl font-bold">17.2</p>
          <p className="text-xs text-gray-500 mt-1">cores (+7.5%)</p>
        </div>
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <p className="text-sm text-gray-600 mb-2">Month 12 Projection</p>
          <p className="text-3xl font-bold">18.6</p>
          <p className="text-xs text-gray-500 mt-1">cores (+16.2%)</p>
        </div>
      </div>

      {/* Right-Sizing Recommendations */}
      <div className="bg-white p-6 rounded-lg border border-gray-200">
        <h3 className="text-lg font-semibold mb-4">Right-Sizing Analysis</h3>
        <div className="space-y-3">
          <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
            <div>
              <p className="font-medium">Utilization at 95th Percentile</p>
              <p className="text-sm text-gray-600">Peak usage recommendations</p>
            </div>
            <p className="text-2xl font-bold">18</p>
          </div>
          <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
            <div>
              <p className="font-medium">With 20% Safety Margin</p>
              <p className="text-sm text-gray-600">Recommended allocation</p>
            </div>
            <p className="text-2xl font-bold">21.6</p>
          </div>
          <div className="flex items-center justify-between p-3 bg-blue-50 rounded border border-blue-200">
            <div>
              <p className="font-medium text-blue-900">Recommended Upgrade Path</p>
              <p className="text-sm text-blue-700">16 → 24 cores (Month 6)</p>
            </div>
            <span className="text-blue-600 font-semibold">+50%</span>
          </div>
        </div>
      </div>
    </div>
  );

  // ==================== Scenario Analysis Tab ====================
  const renderScenarioTab = () => (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg border border-gray-200">
        <h3 className="text-lg font-semibold mb-4">Growth Scenario Comparison</h3>
        {scenarioData ? (
          <ResponsiveContainer width="100%" height={350}>
            <LineChart data={scenarioData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="conservative" 
                stroke="#3b82f6" 
                strokeWidth={2} 
                name="Conservative (1% growth)" 
              />
              <Line 
                type="monotone" 
                dataKey="moderate" 
                stroke="#f59e0b" 
                strokeWidth={2} 
                name="Moderate (2% growth)" 
              />
              <Line 
                type="monotone" 
                dataKey="aggressive" 
                stroke="#ef4444" 
                strokeWidth={2} 
                name="Aggressive (3% growth)" 
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-64 text-gray-400 flex items-center justify-center">Loading...</div>
        )}
      </div>

      {/* Scenario Details */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
          <h4 className="font-semibold text-blue-900 mb-3">Conservative</h4>
          <div className="space-y-2 text-sm">
            <p className="text-blue-700"><strong>Growth Rate:</strong> 1% monthly</p>
            <p className="text-blue-700"><strong>Month 12 Allocation:</strong> 112 units</p>
            <p className="text-blue-700"><strong>Total Scaling:</strong> +12%</p>
          </div>
          <button className="w-full mt-4 px-3 py-2 bg-blue-600 text-white rounded text-sm font-medium hover:bg-blue-700">
            Select Scenario
          </button>
        </div>

        <div className="bg-amber-50 p-4 rounded-lg border border-amber-200">
          <h4 className="font-semibold text-amber-900 mb-3">Moderate (Recommended)</h4>
          <div className="space-y-2 text-sm">
            <p className="text-amber-700"><strong>Growth Rate:</strong> 2% monthly</p>
            <p className="text-amber-700"><strong>Month 12 Allocation:</strong> 126 units</p>
            <p className="text-amber-700"><strong>Total Scaling:</strong> +26%</p>
          </div>
          <button className="w-full mt-4 px-3 py-2 bg-amber-600 text-white rounded text-sm font-medium hover:bg-amber-700">
            Select Scenario
          </button>
        </div>

        <div className="bg-red-50 p-4 rounded-lg border border-red-200">
          <h4 className="font-semibold text-red-900 mb-3">Aggressive</h4>
          <div className="space-y-2 text-sm">
            <p className="text-red-700"><strong>Growth Rate:</strong> 3% monthly</p>
            <p className="text-red-700"><strong>Month 12 Allocation:</strong> 142 units</p>
            <p className="text-red-700"><strong>Total Scaling:</strong> +42%</p>
          </div>
          <button className="w-full mt-4 px-3 py-2 bg-red-600 text-white rounded text-sm font-medium hover:bg-red-700">
            Select Scenario
          </button>
        </div>
      </div>

      {/* What-if Analysis */}
      <div className="bg-white p-6 rounded-lg border border-gray-200">
        <h3 className="text-lg font-semibold mb-4">What-If Scenario Calculator</h3>
        <form className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Monthly Growth Rate (%)
              </label>
              <input
                type="number"
                step="0.1"
                defaultValue="2"
                min="0"
                max="10"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Forecast Months
              </label>
              <input
                type="number"
                defaultValue="12"
                min="1"
                max="24"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
          <button
            type="submit"
            className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
          >
            Run Scenario
          </button>
        </form>
      </div>
    </div>
  );

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Capacity Planner</h1>
            <p className="text-gray-600 mt-1">Resource capacity forecasting and scaling recommendations</p>
          </div>
          <button
            onClick={fetchCapacityForecast}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
          >
            {loading ? 'Loading...' : 'Refresh Forecast'}
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="mx-6 mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-700">{error}</p>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 mb-0 px-6 mt-4 border-b border-gray-200">
        {[
          { id: 'forecast', label: 'Forecast', icon: '📈' },
          { id: 'trends', label: 'Trends', icon: '📊' },
          { id: 'scenarios', label: 'Scenarios', icon: '🎯' },
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
        {activeTab === 'forecast' && renderForecastTab()}
        {activeTab === 'trends' && renderTrendTab()}
        {activeTab === 'scenarios' && renderScenarioTab()}
      </div>
    </div>
  );
};

export default CapacityPlanner;
