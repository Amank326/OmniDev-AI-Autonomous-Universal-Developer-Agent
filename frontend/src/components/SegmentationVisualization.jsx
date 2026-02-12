"""
SegmentationVisualization Component

Interactive 2D/3D scatter plot visualization of customer segments
with cluster information and customer details on hover
"""

import React, { useState, useEffect } from 'react';
import Plot from 'react-plotly.js';
import { Card, Tabs, Tag, Table, Spin } from 'antd';
import axios from 'axios';

const SegmentationVisualization = ({ refreshInterval = 30000 }) => {
  const [segments, setSegments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [view3d, setView3d] = useState(false);
  const [selectedSegment, setSelectedSegment] = useState(null);

  useEffect(() => {
    fetchSegments();
    const interval = setInterval(fetchSegments, refreshInterval);
    return () => clearInterval(interval);
  }, []);

  const fetchSegments = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/v1/phase9/segmentation/segments', {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
      });
      setSegments(response.data.data);
    } catch (error) {
      console.error('Error fetching segments:', error);
    } finally {
      setLoading(false);
    }
  };

  // Generate sample data for visualization
  const generatePlotData = () => {
    const colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A'];
    
    return segments.map((segment, idx) => ({
      x: Array.from({ length: segment.customer_count }, () => Math.random() * 100),
      y: Array.from({ length: segment.customer_count }, () => Math.random() * 100),
      z: Array.from({ length: segment.customer_count }, () => Math.random() * 100),
      mode: 'markers',
      type: view3d ? 'scatter3d' : 'scatter',
      name: segment.segment_name,
      marker: {
        size: 8,
        color: colors[idx % colors.length],
        opacity: 0.7,
        line: { width: 1, color: 'white' }
      },
      text: Array.from({ length: segment.customer_count }, 
        (_, i) => `${segment.segment_name}<br>Customer ${i + 1}`),
      hovertemplate: '%{text}<extra></extra>'
    }));
  };

  const segmentColumns = [
    {
      title: 'Segment',
      dataIndex: 'segment_name',
      key: 'name',
      render: (text) => <Tag color="blue">{text}</Tag>
    },
    {
      title: 'Customers',
      dataIndex: 'customer_count',
      key: 'count',
      sorter: (a, b) => a.customer_count - b.customer_count
    },
    {
      title: 'Avg LTV',
      dataIndex: 'avg_ltv',
      key: 'ltv',
      render: (value) => `$${value?.toFixed(2) || 0}`
    },
    {
      title: 'Churn Risk',
      dataIndex: 'churn_risk',
      key: 'churn',
      render: (value) => {
        const risk = value?.toFixed(2) || 0;
        const color = risk > 0.6 ? 'red' : risk > 0.3 ? 'orange' : 'green';
        return <Tag color={color}>{(risk * 100).toFixed(0)}%</Tag>;
      }
    }
  ];

  return (
    <Card 
      title="Customer Segmentation Analysis" 
      loading={loading}
      extra={
        <button 
          onClick={() => setView3d(!view3d)}
          style={{ padding: '5px 15px', marginRight: '10px' }}
        >
          {view3d ? '2D View' : '3D View'}
        </button>
      }
    >
      <Tabs items={[
        {
          key: '1',
          label: 'Visualization',
          children: (
            <div style={{ height: '500px' }}>
              {segments.length > 0 ? (
                <Plot
                  data={generatePlotData()}
                  layout={{
                    title: 'Customer Segments',
                    hovermode: 'closest',
                    scene: view3d ? {
                      xaxis: { title: 'Feature X' },
                      yaxis: { title: 'Feature Y' },
                      zaxis: { title: 'Feature Z' }
                    } : undefined
                  }}
                  config={{ responsive: true, displayModeBar: true }}
                  style={{ width: '100%', height: '100%' }}
                />
              ) : (
                <Spin size="large" />
              )}
            </div>
          )
        },
        {
          key: '2',
          label: 'Segment Details',
          children: (
            <Table
              dataSource={segments}
              columns={segmentColumns}
              rowKey="segment_id"
              pagination={{ pageSize: 10 }}
              onRow={(record) => ({
                onClick: () => setSelectedSegment(record)
              })}
            />
          )
        }
      ]} />
    </Card>
  );
};

export default SegmentationVisualization;
