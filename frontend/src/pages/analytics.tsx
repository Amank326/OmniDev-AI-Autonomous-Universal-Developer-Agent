/**
 * Analytics Page - Phase 6
 * Main analytics dashboard page with tabbed navigation
 */

import React, { useState } from 'react';
import AnalyticsDashboard from '../components/AnalyticsDashboard';
import SubscriptionAnalytics from '../components/SubscriptionAnalytics';
import CustomerAnalytics from '../components/CustomerAnalytics';
import { BarChart3, Users, TrendingUp, Download } from 'lucide-react';

type TabType = 'dashboard' | 'subscriptions' | 'customers' | 'export';

const AnalyticsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('dashboard');
  const [isExporting, setIsExporting] = useState(false);

  const tabs = [
    {
      id: 'dashboard',
      label: 'Dashboard',
      icon: <BarChart3 className="w-4 h-4" />
    },
    {
      id: 'subscriptions',
      label: 'Subscriptions',
      icon: <TrendingUp className="w-4 h-4" />
    },
    {
      id: 'customers',
      label: 'Customers',
      icon: <Users className="w-4 h-4" />
    },
    {
      id: 'export',
      label: 'Export',
      icon: <Download className="w-4 h-4" />
    }
  ];

  const handleExport = async (format: 'csv' | 'json' | 'pdf') => {
    try {
      setIsExporting(true);
      const response = await fetch('/api/analytics/export', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          format,
          period_days: 30
        })
      });

      if (!response.ok) throw new Error('Export failed');

      const data = await response.json();
      
      if (format === 'json') {
        // Download JSON
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        downloadBlob(blob, `analytics_${new Date().toISOString().split('T')[0]}.json`);
      } else if (format === 'csv') {
        // Download CSV
        const blob = new Blob([data.content], { type: 'text/csv' });
        downloadBlob(blob, data.filename);
      }
    } catch (error) {
      console.error('Export error:', error);
      alert('Failed to export analytics');
    } finally {
      setIsExporting(false);
    }
  };

  const downloadBlob = (blob: Blob, filename: string) => {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  };

  return (
    <div className="min-h-screen bg-gray-100 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Page Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900">Analytics & Reporting</h1>
          <p className="mt-2 text-lg text-gray-600">
            Track revenue, subscriptions, and customer metrics in real-time
          </p>
        </div>

        {/* Tabs Navigation */}
        <div className="bg-white rounded-lg shadow mb-6">
          <div className="flex border-b border-gray-200">
            {tabs.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as TabType)}
                className={`flex-1 px-4 py-4 font-medium text-sm border-b-2 transition-colors flex items-center justify-center gap-2 ${
                  activeTab === tab.id
                    ? 'text-blue-600 border-blue-600'
                    : 'text-gray-600 border-transparent hover:text-gray-900'
                }`}
              >
                {tab.icon}
                {tab.label}
              </button>
            ))}
          </div>

          {/* Tab Content */}
          <div className="p-6">
            {activeTab === 'dashboard' && <AnalyticsDashboard />}
            
            {activeTab === 'subscriptions' && <SubscriptionAnalytics />}
            
            {activeTab === 'customers' && <CustomerAnalytics />}
            
            {activeTab === 'export' && (
              <div className="space-y-6">
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-blue-900 mb-2">Export Analytics Data</h3>
                  <p className="text-blue-800">
                    Download your analytics data in different formats for further analysis and reporting
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {/* CSV Export */}
                  <button
                    onClick={() => handleExport('csv')}
                    disabled={isExporting}
                    className="bg-white border border-gray-300 rounded-lg p-6 hover:bg-gray-50 transition-colors disabled:opacity-50"
                  >
                    <div className="text-3xl font-bold text-green-600 mb-2">CSV</div>
                    <p className="text-gray-600 text-sm mb-4">Comma-separated values</p>
                    <p className="text-xs text-gray-500 mb-4">
                      Compatible with Excel, Google Sheets, and other spreadsheet tools
                    </p>
                    <span className="text-sm font-medium text-green-600">
                      {isExporting ? 'Exporting...' : 'Export as CSV'}
                    </span>
                  </button>

                  {/* JSON Export */}
                  <button
                    onClick={() => handleExport('json')}
                    disabled={isExporting}
                    className="bg-white border border-gray-300 rounded-lg p-6 hover:bg-gray-50 transition-colors disabled:opacity-50"
                  >
                    <div className="text-3xl font-bold text-blue-600 mb-2">JSON</div>
                    <p className="text-gray-600 text-sm mb-4">JavaScript Object Notation</p>
                    <p className="text-xs text-gray-500 mb-4">
                      Perfect for API integrations and programmatic access
                    </p>
                    <span className="text-sm font-medium text-blue-600">
                      {isExporting ? 'Exporting...' : 'Export as JSON'}
                    </span>
                  </button>

                  {/* PDF Export */}
                  <button
                    onClick={() => handleExport('pdf')}
                    disabled={isExporting || true} // Coming soon
                    className="bg-gray-50 border border-gray-300 rounded-lg p-6 cursor-not-allowed opacity-50"
                  >
                    <div className="text-3xl font-bold text-red-600 mb-2">PDF</div>
                    <p className="text-gray-600 text-sm mb-4">Portable Document Format</p>
                    <p className="text-xs text-gray-500 mb-4">
                      Professional reports ready to share with stakeholders
                    </p>
                    <span className="text-sm font-medium text-gray-400">Coming Soon</span>
                  </button>
                </div>

                {/* Export Options */}
                <div className="bg-white border border-gray-200 rounded-lg p-6">
                  <h4 className="font-semibold text-gray-900 mb-4">Export Options</h4>
                  
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Period
                      </label>
                      <select className="w-full px-3 py-2 border border-gray-300 rounded-md text-gray-900 focus:outline-none focus:ring-blue-500 focus:border-blue-500">
                        <option>Last 7 days</option>
                        <option>Last 30 days</option>
                        <option>Last 90 days</option>
                        <option>Last 12 months</option>
                        <option>Custom range</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Metrics to Include
                      </label>
                      <div className="space-y-2">
                        <label className="flex items-center">
                          <input type="checkbox" defaultChecked className="rounded border-gray-300" />
                          <span className="ml-2 text-sm text-gray-700">Revenue Metrics (MRR, ARR, LTV)</span>
                        </label>
                        <label className="flex items-center">
                          <input type="checkbox" defaultChecked className="rounded border-gray-300" />
                          <span className="ml-2 text-sm text-gray-700">Subscription Analytics</span>
                        </label>
                        <label className="flex items-center">
                          <input type="checkbox" defaultChecked className="rounded border-gray-300" />
                          <span className="ml-2 text-sm text-gray-700">Customer Metrics</span>
                        </label>
                        <label className="flex items-center">
                          <input type="checkbox" className="rounded border-gray-300" />
                          <span className="ml-2 text-sm text-gray-700">Cohort Analysis</span>
                        </label>
                        <label className="flex items-center">
                          <input type="checkbox" className="rounded border-gray-300" />
                          <span className="ml-2 text-sm text-gray-700">Churn Predictions</span>
                        </label>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Scheduled Reports */}
                <div className="bg-white border border-gray-200 rounded-lg p-6">
                  <h4 className="font-semibold text-gray-900 mb-4">Scheduled Reports</h4>
                  <p className="text-gray-600 text-sm mb-4">
                    Receive automated analytics reports via email on a regular schedule
                  </p>
                  <button className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-medium text-sm">
                    Set Up Scheduled Reports
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Footer Info */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="font-semibold text-gray-900 mb-3">Analytics Dashboard Information</h3>
          <ul className="space-y-2 text-sm text-gray-600">
            <li>✓ All metrics are updated in real-time from your payment system</li>
            <li>✓ Churn prediction uses machine learning algorithms</li>
            <li>✓ Cohort analysis tracks customer retention by signup period</li>
            <li>✓ Revenue forecasts are based on 90-day historical trends</li>
            <li>✓ Data is automatically aggregated hourly for performance</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsPage;
