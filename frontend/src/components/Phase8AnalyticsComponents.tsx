/**
 * Phase 8: Advanced Analytics Dashboard Components
 *
 * Provides 4 advanced visualization components for:
 * - CohortMatrix: Retention heatmap across cohorts and time periods
 * - RetentionChart: Line chart showing retention curves for multiple cohorts
 * - LTVProjection: Bar chart comparing historical vs projected LTV across customers
 * - JourneyVisualization: Sankey diagram of customer journey stages
 */

import React, { useState, useEffect } from 'react';
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, ComposedChart
} from 'recharts';
import { TrendingUp, TrendingDown, AlertCircle, CheckCircle } from 'lucide-react';
import { api } from '../services/api';

// ============================================================================
// COHORT MATRIX COMPONENT
// ============================================================================

interface CohortMatrixProps {
  cohortIds?: number[];
  refresh?: boolean;
}

export const CohortMatrix: React.FC<CohortMatrixProps> = ({
  cohortIds = [],
  refresh = false
}) => {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (cohortIds.length === 0) return;
    loadCohortData();
  }, [cohortIds, refresh]);

  const loadCohortData = async () => {
    setLoading(true);
    try {
      const results = await Promise.all(
        cohortIds.map(id => api.get(`/cohorts/retention/${id}`))
      );

      const matrixData: any[] = [];
      results.forEach((response: any) => {
        const curve = response.data;
        const cohortName = curve.cohort_name;

        curve.points.forEach((point: any) => {
          const existingRow = matrixData.find(
            r => r.period === point.period_label
          );

          if (existingRow) {
            existingRow[cohortName] = point.retention_percentage;
          } else {
            matrixData.push({
              period: point.period_label,
              [cohortName]: point.retention_percentage
            });
          }
        });
      });

      setData(matrixData.sort((a, b) => {
        const order = ['Day 0', 'Week 1', 'Month 1', 'Month 3', 'Month 6', 'Month 12'];
        return order.indexOf(a.period) - order.indexOf(b.period);
      }));
    } catch (error) {
      console.error('Failed to load cohort data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="p-4 text-center">Loading cohort data...</div>;
  }

  if (data.length === 0) {
    return <div className="p-4 text-gray-500">No cohort data available</div>;
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">Cohort Retention Matrix</h3>

      {/* Heatmap Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b">
              <th className="text-left p-2">Period</th>
              {cohortIds.map((id) => (
                <th key={id} className="text-center p-2 font-medium">
                  Cohort {id}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.map((row) => (
              <tr key={row.period} className="border-b hover:bg-gray-50">
                <td className="p-2 font-medium">{row.period}</td>
                {cohortIds.map((id) => {
                  const value = row[`Cohort ${id}`] || 0;
                  const color = getHeatmapColor(value);

                  return (
                    <td
                      key={id}
                      className={`text-center p-2 ${color}`}
                    >
                      {value.toFixed(1)}%
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Color Legend */}
      <div className="mt-4 flex items-center gap-4 text-xs">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-green-500"></div>
          <span>High Retention (&gt;70%)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-yellow-500"></div>
          <span>Medium (30-70%)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-red-500"></div>
          <span>Low (&lt;30%)</span>
        </div>
      </div>
    </div>
  );
};

function getHeatmapColor(value: number): string {
  if (value >= 70) return 'bg-green-100 text-green-900';
  if (value >= 30) return 'bg-yellow-100 text-yellow-900';
  return 'bg-red-100 text-red-900';
}


// ============================================================================
// RETENTION CURVE COMPONENT
// ============================================================================

interface RetentionCurveData {
  period_label: string;
  retention_percentage: number;
  api_calls_in_period: number;
}

interface RetentionChartProps {
  cohortIds: number[];
  refresh?: boolean;
}

export const RetentionChart: React.FC<RetentionChartProps> = ({
  cohortIds,
  refresh = false
}) => {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadRetentionData();
  }, [cohortIds, refresh]);

  const loadRetentionData = async () => {
    setLoading(true);
    try {
      const results = await Promise.all(
        cohortIds.map(id =>
          api.get(`/cohorts/retention/${id}`).then(r => ({
            cohortId: id,
            ...r.data
          }))
        )
      );

      // Transform data for multi-line chart
      const chartData: any[] = [];
      const points = results[0]?.points || [];

      points.forEach((point: RetentionCurveData, idx: number) => {
        const row: any = { period: point.period_label };

        results.forEach(result => {
          if (result.points[idx]) {
            row[`Cohort ${result.cohortId}`] = result.points[idx].retention_percentage;
          }
        });

        chartData.push(row);
      });

      setData(chartData);
    } catch (error) {
      console.error('Failed to load retention data:', error);
    } finally {
      setLoading(false);
    }
  };

  const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">Retention Curves by Cohort</h3>

      {loading && <div className="text-center py-8">Loading...</div>}

      {!loading && data.length > 0 && (
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis
              dataKey="period"
              style={{ fontSize: 12 }}
            />
            <YAxis
              label={{ value: 'Retention %', angle: -90, position: 'insideLeft' }}
            />
            <Tooltip
              formatter={(value: number) => `${value.toFixed(1)}%`}
              labelStyle={{ color: '#000' }}
            />
            <Legend />

            {cohortIds.map((id, idx) => (
              <Line
                key={id}
                type="monotone"
                dataKey={`Cohort ${id}`}
                stroke={colors[idx % colors.length]}
                strokeWidth={2}
                dot={{ r: 4 }}
                connectNulls
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      )}

      {!loading && data.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          No retention data available
        </div>
      )}

      {/* Key Insights */}
      <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-blue-50 p-4 rounded">
          <div className="text-sm text-gray-600">Avg Month 1 Retention</div>
          <div className="text-2xl font-bold text-blue-600">
            {calculateAverageRetention(data, 'Month 1')}%
          </div>
        </div>
        <div className="bg-green-50 p-4 rounded">
          <div className="text-sm text-gray-600">Avg Month 3 Retention</div>
          <div className="text-2xl font-bold text-green-600">
            {calculateAverageRetention(data, 'Month 3')}%
          </div>
        </div>
        <div className="bg-purple-50 p-4 rounded">
          <div className="text-sm text-gray-600">Avg Year 1 Retention</div>
          <div className="text-2xl font-bold text-purple-600">
            {calculateAverageRetention(data, 'Month 12')}%
          </div>
        </div>
      </div>
    </div>
  );
};

function calculateAverageRetention(data: any[], period: string): string {
  if (data.length === 0) return '0';

  const row = data.find(r => r.period === period);
  if (!row) return '0';

  const values = Object.entries(row)
    .filter(([key]) => key.startsWith('Cohort'))
    .map(([, value]) => value as number);

  const avg = values.reduce((a, b) => a + b, 0) / values.length;
  return avg.toFixed(1);
}


// ============================================================================
// LTV PROJECTION COMPONENT
// ============================================================================

interface LTVData {
  customer_id: number;
  historical_ltv: number;
  projected_ltv: number;
  ltv_tier: string;
  churn_risk_score: number;
}

interface LTVProjectionProps {
  customerIds: number[];
  refresh?: boolean;
}

export const LTVProjection: React.FC<LTVProjectionProps> = ({
  customerIds,
  refresh = false
}) => {
  const [data, setData] = useState<LTVData[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadLTVData();
  }, [customerIds, refresh]);

  const loadLTVData = async () => {
    setLoading(true);
    try {
      const results = await Promise.all(
        customerIds.map(id =>
          api.get(`/cohorts/ltv/${id}`).then(r => r.data)
        )
      );
      setData(results);
    } catch (error) {
      console.error('Failed to load LTV data:', error);
    } finally {
      setLoading(false);
    }
  };

  const chartData = data.map((ltv, idx) => ({
    customer: `C${ltv.customer_id}`,
    historical: ltv.historical_ltv,
    projected: ltv.projected_ltv,
    growth: ltv.projected_ltv - ltv.historical_ltv
  }));

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">Lifetime Value Projections</h3>

      {loading && <div className="text-center py-8">Loading...</div>}

      {!loading && data.length > 0 && (
        <>
          <ResponsiveContainer width="100%" height={400}>
            <ComposedChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="customer" />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
              <Tooltip
                formatter={(value: number) => `$${value.toFixed(2)}`}
                labelStyle={{ color: '#000' }}
              />
              <Legend />

              <Bar yAxisId="left" dataKey="historical" fill="#3b82f6" name="Historical LTV" />
              <Bar yAxisId="left" dataKey="projected" fill="#10b981" name="Projected LTV" />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="growth"
                stroke="#f59e0b"
                name="Growth Potential"
              />
            </ComposedChart>
          </ResponsiveContainer>

          {/* Customer Details */}
          <div className="mt-6 space-y-3">
            <h4 className="font-semibold text-gray-700">Customer Segments</h4>

            {data.map((ltv) => (
              <div
                key={ltv.customer_id}
                className="flex items-center justify-between p-3 bg-gray-50 rounded"
              >
                <div>
                  <div className="font-medium">Customer {ltv.customer_id}</div>
                  <div className="text-sm text-gray-600">
                    {ltv.historical_ltv.toFixed(2)} → {ltv.projected_ltv.toFixed(2)}
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                    ltv.ltv_tier === 'High' ? 'bg-green-100 text-green-700' :
                    ltv.ltv_tier === 'Medium' ? 'bg-yellow-100 text-yellow-700' :
                    'bg-red-100 text-red-700'
                  }`}>
                    {ltv.ltv_tier}
                  </div>

                  {ltv.churn_risk_score > 0.7 ? (
                    <AlertCircle className="w-5 h-5 text-red-500" />
                  ) : (
                    <CheckCircle className="w-5 h-5 text-green-500" />
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Summary Stats */}
          <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-blue-50 p-4 rounded">
              <div className="text-sm text-gray-600">Avg Historical</div>
              <div className="text-2xl font-bold text-blue-600">
                ${(data.reduce((a, b) => a + b.historical_ltv, 0) / data.length).toFixed(0)}
              </div>
            </div>
            <div className="bg-green-50 p-4 rounded">
              <div className="text-sm text-gray-600">Avg Projected</div>
              <div className="text-2xl font-bold text-green-600">
                ${(data.reduce((a, b) => a + b.projected_ltv, 0) / data.length).toFixed(0)}
              </div>
            </div>
            <div className="bg-purple-50 p-4 rounded">
              <div className="text-sm text-gray-600">Avg Growth</div>
              <div className="text-2xl font-bold text-purple-600">
                ${(
                  data.reduce((a, b) => a + (b.projected_ltv - b.historical_ltv), 0) /
                  data.length
                ).toFixed(0)}
              </div>
            </div>
          </div>
        </>
      )}

      {!loading && data.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          No LTV data available
        </div>
      )}
    </div>
  );
};


// ============================================================================
// JOURNEY VISUALIZATION COMPONENT
// ============================================================================

interface JourneyData {
  customer_id: number;
  current_stage: string;
  days_in_stage: number;
  momentum_score: number;
  at_risk: boolean;
  engagement_trajectory: string;
}

interface JourneyVisualizationProps {
  customerIds: number[];
  refresh?: boolean;
}

const STAGES = [
  { name: 'Awareness', color: '#e5e7eb' },
  { name: 'Consideration', color: '#bfdbfe' },
  { name: 'Activation', color: '#86efac' },
  { name: 'Retention', color: '#34d399' },
  { name: 'Revenue', color: '#6366f1' },
  { name: 'Advocacy', color: '#8b5cf6' }
];

export const JourneyVisualization: React.FC<JourneyVisualizationProps> = ({
  customerIds,
  refresh = false
}) => {
  const [data, setData] = useState<JourneyData[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadJourneyData();
  }, [customerIds, refresh]);

  const loadJourneyData = async () => {
    setLoading(true);
    try {
      const results = await Promise.all(
        customerIds.map(id =>
          api.get(`/cohorts/journey/${id}`).then(r => r.data)
        )
      );
      setData(results);
    } catch (error) {
      console.error('Failed to load journey data:', error);
    } finally {
      setLoading(false);
    }
  };

  const stageCounts = STAGES.map(stage => {
    const count = data.filter(d => d.current_stage === stage.name).length;
    return { ...stage, count };
  });

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-6">Customer Journey Distribution</h3>

      {loading && <div className="text-center py-8">Loading...</div>}

      {!loading && data.length > 0 && (
        <>
          {/* Flow Diagram */}
          <div className="mb-8">
            <div className="flex items-center justify-between gap-2 mb-6">
              {stageCounts.map((stage, idx) => (
                <div key={stage.name} className="flex-1 text-center">
                  <div
                    className="w-full p-4 rounded-lg mb-2 flex items-center justify-center"
                    style={{ backgroundColor: stage.color }}
                  >
                    <span className="font-semibold text-gray-800">
                      {stage.count}
                    </span>
                  </div>
                  <div className="text-xs font-medium text-gray-600">
                    {stage.name}
                  </div>
                  <div className="text-xs text-gray-500">
                    {((stage.count / data.length) * 100).toFixed(0)}%
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Customer Details by Stage */}
          <div className="space-y-4">
            <h4 className="font-semibold text-gray-700">Customer Details</h4>

            {data.map((journey) => {
              const stage = STAGES.find(s => s.name === journey.current_stage);

              return (
                <div
                  key={journey.customer_id}
                  className="p-4 bg-gray-50 rounded border-l-4"
                  style={{ borderColor: stage?.color || '#e5e7eb' }}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="font-medium">Customer {journey.customer_id}</div>
                    <div className="flex items-center gap-2">
                      {journey.momentum_score > 0.3 ? (
                        <TrendingUp className="w-4 h-4 text-green-500" />
                      ) : journey.momentum_score < -0.3 ? (
                        <TrendingDown className="w-4 h-4 text-red-500" />
                      ) : (
                        <div className="w-4 h-4 text-gray-400">→</div>
                      )}
                      {journey.at_risk && (
                        <AlertCircle className="w-4 h-4 text-yellow-500" />
                      )}
                    </div>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <div className="text-gray-600">Current Stage</div>
                      <div className="font-medium">{journey.current_stage}</div>
                    </div>
                    <div>
                      <div className="text-gray-600">Days in Stage</div>
                      <div className="font-medium">{journey.days_in_stage}</div>
                    </div>
                    <div>
                      <div className="text-gray-600">Momentum</div>
                      <div className="font-medium">
                        {journey.momentum_score.toFixed(2)}
                      </div>
                    </div>
                    <div>
                      <div className="text-gray-600">Trajectory</div>
                      <div className="font-medium">{journey.engagement_trajectory}</div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Stage Statistics */}
          <div className="mt-8 pt-6 border-t">
            <h4 className="font-semibold text-gray-700 mb-4">Stage Summary</h4>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-green-50 p-4 rounded">
                <div className="text-sm text-gray-600">Growing Customers</div>
                <div className="text-2xl font-bold text-green-600">
                  {data.filter(d => d.momentum_score > 0.3).length}
                </div>
              </div>
              <div className="bg-yellow-50 p-4 rounded">
                <div className="text-sm text-gray-600">At-Risk Customers</div>
                <div className="text-2xl font-bold text-yellow-600">
                  {data.filter(d => d.at_risk).length}
                </div>
              </div>
              <div className="bg-blue-50 p-4 rounded">
                <div className="text-sm text-gray-600">High Revenue Stage</div>
                <div className="text-2xl font-bold text-blue-600">
                  {data.filter(d => ['Revenue', 'Advocacy'].includes(d.current_stage)).length}
                </div>
              </div>
            </div>
          </div>
        </>
      )}

      {!loading && data.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          No journey data available
        </div>
      )}
    </div>
  );
};

export default {
  CohortMatrix,
  RetentionChart,
  LTVProjection,
  JourneyVisualization
};
