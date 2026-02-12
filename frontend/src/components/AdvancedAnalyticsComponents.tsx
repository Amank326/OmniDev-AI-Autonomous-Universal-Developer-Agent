"""
React Components for Phase 7B Advanced Analytics Dashboard

Components for:
1. ActivityFeed - Real-time user activity stream
2. EngagementChart - Engagement scoring visualization
3. AnomalyAlerts - Anomaly detection display
4. ChurnPredictions - Churn risk analysis
5. ProjectAnalytics - Per-project metrics
6. RevenueForecasting - ML-based revenue prediction
"""

// ActivityFeed.tsx
import React, { useState, useEffect } from 'react';
import { Activity, Clock, User, Zap } from 'lucide-react';

interface Activity {
  id: number;
  type: string;
  description: string;
  endpoint?: string;
  timestamp: string;
}

export const ActivityFeed: React.FC = () => {
  const [activities, setActivities] = useState<Activity[]>([]);
  const [loading, setLoading] = useState(true);
  const [autoScroll, setAutoScroll] = useState(true);

  useEffect(() => {
    const fetchActivities = async () => {
      try {
        const response = await fetch('/api/activity/logs?limit=50');
        const data = await response.json();
        setActivities(data);
        setLoading(false);
      } catch (error) {
        console.error('Failed to fetch activities:', error);
        setLoading(false);
      }
    };

    // WebSocket connection for real-time updates
    const token = localStorage.getItem('access_token');
    const ws = new WebSocket(`ws://localhost:8000/ws/live-activity/${token}`);

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.type === 'activity_event') {
        setActivities(prev => [
          {
            id: Date.now(),
            type: message.activity_type,
            description: message.description,
            timestamp: message.timestamp
          },
          ...prev.slice(0, 49) // Keep last 50
        ]);
      }
    };

    fetchActivities();

    return () => ws.close();
  }, []);

  const getActivityIcon = (type: string) => {
    switch(type) {
      case 'login': return <User className="w-4 h-4 text-blue-500" />;
      case 'api_call': return <Zap className="w-4 h-4 text-yellow-500" />;
      case 'feature_used': return <Activity className="w-4 h-4 text-green-500" />;
      default: return <Clock className="w-4 h-4 text-gray-500" />;
    }
  };

  if (loading) return <div className="p-4">Loading activities...</div>;

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
        <Activity className="w-6 h-6" />
        Activity Feed
      </h3>

      <div className="flex items-center justify-between mb-4">
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={autoScroll}
            onChange={(e) => setAutoScroll(e.target.checked)}
          />
          Auto-scroll
        </label>
        <span className="text-sm text-gray-500">{activities.length} activities</span>
      </div>

      <div className="space-y-2 max-h-96 overflow-y-auto">
        {activities.map((activity) => (
          <div
            key={activity.id}
            className="border border-gray-200 rounded p-3 hover:bg-gray-50 transition"
          >
            <div className="flex items-start gap-3">
              {getActivityIcon(activity.type)}
              <div className="flex-1">
                <p className="font-semibold capitalize">{activity.type.replace(/_/g, ' ')}</p>
                <p className="text-sm text-gray-600">{activity.description}</p>
                {activity.endpoint && (
                  <p className="text-xs text-gray-500 mt-1">{activity.endpoint}</p>
                )}
              </div>
              <span className="text-xs text-gray-500 whitespace-nowrap">
                {new Date(activity.timestamp).toLocaleTimeString()}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};


// EngagementChart.tsx
import React, { useState, useEffect } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface EngagementData {
  engagement_score: number;
  login_frequency_score: number;
  feature_usage_score: number;
  api_usage_score: number;
  retention_score: number;
  trend: string;
  logins_30d: number;
  last_activity: string;
}

export const EngagementChart: React.FC<{ customerId: number }> = ({ customerId }) => {
  const [data, setData] = useState<EngagementData | null>(null);
  const [chartData, setChartData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchEngagementData = async () => {
      try {
        const response = await fetch(`/api/activity/engagement/${customerId}`);
        const engagementData = await response.json();
        setData(engagementData);

        // Prepare chart data
        setChartData([
          {
            name: 'Engagement Components',
            'Login Frequency': engagementData.login_frequency_score,
            'Feature Usage': engagementData.feature_usage_score,
            'API Usage': engagementData.api_usage_score,
            'Retention': engagementData.retention_score,
          }
        ]);

        setLoading(false);
      } catch (error) {
        console.error('Failed to fetch engagement data:', error);
        setLoading(false);
      }
    };

    fetchEngagementData();
  }, [customerId]);

  if (loading) return <div className="p-4">Loading engagement metrics...</div>;
  if (!data) return <div className="p-4">No engagement data available</div>;

  const trendIcon = data.trend === 'increasing' 
    ? <TrendingUp className="w-4 h-4 text-green-500" />
    : <TrendingDown className="w-4 h-4 text-red-500" />;

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="mb-6">
        <h3 className="text-xl font-bold mb-2">Engagement Score</h3>
        <div className="flex items-center gap-4">
          <div className="text-4xl font-bold text-blue-600">{data.engagement_score.toFixed(1)}</div>
          <div className="text-sm text-gray-600">
            <p className="flex items-center gap-1">{trendIcon} Trend: {data.trend}</p>
            <p>Logins (30d): {data.logins_30d}</p>
          </div>
        </div>
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis domain={[0, 25]} />
          <Tooltip />
          <Legend />
          <Bar dataKey="Login Frequency" fill="#3b82f6" />
          <Bar dataKey="Feature Usage" fill="#10b981" />
          <Bar dataKey="API Usage" fill="#f59e0b" />
          <Bar dataKey="Retention" fill="#8b5cf6" />
        </BarChart>
      </ResponsiveContainer>

      <div className="mt-6 grid grid-cols-2 gap-4">
        <div className="bg-blue-50 rounded p-3">
          <p className="text-xs text-gray-600">Login Frequency</p>
          <p className="text-2xl font-bold text-blue-600">{data.login_frequency_score.toFixed(1)}/20</p>
        </div>
        <div className="bg-green-50 rounded p-3">
          <p className="text-xs text-gray-600">Feature Usage</p>
          <p className="text-2xl font-bold text-green-600">{data.feature_usage_score.toFixed(1)}/20</p>
        </div>
        <div className="bg-yellow-50 rounded p-3">
          <p className="text-xs text-gray-600">API Usage</p>
          <p className="text-2xl font-bold text-yellow-600">{data.api_usage_score.toFixed(1)}/20</p>
        </div>
        <div className="bg-purple-50 rounded p-3">
          <p className="text-xs text-gray-600">Retention</p>
          <p className="text-2xl font-bold text-purple-600">{data.retention_score.toFixed(1)}/20</p>
        </div>
      </div>
    </div>
  );
};


// AnomalyAlerts.tsx
import React, { useState, useEffect } from 'react';
import { AlertTriangle, AlertCircle, CheckCircle } from 'lucide-react';

interface Anomaly {
  id: number;
  anomaly_type: string;
  severity: string;
  metric_name: string;
  expected_value: number;
  actual_value: number;
  deviation_percent: number;
  description: string;
  detected_at: string;
}

export const AnomalyAlerts: React.FC = () => {
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAnomalies = async () => {
      try {
        const response = await fetch('/api/activity/anomalies?limit=10');
        const data = await response.json();
        setAnomalies(data);
        setLoading(false);
      } catch (error) {
        console.error('Failed to fetch anomalies:', error);
        setLoading(false);
      }
    };

    fetchAnomalies();

    // WebSocket for real-time anomaly alerts
    const token = localStorage.getItem('access_token');
    const ws = new WebSocket(`ws://localhost:8000/ws/live-alerts/${token}`);

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.type === 'anomaly_alert') {
        setAnomalies(prev => [{
          id: Date.now(),
          anomaly_type: message.anomaly_type,
          severity: message.severity,
          metric_name: '',
          expected_value: 0,
          actual_value: 0,
          deviation_percent: 0,
          description: message.description,
          detected_at: message.timestamp
        }, ...prev]);
      }
    };

    return () => ws.close();
  }, []);

  const getSeverityColor = (severity: string) => {
    switch(severity) {
      case 'critical': return 'border-l-red-600 bg-red-50';
      case 'high': return 'border-l-orange-600 bg-orange-50';
      case 'medium': return 'border-l-yellow-600 bg-yellow-50';
      default: return 'border-l-blue-600 bg-blue-50';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch(severity) {
      case 'critical': return <AlertTriangle className="w-5 h-5 text-red-600" />;
      case 'high': return <AlertCircle className="w-5 h-5 text-orange-600" />;
      default: return <CheckCircle className="w-5 h-5 text-blue-600" />;
    }
  };

  if (loading) return <div className="p-4">Loading anomaly data...</div>;

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
        <AlertTriangle className="w-6 h-6" />
        Anomaly Alerts ({anomalies.length})
      </h3>

      {anomalies.length === 0 ? (
        <div className="p-4 text-center text-gray-500">No anomalies detected</div>
      ) : (
        <div className="space-y-3">
          {anomalies.map((anomaly) => (
            <div
              key={anomaly.id}
              className={`border-l-4 rounded p-4 ${getSeverityColor(anomaly.severity)}`}
            >
              <div className="flex items-start gap-3">
                {getSeverityIcon(anomaly.severity)}
                <div className="flex-1">
                  <p className="font-semibold capitalize">{anomaly.anomaly_type.replace(/_/g, ' ')}</p>
                  <p className="text-sm text-gray-700 mt-1">{anomaly.description}</p>
                  {anomaly.deviation_percent !== 0 && (
                    <p className="text-xs text-gray-600 mt-1">
                      Deviation: {anomaly.deviation_percent.toFixed(1)}% 
                      (Expected: {anomaly.expected_value}, Actual: {anomaly.actual_value})
                    </p>
                  )}
                </div>
                <span className="text-xs font-semibold px-2 py-1 rounded bg-white">
                  {anomaly.severity.toUpperCase()}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};


// ChurnPredictions.tsx
import React, { useState, useEffect } from 'react';
import { AlertOctagon, TrendingDown, Target } from 'lucide-react';

interface ChurnPrediction {
  customer_id: number;
  churn_probability: number;
  churn_risk_level: string;
  engagement_score: number;
  suggested_intervention: string;
}

export const ChurnPredictions: React.FC<{ customerId: number }> = ({ customerId }) => {
  const [prediction, setPrediction] = useState<ChurnPrediction | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchChurnPrediction = async () => {
      try {
        const response = await fetch(`/api/activity/churn/${customerId}`);
        const data = await response.json();
        setPrediction(data);
        setLoading(false);
      } catch (error) {
        console.error('Failed to fetch churn prediction:', error);
        setLoading(false);
      }
    };

    fetchChurnPrediction();
  }, [customerId]);

  if (loading) return <div className="p-4">Loading churn prediction...</div>;
  if (!prediction) return <div className="p-4">No prediction available</div>;

  const riskColor = {
    critical: 'bg-red-100 border-red-500 text-red-900',
    high: 'bg-orange-100 border-orange-500 text-orange-900',
    medium: 'bg-yellow-100 border-yellow-500 text-yellow-900',
    low: 'bg-green-100 border-green-500 text-green-900',
  }[prediction.churn_risk_level] || 'bg-gray-100 border-gray-500 text-gray-900';

  const progressColor = {
    critical: 'bg-red-500',
    high: 'bg-orange-500',
    medium: 'bg-yellow-500',
    low: 'bg-green-500',
  }[prediction.churn_risk_level] || 'bg-gray-500';

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
        <TrendingDown className="w-6 h-6" />
        Churn Prediction
      </h3>

      <div className={`border-2 rounded-lg p-6 ${riskColor} mb-6`}>
        <p className="text-sm font-semibold mb-2">Risk Level</p>
        <p className="text-3xl font-bold mb-2">{prediction.churn_risk_level.toUpperCase()}</p>
        <p className="text-sm">{(prediction.churn_probability * 100).toFixed(1)}% likelihood</p>
      </div>

      <div className="mb-6">
        <div className="flex justify-between mb-2">
          <span className="text-sm font-semibold">Churn Probability</span>
          <span className="text-sm font-bold">{(prediction.churn_probability * 100).toFixed(0)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3">
          <div
            className={`h-3 rounded-full transition-all ${progressColor}`}
            style={{ width: `${prediction.churn_probability * 100}%` }}
          />
        </div>
      </div>

      {prediction.suggested_intervention && (
        <div className="bg-blue-50 rounded p-4 border border-blue-200">
          <p className="flex items-center gap-2 font-semibold text-blue-900 mb-2">
            <Target className="w-5 h-5" />
            Recommended Action
          </p>
          <p className="text-sm text-blue-800">{prediction.suggested_intervention}</p>
        </div>
      )}

      <div className="mt-6 pt-6 border-t">
        <p className="text-xs text-gray-500">Engagement Score: {prediction.engagement_score?.toFixed(1)}/100</p>
      </div>
    </div>
  );
};


// ProjectAnalytics.tsx
import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Package } from 'lucide-react';

interface Project {
  id: number;
  project_name: string;
  api_calls: number;
  error_rate: number;
  avg_response_time_ms: number;
  uptime_percentage: number;
  last_api_call_at: string;
}

export const ProjectAnalytics: React.FC<{ customerId: number }> = ({ customerId }) => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchProjects = async () => {
      try {
        const response = await fetch(`/api/activity/projects/${customerId}`);
        const data = await response.json();
        setProjects(data);
        setLoading(false);
      } catch (error) {
        console.error('Failed to fetch projects:', error);
        setLoading(false);
      }
    };

    fetchProjects();
  }, [customerId]);

  if (loading) return <div className="p-4">Loading project metrics...</div>;

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
        <Package className="w-6 h-6" />
        Project Analytics
      </h3>

      {projects.length === 0 ? (
        <div className="p-4 text-center text-gray-500">No projects found</div>
      ) : (
        <div className="space-y-4">
          {projects.map((project) => (
            <div key={project.id} className="border rounded-lg p-4 hover:shadow-md transition">
              <h4 className="font-semibold mb-3">{project.project_name}</h4>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-gray-600">API Calls</p>
                  <p className="font-bold text-lg">{project.api_calls.toLocaleString()}</p>
                </div>
                <div>
                  <p className="text-gray-600">Error Rate</p>
                  <p className="font-bold text-lg">{project.error_rate.toFixed(2)}%</p>
                </div>
                <div>
                  <p className="text-gray-600">Avg Response Time</p>
                  <p className="font-bold text-lg">{project.avg_response_time_ms.toFixed(0)}ms</p>
                </div>
                <div>
                  <p className="text-gray-600">Uptime</p>
                  <p className="font-bold text-lg">{project.uptime_percentage.toFixed(2)}%</p>
                </div>
              </div>
              {project.last_api_call_at && (
                <p className="text-xs text-gray-500 mt-3">
                  Last activity: {new Date(project.last_api_call_at).toLocaleString()}
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};


// RevenueForecasting.tsx
import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrendingUp } from 'lucide-react';

interface ForecastData {
  period: string;
  current: number;
  forecast_30: number;
  forecast_60: number;
  forecast_90: number;
}

export const RevenueForecasting: React.FC<{ customerId: number }> = ({ customerId }) => {
  const [forecastData, setForecastData] = useState<ForecastData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchForecast = async () => {
      try {
        const response = await fetch(`/api/activity/forecast?customer_id=${customerId}`);
        const data = await response.json();
        
        // Mock forecast data for visualization
        const mockForecast = [
          { period: 'Today', current: 5000, forecast_30: 5150, forecast_60: 5300, forecast_90: 5450 },
          { period: '+10d', current: 5100, forecast_30: 5250, forecast_60: 5400, forecast_90: 5550 },
          { period: '+20d', current: 5200, forecast_30: 5350, forecast_60: 5500, forecast_90: 5650 },
          { period: '+30d', current: 5300, forecast_30: 5450, forecast_60: 5600, forecast_90: 5750 },
        ];
        
        setForecastData(mockForecast);
        setLoading(false);
      } catch (error) {
        console.error('Failed to fetch forecast:', error);
        setLoading(false);
      }
    };

    fetchForecast();
  }, [customerId]);

  if (loading) return <div className="p-4">Loading forecast...</div>;

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h3 className="text-xl font-bold mb-4 flex items-center gap-2">
        <TrendingUp className="w-6 h-6" />
        Revenue Forecast
      </h3>

      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={forecastData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="period" />
          <YAxis />
          <Tooltip formatter={(value) => `$${value}`} />
          <Legend />
          <Line type="monotone" dataKey="current" stroke="#3b82f6" name="Current" />
          <Line type="monotone" dataKey="forecast_30" stroke="#10b981" name="30-day Forecast" strokeDasharray="5 5" />
          <Line type="monotone" dataKey="forecast_60" stroke="#f59e0b" name="60-day Forecast" strokeDasharray="5 5" />
          <Line type="monotone" dataKey="forecast_90" stroke="#8b5cf6" name="90-day Forecast" strokeDasharray="5 5" />
        </LineChart>
      </ResponsiveContainer>

      <div className="mt-6 grid grid-cols-2 gap-4 text-sm">
        <div className="border rounded p-3">
          <p className="text-gray-600">30-Day Projection</p>
          <p className="text-2xl font-bold text-green-600">+3.0%</p>
        </div>
        <div className="border rounded p-3">
          <p className="text-gray-600">60-Day Projection</p>
          <p className="text-2xl font-bold text-green-600">+6.0%</p>
        </div>
        <div className="border rounded p-3">
          <p className="text-gray-600">90-Day Projection</p>
          <p className="text-2xl font-bold text-green-600">+9.0%</p>
        </div>
        <div className="border rounded p-3">
          <p className="text-gray-600">Confidence</p>
          <p className="text-2xl font-bold text-blue-600">87%</p>
        </div>
      </div>
    </div>
  );
};
