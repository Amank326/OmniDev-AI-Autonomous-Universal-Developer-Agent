import React, { useState, useEffect } from 'react';
import { LineChart, Line, AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ScatterChart, Scatter } from 'recharts';
import { TrendingUp, Target, Zap, Calculator } from 'lucide-react';

const DynamicPricingManager = ({ agentId }) => {
  const [basePriceInput, setBasePriceInput] = useState(99);
  const [demandInput, setDemandInput] = useState(0.65);
  const [currentPrice, setCurrentPrice] = useState(99);
  const [optimizedPrice, setOptimizedPrice] = useState(null);
  const [demandCurve, setDemandCurve] = useState([]);
  const [pricingHistory, setPricingHistory] = useState([]);
  const [abTests, setAbTests] = useState([]);
  const [elasticity, setElasticity] = useState(-1.3);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadPricingData();
    generateDemandCurve(basePriceInput);
  }, [agentId]);

  const loadPricingData = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/v1/automation/analytics/pricing-impact/${agentId}`);
      const data = await response.json();
      
      if (data.data) {
        setElasticity(data.data.demand_elasticity || -1.3);
      }

      // Mock historical data
      const history = [];
      for (let i = 30; i >= 0; i--) {
        const date = new Date();
        date.setDate(date.getDate() - i);
        history.push({
          date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
          price: 99 + (Math.random() * 10 - 5),
          revenue: 4200 + (Math.random() * 800 - 400),
          quantity: 42 + (Math.random() * 8 - 4),
        });
      }
      setPricingHistory(history);

      // Mock A/B tests
      setAbTests([
        { id: 'test_1', control: 99, variant: 105, controlConversions: 152, variantConversions: 79, daysLeft: 3, winner: 'control' },
        { id: 'test_2', control: 89, variant: 95, controlConversions: 168, variantConversions: 145, daysLeft: 0, winner: 'variant' },
      ]);
    } catch (error) {
      console.error('Failed to load pricing data:', error);
    } finally {
      setLoading(false);
    }
  };

  const generateDemandCurve = (basePrice) => {
    const curve = [];
    for (let price = basePrice * 0.6; price <= basePrice * 1.5; price += basePrice * 0.05) {
      const quantity = 50 * Math.pow(price / basePrice, elasticity);
      const revenue = price * quantity;
      curve.push({
        price: Math.round(price),
        quantity: Math.round(quantity * 10) / 10,
        revenue: Math.round(revenue),
      });
    }
    setDemandCurve(curve);
  };

  const calculateOptimalPrice = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/v1/automation/pricing/calculate-optimal/${agentId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          base_price: basePriceInput,
          demand: demandInput,
          goal: 'revenue',
        }),
      });

      const data = await response.json();
      if (data.data) {
        setOptimizedPrice(data.data);
      }
    } catch (error) {
      console.error('Failed to calculate optimal price:', error);
    } finally {
      setLoading(false);
    }
  };

  const startAbTest = async () => {
    const variantPrice = Math.round(currentPrice * (1 + (Math.random() * 0.1 - 0.05)));
    
    try {
      const response = await fetch('/api/v1/automation/pricing/ab-test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          control_price: currentPrice,
          variant_price: variantPrice,
          split_ratio: 50,
          duration: 7,
        }),
      });

      const data = await response.json();
      if (data.data) {
        setAbTests([...abTests, data.data]);
      }
    } catch (error) {
      console.error('Failed to start A/B test:', error);
    }
  };

  const applyPrice = async (newPrice) => {
    setCurrentPrice(newPrice);
    try {
      await fetch(`/api/v1/automation/pricing/track-performance/${agentId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          price: newPrice,
          quantity: 45,
        }),
      });
    } catch (error) {
      console.error('Failed to apply price:', error);
    }
  };

  return (
    <div className="w-full bg-gray-50 min-h-screen p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <h1 className="text-3xl font-bold mb-2">Dynamic Pricing Manager</h1>
          <p className="text-gray-600">Agent: {agentId}</p>
        </div>

        {/* Price Calculator */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <Calculator className="w-5 h-5 text-blue-500" />
            Price Optimizer
          </h2>

          <div className="grid grid-cols-3 gap-6">
            {/* Input Controls */}
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Base Price
                </label>
                <div className="flex gap-2">
                  <input
                    type="number"
                    value={basePriceInput}
                    onChange={(e) => {
                      setBasePriceInput(parseFloat(e.target.value));
                      generateDemandCurve(parseFloat(e.target.value));
                    }}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded"
                    step="1"
                  />
                  <span className="text-2xl font-semibold text-gray-700 px-2">$</span>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Current Demand
                </label>
                <div className="flex items-center gap-2">
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                    value={demandInput}
                    onChange={(e) => setDemandInput(parseFloat(e.target.value))}
                    className="flex-1"
                  />
                  <span className="text-lg font-semibold w-12">{(demandInput * 100).toFixed(0)}%</span>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Price Elasticity
                </label>
                <input
                  type="number"
                  value={elasticity}
                  onChange={(e) => {
                    setElasticity(parseFloat(e.target.value));
                    generateDemandCurve(basePriceInput);
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded"
                  step="0.1"
                />
                <p className="text-xs text-gray-500 mt-1">
                  {elasticity < -1.5 ? '📈 Elastic' : elasticity < -0.5 ? '📊 Unit Elastic' : '📉 Inelastic'}
                </p>
              </div>

              <button
                onClick={calculateOptimalPrice}
                disabled={loading}
                className="w-full bg-blue-500 hover:bg-blue-600 disabled:bg-gray-400 text-white py-2 rounded font-semibold"
              >
                {loading ? 'Calculating...' : 'Calculate Optimal Price'}
              </button>
            </div>

            {/* Optimization Results */}
            <div className="bg-gradient-to-br from-blue-50 to-purple-50 rounded-lg p-4 border border-blue-200">
              {optimizedPrice ? (
                <div className="space-y-3">
                  <h3 className="font-semibold text-lg">Optimization Results</h3>
                  
                  <div className="bg-white rounded p-3">
                    <p className="text-sm text-gray-600">Recommended Price</p>
                    <p className="text-3xl font-bold text-green-600">
                      ${optimizedPrice.optimal_price}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      {optimizedPrice.price_change_percent > 0 ? '↑' : '↓'} {Math.abs(optimizedPrice.price_change_percent)}% change
                    </p>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div className="bg-white rounded p-2">
                      <p className="text-gray-600">Expected Revenue</p>
                      <p className="font-semibold">${optimizedPrice.expected_revenue}</p>
                    </div>
                    <div className="bg-white rounded p-2">
                      <p className="text-gray-600">Est. Quantity</p>
                      <p className="font-semibold">{optimizedPrice.expected_quantity}</p>
                    </div>
                  </div>

                  <button
                    onClick={() => applyPrice(optimizedPrice.optimal_price)}
                    className="w-full bg-green-500 hover:bg-green-600 text-white py-2 rounded font-semibold text-sm"
                  >
                    Apply This Price
                  </button>
                </div>
              ) : (
                <div className="h-full flex items-center justify-center text-gray-400">
                  Click "Calculate Optimal Price" to get recommendations
                </div>
              )}
            </div>

            {/* Current Metrics */}
            <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-lg p-4 border border-purple-200">
              <h3 className="font-semibold text-lg mb-3">Current Metrics</h3>
              <div className="space-y-2 text-sm">
                <div>
                  <p className="text-gray-600">Current Price</p>
                  <p className="text-2xl font-bold text-purple-600">${currentPrice}</p>
                </div>
                <div>
                  <p className="text-gray-600">Est. Monthly Revenue</p>
                  <p className="text-lg font-semibold">$4,455</p>
                </div>
                <div>
                  <p className="text-gray-600">Est. Quantity</p>
                  <p className="text-lg font-semibold">45 units</p>
                </div>
                <button
                  onClick={startAbTest}
                  className="w-full mt-3 bg-purple-500 hover:bg-purple-600 text-white py-2 rounded font-semibold text-sm"
                >
                  Start A/B Test
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Demand Curve */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-green-500" />
            Demand Curve Analysis
          </h2>

          <ResponsiveContainer width="100%" height={300}>
            <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" dataKey="price" name="Price ($)" />
              <YAxis type="number" dataKey="revenue" name="Revenue ($)" />
              <Tooltip cursor={{ strokeDasharray: '3 3' }} />
              <Scatter name="Revenue Points" data={demandCurve} fill="#3b82f6" />
            </ScatterChart>
          </ResponsiveContainer>

          <div className="grid grid-cols-4 gap-4 mt-4">
            {demandCurve.length > 0 && demandCurve.map((point, idx) => (
              idx % Math.floor(demandCurve.length / 4) === 0 && (
                <div key={idx} className="border rounded p-2 text-center text-sm">
                  <p className="text-gray-600">Price: ${point.price}</p>
                  <p className="font-semibold">${point.revenue} Revenue</p>
                  <p className="text-gray-500">{point.quantity} units</p>
                </div>
              )
            ))}
          </div>
        </div>

        {/* Pricing History */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Pricing & Revenue History</h2>

          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={pricingHistory}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
              <Tooltip />
              <Legend />
              <Area yAxisId="left" type="monotone" dataKey="price" fill="#3b82f6" stroke="#3b82f6" name="Price ($)" />
              <Area yAxisId="right" type="monotone" dataKey="revenue" fill="#10b981" stroke="#10b981" name="Revenue ($)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* A/B Tests */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
            <Zap className="w-5 h-5 text-orange-500" />
            A/B Tests
          </h2>

          <div className="grid grid-cols-1 gap-4">
            {abTests.map((test) => (
              <ABTestCard key={test.id} test={test} />
            ))}

            {abTests.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                No active A/B tests. Click "Start A/B Test" to begin testing.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// Helper Components

const ABTestCard = ({ test }) => {
  const totalControl = test.controlConversions;
  const totalVariant = test.variantConversions;
  const controlRate = ((totalControl / (totalControl + 10)) * 100).toFixed(1);
  const variantRate = ((totalVariant / (totalVariant + 10)) * 100).toFixed(1);
  const winner = test.winner === 'control' ? 'control' : 'variant';

  return (
    <div className="border rounded-lg p-4 hover:bg-gray-50">
      <div className="flex justify-between items-start mb-3">
        <h3 className="font-semibold">Test: ${test.control} vs ${test.variant}</h3>
        <span className={`text-xs font-semibold px-2 py-1 rounded ${
          test.daysLeft > 0
            ? 'bg-blue-100 text-blue-800'
            : 'bg-green-100 text-green-800'
        }`}>
          {test.daysLeft > 0 ? `${test.daysLeft}d left` : 'Completed'}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <p className="text-sm font-semibold mb-2">Control: ${test.control}</p>
          <div className="flex items-center gap-2 mb-1">
            <div className="flex-1 bg-gray-200 rounded-full h-3 overflow-hidden">
              <div className="bg-blue-500 h-full" style={{ width: '60%' }} />
            </div>
            <span className="text-sm font-semibold">{controlRate}%</span>
          </div>
          <p className="text-xs text-gray-600">{totalControl} conversions</p>
        </div>

        <div>
          <p className="text-sm font-semibold mb-2">Variant: ${test.variant}</p>
          <div className="flex items-center gap-2 mb-1">
            <div className="flex-1 bg-gray-200 rounded-full h-3 overflow-hidden">
              <div className="bg-green-500 h-full" style={{ width: '40%' }} />
            </div>
            <span className="text-sm font-semibold">{variantRate}%</span>
          </div>
          <p className="text-xs text-gray-600">{totalVariant} conversions</p>
        </div>
      </div>

      {test.daysLeft === 0 && (
        <div className="mt-3 p-2 bg-green-50 border border-green-200 rounded text-sm">
          <p>Winner: <span className="font-semibold">${winner === 'control' ? test.control : test.variant}</span> 
          ({winner === 'control' ? controlRate : variantRate}% conversion)</p>
        </div>
      )}
    </div>
  );
};

export default DynamicPricingManager;
