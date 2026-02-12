import React, { useState, useEffect, useCallback } from 'react';
import {
  PieChart, Pie, BarChart, Bar, LineChart, Line, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell, ScatterChart, Scatter
} from 'recharts';
import { DollarSign, TrendingUp, Users, Target, AlertCircle, CheckCircle } from 'lucide-react';

const CostPlanner = ({ workspaceId, socket }) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [costData, setCostData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [expandedOpp, setExpandedOpp] = useState(null);
  const [forecastData, setForecastData] = useState(null);

  // Color palette for cost categories
  const categoryColors = {
    COMPUTE: '#3b82f6',
    STORAGE: '#8b5cf6',
    NETWORK: '#ec4899',
    DATABASE: '#14b8a6',
    ANALYTICS: '#f59e0b',
    ML: '#6366f1',
    MONITORING: '#06b6d4',
    OTHER: '#6b7280',
  };

  // Fetch cost analysis
  const fetchCostAnalysis = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/optimization/costs/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Workspace-ID': workspaceId,
        },
        body: JSON.stringify({
          period_days: 30,
          num_users: 10,
        }),
      });

      if (!response.ok) throw new Error('Cost analysis failed');
      const data = await response.json();
      setCostData(data);

      // Generate forecast
      generateForecast(data.total_cost);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [workspaceId]);

  // Generate cost forecast
  const generateForecast = (currentCost) => {
    const months = [];
    let cost = currentCost;
    const months_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    
    for (let i = 0; i < 12; i++) {
      months.push({
        month: months_names[i],
        forecast: Math.round(cost * 100) / 100,
        trend: Math.random() > 0.5 ? Math.round((cost * 1.02) * 100) / 100 : Math.round((cost * 0.98) * 100) / 100,
      });
      cost = cost * 1.02; // 2% monthly growth
    }
    setForecastData(months);
  };

  // WebSocket listener
  useEffect(() => {
    if (!socket) return;

    socket.on('cost_analysis_complete', (data) => {
      if (data.workspace_id === workspaceId) {
        setCostData({
          ...costData,
          total_cost: data.total_cost,
          cost_per_user: data.cost_per_user,
          cost_by_category: data.cost_by_category,
        });
      }
    });

    return () => {
      socket.off('cost_analysis_complete');
    };
  }, [socket, workspaceId, costData]);

  useEffect(() => {
    fetchCostAnalysis();
  }, [fetchCostAnalysis]);

  // ==================== Overview Tab ====================
  const renderOverviewTab = () => (
    <div className="space-y-6">
      {/* Top KPIs */}
      <div className="grid grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Monthly Cost</p>
              <p className="text-2xl font-bold">
                ${costData?.total_cost ? costData.total_cost.toFixed(2) : '0.00'}
              </p>
            </div>
            <DollarSign className="w-8 h-8 text-blue-500" />
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Cost Per User</p>
              <p className="text-2xl font-bold">
                ${costData?.cost_per_user ? costData.cost_per_user.toFixed(2) : '0.00'}
              </p>
            </div>
            <Users className="w-8 h-8 text-green-500" />
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Cost Trend</p>
              <p className="text-2xl font-bold">
                {costData?.trend === 'INCREASING' ? '📈' : costData?.trend === 'DECREASING' ? '📉' : '→'} {costData?.trend || 'STABLE'}
              </p>
            </div>
            <TrendingUp className="w-8 h-8 text-purple-500" />
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Optimization Potential</p>
              <p className="text-2xl font-bold">
                {costData?.optimization_potential_percent ? costData.optimization_potential_percent.toFixed(1) : '0'}%
              </p>
            </div>
            <Target className="w-8 h-8 text-orange-500" />
          </div>
        </div>
      </div>

      {/* Cost Breakdown by Category */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <h3 className="text-lg font-semibold mb-4">Cost by Category</h3>
          {costData?.cost_by_category ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={Object.entries(costData.cost_by_category).map(([name, value]) => ({
                    name,
                    value: parseFloat(value),
                  }))}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {Object.keys(costData.cost_by_category).map((category) => (
                    <Cell key={category} fill={categoryColors[category] || '#6b7280'} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => `$${value.toFixed(2)}`} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-64 text-gray-400 flex items-center justify-center">Loading...</div>
          )}
        </div>

        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <h3 className="text-lg font-semibold mb-4">Cost Breakdown Table</h3>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {costData?.breakdown ? (
              costData.breakdown.map((item, idx) => (
                <div key={idx} className="flex items-center justify-between p-2 hover:bg-gray-50 rounded">
                  <div className="flex items-center gap-2 flex-1">
                    <div
                      className="w-3 h-3 rounded flex-shrink-0"
                      style={{ backgroundColor: categoryColors[item.category] || '#6b7280' }}
                    />
                    <span className="text-sm font-medium">{item.category}</span>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-semibold">${item.cost.toFixed(2)}</p>
                    <p className="text-xs text-gray-500">{item.percentage.toFixed(1)}%</p>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-gray-400 text-sm">No data available</p>
            )}
          </div>
        </div>
      </div>

      {/* Cost Forecast */}
      {forecastData && (
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <h3 className="text-lg font-semibold mb-4">12-Month Cost Forecast</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={forecastData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip formatter={(value) => `$${value.toFixed(2)}`} />
              <Legend />
              <Line type="monotone" dataKey="forecast" stroke="#3b82f6" strokeWidth={2} name="Forecast" />
              <Line type="monotone" dataKey="trend" stroke="#ef4444" strokeDasharray="5 5" strokeWidth={2} name="Projection" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );

  // ==================== Team Allocation Tab ====================
  const renderAllocationTab = () => {
    const allocations = costData?.allocations || [];
    const total = allocations.reduce((sum, a) => sum + a.cost, 0);

    return (
      <div className="space-y-4">
        <div className="bg-white p-6 rounded-lg border border-gray-200">
          <h3 className="text-lg font-semibold mb-4">Cost Allocation by Team</h3>
          
          {allocations.length > 0 ? (
            <div className="space-y-3">
              {allocations.map((alloc, idx) => (
                <div key={idx} className="border border-gray-200 rounded p-4 hover:bg-gray-50">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-semibold capitalize">{alloc.owner}</h4>
                    <p className="text-lg font-bold text-blue-600">${alloc.cost.toFixed(2)}</p>
                  </div>
                  
                  <div className="space-y-2">
                    <div>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-gray-600">Percentage</span>
                        <span className="font-semibold">{alloc.percentage.toFixed(1)}%</span>
                      </div>
                      <div className="w-full h-2 bg-gray-200 rounded overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-blue-500 to-blue-600"
                          style={{ width: `${alloc.percentage}%` }}
                        />
                      </div>
                    </div>

                    <div className="pt-2 border-t border-gray-100">
                      <p className="text-xs text-gray-600">
                        Primary Driver: <span className="font-semibold">{alloc.primary_driver}</span>
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <p>No allocation data available</p>
            </div>
          )}
        </div>
      </div>
    );
  };

  // ==================== Opportunities Tab ====================
  const renderOpportunitiesTab = () => {
    const opportunities = costData?.opportunities || [];
    const totalSavings = opportunities.reduce((sum, opp) => sum + opp.savings, 0);

    return (
      <div className="space-y-4">
        {/* Summary Card */}
        {totalSavings > 0 && (
          <div className="bg-gradient-to-r from-green-50 to-emerald-50 p-6 rounded-lg border border-green-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-green-700 font-medium">Total Savings Opportunity</p>
                <p className="text-3xl font-bold text-green-900 mt-1">
                  ${totalSavings.toFixed(2)}/month
                </p>
                <p className="text-xs text-green-700 mt-1">
                  {(totalSavings * 12).toFixed(0)}/year savings potential
                </p>
              </div>
              <CheckCircle className="w-12 h-12 text-green-500" />
            </div>
          </div>
        )}

        {/* Opportunities List */}
        <div className="space-y-3">
          {opportunities.length > 0 ? (
            opportunities.map((opp, idx) => (
              <div key={opp.opportunity_id || idx} className="bg-white border border-gray-200 rounded-lg overflow-hidden">
                <button
                  onClick={() => setExpandedOpp(expandedOpp === idx ? null : idx)}
                  className="w-full p-4 hover:bg-gray-50 flex items-center justify-between"
                >
                  <div className="flex items-start gap-3 flex-1 text-left">
                    <div className={`w-10 h-10 rounded flex items-center justify-center flex-shrink-0 ${
                      opp.category === 'COMPUTE' ? 'bg-blue-100' :
                      opp.category === 'STORAGE' ? 'bg-purple-100' :
                      opp.category === 'NETWORK' ? 'bg-pink-100' : 'bg-gray-100'
                    }`}>
                      <DollarSign className="w-5 h-5" />
                    </div>
                    <div className="flex-1">
                      <h4 className="font-semibold">{opp.category} Optimization</h4>
                      <p className="text-sm text-gray-600">{opp.description}</p>
                      <div className="flex gap-4 mt-2 text-xs">
                        <span>Current: ${opp.current_spend.toFixed(2)}</span>
                        <span>→ Target: ${opp.recommended_spend.toFixed(2)}</span>
                      </div>
                    </div>
                  </div>
                  <div className="text-right flex-shrink-0">
                    <p className="text-lg font-bold text-green-600">${opp.savings.toFixed(2)}</p>
                    <p className="text-xs text-gray-500"{opp.savings_percent.toFixed(1)}% savings</p>
                  </div>
                </button>

                {expandedOpp === idx && (
                  <div className="px-4 py-4 bg-gray-50 border-t border-gray-200 space-y-3">
                    <div className="grid grid-cols-4 gap-4">
                      <div>
                        <p className="text-xs font-medium text-gray-600 uppercase">Effort</p>
                        <p className="text-sm font-semibold mt-1">{opp.effort}</p>
                      </div>
                      <div>
                        <p className="text-xs font-medium text-gray-600 uppercase">Payback</p>
                        <p className="text-sm font-semibold mt-1">{opp.payback_months.toFixed(1)} months</p>
                      </div>
                      <div>
                        <p className="text-xs font-medium text-gray-600 uppercase">Risk</p>
                        <p className="text-sm font-semibold mt-1">{opp.risk}</p>
                      </div>
                      <div>
                        <p className="text-xs font-medium text-gray-600 uppercase">Annual Savings</p>
                        <p className="text-sm font-semibold text-green-600 mt-1">
                          ${(opp.savings * 12).toFixed(2)}
                        </p>
                      </div>
                    </div>

                    {opp.actions && opp.actions.length > 0 && (
                      <div className="pt-3 border-t border-gray-200">
                        <p className="text-xs font-medium text-gray-700 uppercase mb-2">Recommended Actions</p>
                        <ul className="space-y-1">
                          {opp.actions.map((action, actionIdx) => (
                            <li key={actionIdx} className="text-sm text-gray-700 flex items-start gap-2">
                              <span className="text-blue-500 flex-shrink-0">•</span>
                              <span>{action}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    <div className="pt-3 border-t border-gray-200">
                      <button className="w-full px-3 py-2 bg-green-600 text-white rounded text-sm font-medium hover:bg-green-700">
                        Implement Opportunity
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ))
          ) : (
            <div className="text-center py-8 text-gray-500">
              <p>No optimization opportunities identified at this time</p>
            </div>
          )}
        </div>
      </div>
    );
  };

  // ==================== ROI Calculator Tab ====================
  const renderROITab = () => (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg border border-gray-200">
        <h3 className="text-lg font-semibold mb-4">ROI Calculator</h3>
        
        <form className="space-y-4" onSubmit={(e) => {
          e.preventDefault();
          // ROI calculation would happen here
        }}>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Investment Amount ($)
              </label>
              <input
                type="number"
                defaultValue="5000"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Annual Savings ($)
              </label>
              <input
                type="number"
                defaultValue="2000"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>

          <button className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium">
            Calculate ROI
          </button>
        </form>

        <div className="mt-6 space-y-3">
          <div className="p-3 bg-blue-50 rounded border border-blue-200">
            <p className="text-sm text-gray-600">Return on Investment (ROI)</p>
            <p className="text-2xl font-bold text-blue-600 mt-1">40%</p>
          </div>
          <div className="p-3 bg-green-50 rounded border border-green-200">
            <p className="text-sm text-gray-600">Payback Period</p>
            <p className="text-2xl font-bold text-green-600 mt-1">2.5 years</p>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="flex flex-col h-full bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Cost Planner</h1>
            <p className="text-gray-600 mt-1">Cost analysis, allocation, and optimization opportunities</p>
          </div>
          <button
            onClick={fetchCostAnalysis}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
          >
            {loading ? 'Analyzing...' : 'Refresh Analysis'}
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="mx-6 mt-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold text-red-800">Error</p>
            <p className="text-sm text-red-700">{error}</p>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 mb-0 px-6 mt-4 border-b border-gray-200">
        {[
          { id: 'overview', label: 'Overview', icon: '📊' },
          { id: 'allocation', label: 'Team Allocation', icon: '👥' },
          { id: 'opportunities', label: 'Opportunities', icon: '💰' },
          { id: 'roi', label: 'ROI Calculator', icon: '📈' },
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
        {activeTab === 'allocation' && renderAllocationTab()}
        {activeTab === 'opportunities' && renderOpportunitiesTab()}
        {activeTab === 'roi' && renderROITab()}
      </div>
    </div>
  );
};

export default CostPlanner;
