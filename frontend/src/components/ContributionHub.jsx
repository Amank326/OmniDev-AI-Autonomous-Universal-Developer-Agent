import React, { useState, useEffect } from 'react';
import { TrendingUp, Award, Zap, DollarSign, Users, BarChart3, CheckCircle, Clock } from 'lucide-react';
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

const ContributionHub = () => {
  const [activeTab, setActiveTab] = useState('submit');
  const [templates, setTemplates] = useState([]);
  const [earnings, setEarnings] = useState({});
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    category: '',
    tags: [],
    isPaid: false,
    price: 0
  });

  // Sample data
  useEffect(() => {
    setTemplates([
      {
        id: '1',
        name: 'Email Marketing Automation',
        status: 'published',
        rating: 4.8,
        downloads: 2840,
        earnings: 12450.50,
        revenue: 24901,
        qualityScore: 89,
        trendingScore: 87,
        featured: true,
        created: '3 months ago'
      },
      {
        id: '2',
        name: 'Data Pipeline Builder',
        status: 'published',
        rating: 4.9,
        downloads: 3420,
        earnings: 18920.75,
        revenue: 37841.5,
        qualityScore: 95,
        trendingScore: 92,
        featured: true,
        created: '5 months ago'
      },
      {
        id: '3',
        name: 'Social Media Scheduler',
        status: 'draft',
        rating: 0,
        downloads: 0,
        earnings: 0,
        revenue: 0,
        qualityScore: 72,
        trendingScore: 0,
        featured: false,
        created: '2 days ago'
      }
    ]);

    setEarnings({
      totalEarnings: 31371.25,
      totalDownloads: 6260,
      totalTemplates: 3,
      monthlyData: [
        { month: 'Jan', earnings: 1200, downloads: 120 },
        { month: 'Feb', earnings: 2850, downloads: 285 },
        { month: 'Mar', earnings: 4200, downloads: 420 },
        { month: 'Apr', earnings: 6500, downloads: 650 },
        { month: 'May', earnings: 8920, downloads: 892 },
        { month: 'Jun', earnings: 12100, downloads: 1210 }
      ],
      earningsByTemplate: [
        { name: 'Email Marketing', value: 12450.50 },
        { name: 'Data Pipeline', value: 18920.75 }
      ]
    });
  }, []);

  const handleSubmitTemplate = (e) => {
    e.preventDefault();
    alert('Template submitted! Your workflow will be reviewed shortly.');
    setFormData({ name: '', description: '', category: '', tags: [], isPaid: false, price: 0 });
  };

  const QualityIndicator = ({ score, size = 'md' }) => {
    const color = score >= 85 ? 'text-green-600' : score >= 70 ? 'text-yellow-600' : 'text-red-600';
    const bgColor = score >= 85 ? 'bg-green-50' : score >= 70 ? 'bg-yellow-50' : 'bg-red-50';
    const sizeClass = size === 'lg' ? 'w-16 h-16' : 'w-10 h-10';
    
    return (
      <div className={`flex items-center justify-center rounded-full ${bgColor} ${sizeClass}`}>
        <span className={`${color} font-bold text-sm`}>{score}</span>
      </div>
    );
  };

  const TemplateCard = ({ template }) => (
    <div className="bg-white rounded-lg shadow-md p-6 mb-4">
      <div className="flex items-start justify-between mb-4">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <h3 className="font-bold text-lg">{template.name}</h3>
            <span className={`text-xs px-2 py-1 rounded ${
              template.status === 'published' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
            }`}>
              {template.status}
            </span>
            {template.featured && <Award className="w-4 h-4 text-yellow-500" />}
          </div>
          <p className="text-gray-600 text-sm">Created {template.created}</p>
        </div>
        <QualityIndicator score={template.qualityScore} />
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
        <div className="bg-gray-50 p-3 rounded">
          <p className="text-xs text-gray-600 mb-1">Quality Score</p>
          <p className="font-bold text-lg">{template.qualityScore}%</p>
        </div>
        <div className="bg-gray-50 p-3 rounded">
          <p className="text-xs text-gray-600 mb-1">Trending Score</p>
          <p className="font-bold text-lg">{template.trendingScore}%</p>
        </div>
        <div className="bg-gray-50 p-3 rounded">
          <p className="text-xs text-gray-600 mb-1">Downloads</p>
          <p className="font-bold text-lg">{template.downloads}</p>
        </div>
        <div className="bg-blue-50 p-3 rounded">
          <p className="text-xs text-gray-600 mb-1">Your Earnings</p>
          <p className="font-bold text-lg text-blue-600">${template.earnings.toFixed(2)}</p>
        </div>
      </div>

      {template.status === 'published' && (
        <div className="mb-4 p-3 bg-blue-50 rounded border border-blue-200">
          <p className="text-xs font-medium text-blue-700">
            ✓ Featured on marketplace • {template.downloads} downloads • {template.rating}⭐ rating
          </p>
        </div>
      )}

      <div className="flex gap-2">
        {template.status === 'draft' && (
          <>
            <button className="flex-1 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium">
              Publish
            </button>
            <button className="flex-1 border border-gray-300 py-2 rounded-lg hover:bg-gray-50 transition-colors text-sm font-medium">
              Preview
            </button>
          </>
        )}
        {template.status === 'published' && (
          <>
            <button className="flex-1 bg-gray-600 text-white py-2 rounded-lg hover:bg-gray-700 transition-colors text-sm font-medium">
              Analytics
            </button>
            <button className="flex-1 border border-gray-300 py-2 rounded-lg hover:bg-gray-50 transition-colors text-sm font-medium">
              Edit
            </button>
          </>
        )}
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-6">
        <div className="max-w-6xl mx-auto">
          <h1 className="text-3xl font-bold mb-2">Contribution Hub</h1>
          <p className="text-gray-600 mb-6">Build, publish, and monetize your workflows</p>

          {/* Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-blue-50 p-4 rounded-lg">
              <div className="flex items-center gap-3">
                <DollarSign className="w-8 h-8 text-blue-600" />
                <div>
                  <p className="text-xs text-gray-600">Total Earnings</p>
                  <p className="text-2xl font-bold">${earnings.totalEarnings?.toFixed(2)}</p>
                </div>
              </div>
            </div>
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="flex items-center gap-3">
                <TrendingUp className="w-8 h-8 text-green-600" />
                <div>
                  <p className="text-xs text-gray-600">Total Downloads</p>
                  <p className="text-2xl font-bold">{earnings.totalDownloads}</p>
                </div>
              </div>
            </div>
            <div className="bg-purple-50 p-4 rounded-lg">
              <div className="flex items-center gap-3">
                <Zap className="w-8 h-8 text-purple-600" />
                <div>
                  <p className="text-xs text-gray-600">Published</p>
                  <p className="text-2xl font-bold">2</p>
                </div>
              </div>
            </div>
            <div className="bg-orange-50 p-4 rounded-lg">
              <div className="flex items-center gap-3">
                <Award className="w-8 h-8 text-orange-600" />
                <div>
                  <p className="text-xs text-gray-600">Featured</p>
                  <p className="text-2xl font-bold">2</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto p-6">
        {/* Tabs */}
        <div className="flex gap-4 mb-6 border-b border-gray-200">
          <button
            onClick={() => setActiveTab('submit')}
            className={`px-4 py-2 font-medium border-b-2 transition-colors ${
              activeTab === 'submit'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-600 hover:text-gray-800'
            }`}
          >
            Submit Template
          </button>
          <button
            onClick={() => setActiveTab('templates')}
            className={`px-4 py-2 font-medium border-b-2 transition-colors ${
              activeTab === 'templates'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-600 hover:text-gray-800'
            }`}
          >
            My Templates
          </button>
          <button
            onClick={() => setActiveTab('earnings')}
            className={`px-4 py-2 font-medium border-b-2 transition-colors ${
              activeTab === 'earnings'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-600 hover:text-gray-800'
            }`}
          >
            Earnings Analytics
          </button>
        </div>

        {/* Submit Tab */}
        {activeTab === 'submit' && (
          <div className="bg-white rounded-lg shadow-md p-6 max-w-2xl">
            <h2 className="text-2xl font-bold mb-6">Submit New Template</h2>
            
            <form onSubmit={handleSubmitTemplate} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Template Name *
                </label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g., Email Marketing Automation"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Description *
                </label>
                <textarea
                  required
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Describe what your workflow does..."
                  rows={4}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Category *
                </label>
                <select
                  required
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select a category</option>
                  <option value="automation">Automation</option>
                  <option value="marketing">Marketing</option>
                  <option value="analytics">Analytics</option>
                  <option value="content">Content</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Tags
                </label>
                <input
                  type="text"
                  placeholder="Comma-separated tags (e.g., email, automation, free)"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="space-y-2">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.isPaid}
                    onChange={(e) => setFormData({ ...formData, isPaid: e.target.checked })}
                    className="rounded"
                  />
                  <span className="text-sm font-medium">This is a paid template</span>
                </label>
                
                {formData.isPaid && (
                  <div className="ml-6">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Price ($)
                    </label>
                    <input
                      type="number"
                      min="1"
                      step="0.01"
                      value={formData.price}
                      onChange={(e) => setFormData({ ...formData, price: parseFloat(e.target.value) })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                )}
              </div>

              <div className="bg-blue-50 border border-blue-200 p-4 rounded-lg mt-6">
                <p className="text-sm text-blue-700">
                  <strong>Revenue Sharing:</strong> You earn 50% of each purchase. Platform takes 30%, referrers get 20%.
                </p>
              </div>

              <button
                type="submit"
                className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition-colors font-medium mt-6"
              >
                Submit Template for Review
              </button>
            </form>
          </div>
        )}

        {/* Templates Tab */}
        {activeTab === 'templates' && (
          <div>
            {templates.map(template => (
              <TemplateCard key={template.id} template={template} />
            ))}
          </div>
        )}

        {/* Earnings Tab */}
        {activeTab === 'earnings' && (
          <div className="space-y-6">
            {/* Monthly Earnings Chart */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-bold mb-4">Monthly Earnings</h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={earnings.monthlyData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="earnings" stroke="#3b82f6" strokeWidth={2} />
                  <Line type="monotone" dataKey="downloads" stroke="#10b981" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Earnings by Template */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h3 className="text-xl font-bold mb-4">Earnings by Template</h3>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie data={earnings.earningsByTemplate} dataKey="value" cx="50%" cy="50%" outerRadius={100} label>
                    <Cell fill="#3b82f6" />
                    <Cell fill="#10b981" />
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ContributionHub;
