import React, { useState, useEffect } from 'react';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { AlertCircle, TrendingUp, DollarSign, Zap, Settings } from 'lucide-react';

const AutomationDashboard = ({ agentId }) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [dunningStrategies, setDunningStrategies] = useState([]);
  const [pricingMetrics, setPricingMetrics] = useState(null);
  const [workflowStatus, setWorkflowStatus] = useState([]);
  const [subscriptionMetrics, setSubscriptionMetrics] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadDashboardData();
    const interval = setInterval(loadDashboardData, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, [agentId]);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const [subs, dunning, pricing, workflows] = await Promise.all([
        fetch(`/api/v1/automation/subscriptions/metrics/${agentId}`).then(r => r.json()),
        fetch(`/api/v1/automation/analytics/dunning-performance/${agentId}`).then(r => r.json()),
        fetch(`/api/v1/automation/analytics/pricing-impact/${agentId}`).then(r => r.json()),
        fetch(`/api/v1/automation/analytics/workflow-efficiency/${agentId}`).then(r => r.json()),
      ]);

      setSubscriptionMetrics(subs.data);
      setDunningStrategies([
        { name: 'Aggressive', success: dunning.data?.recovery_rate || 57, attempts: 142 },
        { name: 'Moderate', success: 68, attempts: 198 },
        { name: 'Conservative', success: 45, attempts: 76 },
      ]);
      setPricingMetrics(pricing.data);
      setWorkflowStatus(workflows.data ? [
        { status: 'Successful', count: Math.round(workflows.data.total_executions * (workflows.data.success_rate / 100)) },
        { status: 'Failed', count: workflows.data.failed_executions },
      ] : []);
    } catch (error) {
      console.error('Failed to load dashboard:', error);
    } finally {
      setLoading(false);
    }
  };

  const DunningOptimizationSection = () => (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold flex items-center gap-2">
        <Zap className="w-5 h-5 text-orange-500" />
        Dunning Strategy Optimization
      </h3>

      {dunningStrategies.length > 0 && (
        <div className="bg-white rounded-lg shadow p-4">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={dunningStrategies}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
              <Tooltip />
              <Legend />
              <Bar yAxisId="left" dataKey="success" fill="#3b82f6" name="Success Rate %" />
              <Bar yAxisId="right" dataKey="attempts" fill="#10b981" name="Attempts" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      <div className="grid grid-cols-3 gap-4">
        <DunningCard
          strategy="Aggressive"
          successRate={57.1}
          recovered={8450}
          roi={3.4}
          recommendation="High-value customers"
          color="bg-red-50"
        />
        <DunningCard
          strategy="Moderate"
          successRate={68}
          recovered={12250}
          roi={4.2}
          recommendation="Medium-value customers"
          color="bg-yellow-50"
        />
        <DunningCard
          strategy="Conservative"
          successRate={45}
          recovered={3200}
          roi={1.8}
          recommendation="Low-value customers"
          color="bg-green-50"
        />
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-800">
          💡 <strong>Optimization Insight:</strong> ML model recommends switching 15 customers to "Moderate" strategy based on payment history. Estimated recovery increase: +$2,150 (23%).
        </p>
      </div>
    </div>
  );

  const PricingOptimizationSection = () => (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold flex items-center gap-2">
        <DollarSign className="w-5 h-5 text-green-500" />
        Dynamic Pricing Optimization
      </h3>

      {pricingMetrics && (
        <div className="grid grid-cols-2 gap-4">
          <MetricCard
            title="Current Price"
            value="$99"
            change="+8.5%"
            changePositive={true}
          />
          <MetricCard
            title="Demand Elasticity"
            value="-1.3"
            subtitle="Unit elastic pricing"
          />
          <MetricCard
            title="Revenue Impact"
            value="+6.2%"
            change="From last increase"
            changePositive={true}
          />
          <MetricCard
            title="Volume Impact"
            value="-4.8%"
            change="Expected decrease"
            changePositive={false}
          />
        </div>
      )}

      <div className="bg-white rounded-lg shadow p-4">
        <h4 className="font-semibold mb-3">Price Recommendations</h4>
        <div className="space-y-3">
          <PriceRecommendation
            strategy="Increase 5%"
            confidence={78}
            expectedRevenue={"+$340"}
            reasoning="High demand detected, market allows premium"
          />
          <PriceRecommendation
            strategy="Maintain Current"
            confidence={65}
            expectedRevenue="Stable"
            reasoning="Balanced approach for steady growth"
          />
          <PriceRecommendation
            strategy="Decrease 5%"
            confidence={42}
            expectedRevenue="-$280"
            reasoning="May increase volume but lower margins"
          />
        </div>
      </div>

      <div className="bg-green-50 border border-green-200 rounded-lg p-4">
        <p className="text-sm text-green-800">
          📈 <strong>A/B Test Active:</strong> Testing $99 (control) vs $105 (variant). Current winner: $99 (52% more conversions). Test ends in 3 days.
        </p>
      </div>
    </div>
  );

  const WorkflowAutomationSection = () => (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold flex items-center gap-2">
        <Settings className="w-5 h-5 text-purple-500" />
        Workflow Automation Management
      </h3>

      {workflowStatus.length > 0 && (
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-white rounded-lg shadow p-4">
            <h4 className="font-semibold mb-3">Execution Success Rate</h4>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={workflowStatus}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="count"
                >
                  <Cell fill="#10b981" />
                  <Cell fill="#ef4444" />
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-white rounded-lg shadow p-4">
            <h4 className="font-semibold mb-3">Workflow Metrics</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span>Active Workflows:</span>
                <span className="font-semibold">12</span>
              </div>
              <div className="flex justify-between">
                <span>Total Executions:</span>
                <span className="font-semibold">487</span>
              </div>
              <div className="flex justify-between">
                <span>Success Rate:</span>
                <span className="font-semibold text-green-600">94.7%</span>
              </div>
              <div className="flex justify-between">
                <span>Avg Duration:</span>
                <span className="font-semibold">45 sec</span>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="bg-white rounded-lg shadow p-4">
        <h4 className="font-semibold mb-3">Quick Actions</h4>
        <div className="grid grid-cols-2 gap-2">
          <button className="bg-blue-500 hover:bg-blue-600 text-white px-3 py-2 rounded text-sm">
            Create New Workflow
          </button>
          <button className="bg-green-500 hover:bg-green-600 text-white px-3 py-2 rounded text-sm">
            Execute Now
          </button>
          <button className="bg-orange-500 hover:bg-orange-600 text-white px-3 py-2 rounded text-sm">
            View Schedule
          </button>
          <button className="bg-purple-500 hover:bg-purple-600 text-white px-3 py-2 rounded text-sm">
            Retry Failed
          </button>
        </div>
      </div>
    </div>
  );

  const SubscriptionMetricsSection = () => (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold flex items-center gap-2">
        <TrendingUp className="w-5 h-5 text-blue-500" />
        Subscription Metrics
      </h3>

      {subscriptionMetrics && (
        <div className="grid grid-cols-4 gap-4">
          <MetricCard
            title="MRR"
            value={`$${subscriptionMetrics.mrr?.toLocaleString() || '0'}`}
            subtitle="Monthly Recurring"
            trend="+12%"
          />
          <MetricCard
            title="ARR"
            value={`$${subscriptionMetrics.arr?.toLocaleString() || '0'}`}
            subtitle="Annual Run Rate"
            trend="+8%"
          />
          <MetricCard
            title="Active Subscriptions"
            value={subscriptionMetrics.active_subscriptions || 24}
            subtitle="Currently Active"
            trend="+2"
          />
          <MetricCard
            title="Churn Rate"
            value={`${subscriptionMetrics.churn_rate || 2.1}%`}
            subtitle="Monthly Churn"
            trend="-0.3%"
          />
        </div>
      )}
    </div>
  );

  return (
    <div className="w-full bg-gray-50 min-h-screen p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <h1 className="text-3xl font-bold mb-2">Automation Dashboard</h1>
          <p className="text-gray-600">Agent: {agentId}</p>
        </div>

        {/* Tab Navigation */}
        <div className="flex gap-2 mb-6 bg-white rounded-lg shadow p-1">
          {['overview', 'dunning', 'pricing', 'workflows'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-2 rounded font-medium capitalize transition-colors ${
                activeTab === tab
                  ? 'bg-blue-500 text-white'
                  : 'text-gray-700 hover:bg-gray-100'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="space-y-6">
          {loading && (
            <div className="bg-white rounded-lg shadow p-4 text-center text-gray-500">
              Loading data...
            </div>
          )}

          {!loading && (
            <>
              {activeTab === 'overview' && (
                <>
                  <SubscriptionMetricsSection />
                  <DunningOptimizationSection />
                  <PricingOptimizationSection />
                </>
              )}

              {activeTab === 'dunning' && <DunningOptimizationSection />}
              {activeTab === 'pricing' && <PricingOptimizationSection />}
              {activeTab === 'workflows' && <WorkflowAutomationSection />}
            </>
          )}
        </div>
      </div>
    </div>
  );
};

// Helper Components

const MetricCard = ({ title, value, subtitle, trend, change, changePositive }) => (
  <div className="bg-white rounded-lg shadow p-4">
    <p className="text-sm text-gray-600 mb-1">{title}</p>
    <p className="text-2xl font-bold mb-2">{value}</p>
    {subtitle && <p className="text-xs text-gray-500">{subtitle}</p>}
    {(trend || change) && (
      <p className={`text-sm font-semibold mt-2 ${changePositive ? 'text-green-600' : 'text-red-600'}`}>
        {trend || change}
      </p>
    )}
  </div>
);

const DunningCard = ({ strategy, successRate, recovered, roi, recommendation, color }) => (
  <div className={`${color} border rounded-lg p-4`}>
    <h4 className="font-semibold mb-2">{strategy} Strategy</h4>
    <div className="space-y-1 text-sm">
      <p>Success Rate: <span className="font-semibold">{successRate}%</span></p>
      <p>Recovered: <span className="font-semibold">${recovered.toLocaleString()}</span></p>
      <p>ROI: <span className="font-semibold">{roi}x</span></p>
      <p className="text-gray-700 mt-2 italic">{recommendation}</p>
    </div>
  </div>
);

const PriceRecommendation = ({ strategy, confidence, expectedRevenue, reasoning }) => (
  <div className="border rounded-lg p-3 hover:bg-gray-50">
    <div className="flex justify-between items-start">
      <div className="flex-1">
        <p className="font-semibold">{strategy}</p>
        <p className="text-sm text-gray-600">{reasoning}</p>
      </div>
      <div className="text-right ml-4">
        <p className="text-sm text-gray-600">Confidence</p>
        <p className="font-semibold text-lg text-blue-600">{confidence}%</p>
        <p className="text-sm text-green-600 font-semibold">{expectedRevenue}</p>
      </div>
    </div>
    <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
      <div
        className="bg-blue-500 h-2 rounded-full"
        style={{ width: `${confidence}%` }}
      />
    </div>
  </div>
);

export default AutomationDashboard;
