"""
PredictionDashboard Component

Displays churn predictions, LTV forecasts, and anomaly detection
with heatmaps, charts, and alerts
"""

import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Progress, Alert, Spin, Tag } from 'antd';
import { WarningOutlined, CheckCircleOutlined, ClockCircleOutlined } from '@ant-design/icons';
import axios from 'axios';
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, ScatterChart, Scatter
} from 'recharts';

const PredictionDashboard = ({ customerId = null }) => {
  const [churnPrediction, setChurnPrediction] = useState(null);
  const [ltvForecast, setLtvForecast] = useState(null);
  const [anomalies, setAnomalies] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (customerId) {
      fetchPredictions();
    }
  }, [customerId]);

  const fetchPredictions = async () => {
    setLoading(true);
    try {
      const headers = { Authorization: `Bearer ${localStorage.getItem('token')}` };
      
      const [churnRes, ltvRes, anomRes] = await Promise.all([
        axios.post(`/api/v1/phase9/predictions/churn?customer_id=${customerId}`, {}, { headers }),
        axios.post(`/api/v1/phase9/predictions/ltv?customer_id=${customerId}`, {}, { headers }),
        axios.post('/api/v1/phase9/predictions/anomalies', {}, { headers })
      ]);

      setChurnPrediction(churnRes.data.data);
      setLtvForecast(ltvRes.data.data);
      setAnomalies(anomRes.data.data || []);
    } catch (error) {
      console.error('Error fetching predictions:', error);
    } finally {
      setLoading(false);
    }
  };

  const getRiskColor = (riskLevel) => {
    const colors = { critical: 'red', high: 'orange', medium: 'gold', low: 'green' };
    return colors[riskLevel] || 'blue';
  };

  const getRiskIcon = (probability) => {
    if (probability > 0.7) return <WarningOutlined />;
    if (probability > 0.3) return <ClockCircleOutlined />;
    return <CheckCircleOutlined />;
  };

  // Sample LTV forecast data for chart
  const ltvChartData = Array.from({ length: 12 }, (_, i) => ({
    month: `M${i + 1}`,
    forecast: (ltvForecast?.forecasted_ltv || 5000) * (1 + Math.random() * 0.2),
    confidence_low: (ltvForecast?.confidence_low || 4000) * (1 + Math.random() * 0.1),
    confidence_high: (ltvForecast?.confidence_high || 6000) * (1 + Math.random() * 0.1)
  }));

  return (
    <Spin spinning={loading}>
      <div style={{ padding: '20px' }}>
        {/* Churn Risk Section */}
        <Card title="Churn Risk Prediction" style={{ marginBottom: '20px' }}>
          {churnPrediction ? (
            <Row gutter={[16, 16]}>
              <Col xs={24} sm={12} lg={6}>
                <Statistic
                  title="Churn Probability"
                  value={(churnPrediction.churn_probability * 100).toFixed(1)}
                  suffix="%"
                  prefix={getRiskIcon(churnPrediction.churn_probability)}
                  valueStyle={{ color: getRiskColor(churnPrediction.risk_level) }}
                />
              </Col>
              <Col xs={24} sm={12} lg={6}>
                <Statistic
                  title="Risk Level"
                  value={churnPrediction.risk_level?.toUpperCase()}
                  valueStyle={{ color: getRiskColor(churnPrediction.risk_level) }}
                />
              </Col>
              <Col xs={24} sm={12} lg={6}>
                <Statistic
                  title="Confidence Score"
                  value={(churnPrediction.confidence * 100).toFixed(0)}
                  suffix="%"
                />
              </Col>
              <Col xs={24} sm={12} lg={6}>
                <Statistic
                  title="Primary Risk Factor"
                  value={churnPrediction.risk_factors?.[0]?.name || 'N/A'}
                />
              </Col>
            </Row>
          ) : (
            <Alert message="No churn prediction available" type="info" />
          )}

          {churnPrediction?.risk_factors && (
            <div style={{ marginTop: '20px' }}>
              <h4>Risk Factors:</h4>
              <Row gutter={[8, 8]}>
                {churnPrediction.risk_factors.map((factor, idx) => (
                  <Col key={idx}>
                    <Tag color={getRiskColor('high')}>
                      {factor.name}: {(factor.score * 100).toFixed(0)}%
                    </Tag>
                  </Col>
                ))}
              </Row>
            </div>
          )}

          {churnPrediction?.churn_probability > 0.5 && (
            <Alert
              message="High Churn Risk Detected"
              description="This customer requires immediate attention. Consider sending a retention offer or assigning a dedicated account manager."
              type="warning"
              showIcon
              style={{ marginTop: '15px' }}
            />
          )}
        </Card>

        {/* LTV Forecast Section */}
        <Card title="Lifetime Value Forecast (12 Months)" style={{ marginBottom: '20px' }}>
          {ltvForecast ? (
            <>
              <Row gutter={[16, 16]} style={{ marginBottom: '20px' }}>
                <Col xs={24} sm={12} lg={6}>
                  <Statistic
                    title="Historical LTV"
                    value={ltvForecast.historical_ltv?.toFixed(0)}
                    prefix="$"
                  />
                </Col>
                <Col xs={24} sm={12} lg={6}>
                  <Statistic
                    title="Forecasted LTV"
                    value={ltvForecast.forecasted_ltv?.toFixed(0)}
                    prefix="$"
                    valueStyle={{ color: ltvForecast.trend === 'increasing' ? 'green' : 'red' }}
                  />
                </Col>
                <Col xs={24} sm={12} lg={6}>
                  <Statistic
                    title="Confidence Level"
                    value={(ltvForecast.confidence_level * 100).toFixed(0)}
                    suffix="%"
                  />
                </Col>
                <Col xs={24} sm={12} lg={6}>
                  <Statistic
                    title="Trend"
                    value={ltvForecast.trend?.toUpperCase()}
                    valueStyle={{ color: ltvForecast.trend === 'increasing' ? 'green' : 'red' }}
                  />
                </Col>
              </Row>

              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={ltvChartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="forecast" stroke="#1890ff" name="Forecast" />
                  <Line type="monotone" dataKey="confidence_low" stroke="#95de64" strokeDasharray="5 5" name="Low Confidence" />
                  <Line type="monotone" dataKey="confidence_high" stroke="#ff7a45" strokeDasharray="5 5" name="High Confidence" />
                </LineChart>
              </ResponsiveContainer>
            </>
          ) : (
            <Alert message="No LTV forecast available" type="info" />
          )}
        </Card>

        {/* Anomalies Section */}
        {anomalies.length > 0 && (
          <Card title={`Detected Anomalies (${anomalies.length})`}>
            <Row gutter={[8, 8]}>
              {anomalies.slice(0, 5).map((anomaly, idx) => (
                <Col key={idx} xs={24} sm={12} lg={8}>
                  <Alert
                    message={`Customer ${anomaly.customer_id}`}
                    description={`Amount: $${anomaly.amount?.toFixed(2)} | Score: ${anomaly.anomaly_score?.toFixed(2)}`}
                    type="warning"
                    showIcon
                  />
                </Col>
              ))}
            </Row>
          </Card>
        )}
      </div>
    </Spin>
  );
};

export default PredictionDashboard;
