import React, { useState, useEffect } from 'react';
import { Search, Star, Download, Eye, TrendingUp, Filter } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const MarketplaceExplorer = () => {
  const [view, setView] = useState('featured');
  const [templates, setTemplates] = useState([]);
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState('popular');
  const [loading, setLoading] = useState(false);

  // Sample data for demo
  const sampleTemplates = [
    {
      id: '1',
      name: 'Email Marketing Automation',
      author: 'Sarah Chen',
      rating: 4.8,
      reviews: 156,
      downloads: 2840,
      icon: '📧',
      tags: ['automation', 'email'],
      price: 0,
      featured: true
    },
    {
      id: '2',
      name: 'Social Media Poster',
      author: 'Alex Rivera',
      rating: 4.6,
      reviews: 98,
      downloads: 1560,
      icon: '📱',
      tags: ['social', 'marketing'],
      price: 0,
      featured: true
    },
    {
      id: '3',
      name: 'Data Pipeline Builder',
      author: 'Jordan Kim',
      rating: 4.9,
      reviews: 234,
      downloads: 3420,
      icon: '📊',
      tags: ['data', 'pipeline'],
      price: 29,
      featured: true
    },
    {
      id: '4',
      name: 'Content Calendar Manager',
      author: 'Emma Stone',
      rating: 4.5,
      reviews: 87,
      downloads: 980,
      icon: '📅',
      tags: ['content', 'calendar'],
      price: 0
    },
    {
      id: '5',
      name: 'Customer Segmentation',
      author: 'Mike Johnson',
      rating: 4.7,
      reviews: 145,
      downloads: 2100,
      icon: '👥',
      tags: ['analytics', 'crm'],
      price: 49
    }
  ];

  const sampleCategories = [
    { id: '1', name: 'Automation', icon: '⚙️', count: 245 },
    { id: '2', name: 'Marketing', icon: '📢', count: 189 },
    { id: '3', name: 'Analytics', icon: '📊', count: 156 },
    { id: '4', name: 'Content', icon: '✍️', count: 134 },
    { id: '5', name: 'Team Tools', icon: '👨‍💼', count: 112 }
  ];

  useEffect(() => {
    setCategories(sampleCategories);
    setTemplates(sampleTemplates);
  }, []);

  const handleSearch = () => {
    setLoading(true);
    setTimeout(() => {
      const filtered = sampleTemplates.filter(t =>
        t.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        t.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
      );
      setTemplates(filtered);
      setLoading(false);
    }, 300);
  };

  const handleSort = (value) => {
    setSortBy(value);
    let sorted = [...templates];
    if (value === 'popular') {
      sorted.sort((a, b) => b.downloads - a.downloads);
    } else if (value === 'rating') {
      sorted.sort((a, b) => b.rating - a.rating);
    } else if (value === 'newest') {
      sorted.reverse();
    }
    setTemplates(sorted);
  };

  const TemplateCard = ({ template }) => (
    <div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
      <div className="flex items-start justify-between mb-3">
        <div className="text-4xl">{template.icon}</div>
        {template.featured && (
          <span className="bg-yellow-100 text-yellow-800 text-xs px-2 py-1 rounded-full">⭐ Featured</span>
        )}
      </div>
      
      <h3 className="text-lg font-bold mb-2">{template.name}</h3>
      <p className="text-sm text-gray-600 mb-3">by {template.author}</p>
      
      <div className="flex gap-2 mb-3 flex-wrap">
        {template.tags.map(tag => (
          <span key={tag} className="bg-blue-100 text-blue-700 text-xs px-2 py-1 rounded">
            {tag}
          </span>
        ))}
      </div>
      
      <div className="flex items-center gap-4 text-sm text-gray-700 mb-4">
        <div className="flex items-center gap-1">
          <Star className="w-4 h-4 fill-yellow-400 text-yellow-400" />
          <span>{template.rating} ({template.reviews})</span>
        </div>
        <div className="flex items-center gap-1">
          <Download className="w-4 h-4" />
          <span>{template.downloads}</span>
        </div>
      </div>
      
      <div className="flex gap-2">
        <button className="flex-1 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium">
          {template.price > 0 ? `$${template.price}` : 'Get Free'}
        </button>
        <button className="flex-1 border border-gray-300 py-2 rounded-lg hover:bg-gray-50 transition-colors text-sm font-medium">
          Fork
        </button>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 p-6">
        <h1 className="text-3xl font-bold mb-4">Workflow Marketplace</h1>
        
        {/* Search Bar */}
        <div className="flex gap-2 mb-6">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-3 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search templates, authors, tags..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <button
            onClick={handleSearch}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Search
          </button>
        </div>

        {/* Filter Tabs */}
        <div className="flex gap-2 overflow-x-auto pb-2">
          {['featured', 'trending', 'all'].map(tab => (
            <button
              key={tab}
              onClick={() => setView(tab)}
              className={`px-4 py-2 rounded-lg whitespace-nowrap text-sm font-medium transition-colors ${
                view === tab
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>
      </div>

      <div className="max-w-7xl mx-auto p-6">
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          {/* Sidebar - Categories */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-md p-4 sticky top-6">
              <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                <Filter className="w-5 h-5" />
                Categories
              </h3>
              <div className="space-y-2">
                <button
                  onClick={() => setSelectedCategory(null)}
                  className={`w-full text-left px-3 py-2 rounded transition-colors ${
                    selectedCategory === null
                      ? 'bg-blue-100 text-blue-700 font-medium'
                      : 'hover:bg-gray-100'
                  }`}
                >
                  All Templates
                </button>
                {categories.map(cat => (
                  <button
                    key={cat.id}
                    onClick={() => setSelectedCategory(cat.id)}
                    className={`w-full text-left px-3 py-2 rounded transition-colors ${
                      selectedCategory === cat.id
                        ? 'bg-blue-100 text-blue-700 font-medium'
                        : 'hover:bg-gray-100'
                    }`}
                  >
                    <div className="flex justify-between items-center">
                      <span>{cat.icon} {cat.name}</span>
                      <span className="text-xs text-gray-500">{cat.count}</span>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-4">
            {/* Sort Options */}
            <div className="mb-6 flex justify-between items-center">
              <p className="text-gray-700">
                {loading ? 'Searching...' : `Showing ${templates.length} templates`}
              </p>
              <select
                value={sortBy}
                onChange={(e) => handleSort(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="popular">Most Popular</option>
                <option value="rating">Highest Rated</option>
                <option value="newest">Newest First</option>
              </select>
            </div>

            {/* Templates Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {templates.map(template => (
                <TemplateCard key={template.id} template={template} />
              ))}
            </div>

            {templates.length === 0 && (
              <div className="bg-white rounded-lg shadow-md p-12 text-center">
                <p className="text-gray-600 mb-4">No templates found</p>
                <button
                  onClick={() => {
                    setSearchQuery('');
                    setTemplates(sampleTemplates);
                  }}
                  className="text-blue-600 hover:underline"
                >
                  Clear filters
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MarketplaceExplorer;
