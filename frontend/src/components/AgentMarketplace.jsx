import React, { useState, useEffect } from 'react';
import {
  Search, Star, Download, Filter, TrendingUp, Tag, Clock,
  DollarSign, CheckCircle, AlertCircle, Eye
} from 'lucide-react';
import '../styles/marketplace.css';

const AgentMarketplace = () => {
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [featured, setFeatured] = useState([]);
  const [trending, setTrending] = useState([]);
  
  // Search & Filter
  const [searchQuery, setSearchQuery] = useState('');
  const [category, setCategory] = useState('all');
  const [sortBy, setSortBy] = useState('rating');
  const [minRating, setMinRating] = useState(0);
  const [isPaidOnly, setIsPaidOnly] = useState(false);
  
  // Pagination
  const [limit, setLimit] = useState(20);
  const [offset, setOffset] = useState(0);
  const [totalCount, setTotalCount] = useState(0);
  
  // UI State
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [showFilters, setShowFilters] = useState(false);
  const [viewMode, setViewMode] = useState('grid'); // grid or list

  const categories = [
    { id: 'all', label: 'All Categories' },
    { id: 'coding', label: 'Coding' },
    { id: 'analysis', label: 'Analysis' },
    { id: 'automation', label: 'Automation' },
    { id: 'content', label: 'Content' },
    { id: 'research', label: 'Research' }
  ];

  const sortOptions = [
    { id: 'rating', label: 'Top Rated' },
    { id: 'downloads', label: 'Most Downloaded' },
    { id: 'trending', label: 'Trending' },
    { id: 'newest', label: 'Newest' }
  ];

  // Fetch featured agents
  useEffect(() => {
    fetchFeatured();
    fetchTrending();
  }, []);

  // Fetch search results
  useEffect(() => {
    if (offset === 0) {
      fetchAgents();
    }
  }, [searchQuery, category, sortBy, minRating, isPaidOnly]);

  const fetchFeatured = async () => {
    try {
      const response = await fetch('/api/v1/agents/featured?limit=6');
      const data = await response.json();
      setFeatured(data.agents || []);
    } catch (error) {
      console.error('Error fetching featured agents:', error);
    }
  };

  const fetchTrending = async () => {
    try {
      const response = await fetch('/api/v1/agents/trending?limit=6&days=30');
      const data = await response.json();
      setTrending(data.agents || []);
    } catch (error) {
      console.error('Error fetching trending agents:', error);
    }
  };

  const fetchAgents = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        query: searchQuery,
        category: category === 'all' ? '' : category,
        sort_by: sortBy,
        min_rating: minRating,
        is_paid_only: isPaidOnly,
        limit,
        offset: 0
      });

      const response = await fetch(`/api/v1/agents/search?${params}`);
      const data = await response.json();
      setAgents(data.agents || []);
      setTotalCount(data.total_count || 0);
      setOffset(0);
    } catch (error) {
      console.error('Error fetching agents:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadMore = async () => {
    try {
      const params = new URLSearchParams({
        query: searchQuery,
        category: category === 'all' ? '' : category,
        sort_by: sortBy,
        min_rating: minRating,
        is_paid_only: isPaidOnly,
        limit,
        offset: offset + limit
      });

      const response = await fetch(`/api/v1/agents/search?${params}`);
      const data = await response.json();
      setAgents([...agents, ...data.agents]);
      setOffset(offset + limit);
    } catch (error) {
      console.error('Error loading more agents:', error);
    }
  };

  const AgentCard = ({ agent }) => (
    <div className="agent-card" onClick={() => setSelectedAgent(agent)}>
      <div className="agent-header">
        {agent.icon_url ? (
          <img src={agent.icon_url} alt={agent.name} className="agent-icon" />
        ) : (
          <div className="agent-icon-placeholder">{agent.name[0]}</div>
        )}
        {agent.is_verified && <CheckCircle size={20} className="verified-badge" />}
      </div>

      <h3 className="agent-name">{agent.name}</h3>
      
      <p className="agent-description">{agent.description}</p>

      <div className="agent-meta">
        <div className="rating">
          <Star size={16} fill="currentColor" />
          <span>{agent.average_rating.toFixed(1)}</span>
        </div>
        <div className="downloads">
          <Download size={16} />
          <span>{(agent.downloads / 1000).toFixed(1)}K</span>
        </div>
        {agent.category && (
          <Tag size={16} className="category-tag">{agent.category}</Tag>
        )}
      </div>

      <div className="agent-footer">
        {agent.is_paid && (
          <div className="price-badge">
            <DollarSign size={14} />
            <span>${agent.price}</span>
          </div>
        )}
        <button className="deploy-btn">Deploy</button>
      </div>
    </div>
  );

  const AgentListItem = ({ agent }) => (
    <div className="agent-list-item" onClick={() => setSelectedAgent(agent)}>
      <div className="list-icon-col">
        {agent.icon_url ? (
          <img src={agent.icon_url} alt={agent.name} className="list-icon" />
        ) : (
          <div className="list-icon-placeholder">{agent.name[0]}</div>
        )}
      </div>

      <div className="list-info-col">
        <div className="list-name">
          <h4>{agent.name}</h4>
          {agent.is_verified && <CheckCircle size={16} className="verified" />}
        </div>
        <p className="list-description">{agent.description}</p>
        <div className="list-tags">
          {agent.tags?.slice(0, 3).map(tag => (
            <span key={tag} className="tag">{tag}</span>
          ))}
        </div>
      </div>

      <div className="list-stats-col">
        <div className="stat">
          <Star size={14} />
          <span>{agent.average_rating.toFixed(1)}</span>
        </div>
        <div className="stat">
          <Download size={14} />
          <span>{(agent.downloads / 1000).toFixed(1)}K</span>
        </div>
        <div className="stat">
          <Eye size={14} />
          <span>{(agent.deployments / 1000).toFixed(1)}K</span>
        </div>
      </div>

      <div className="list-action">
        {agent.is_paid && <span className="price">${agent.price}</span>}
        <button className="deploy-btn">Deploy</button>
      </div>
    </div>
  );

  return (
    <div className="agent-marketplace">
      {/* Header */}
      <div className="marketplace-header">
        <h1>AI Agent Marketplace</h1>
        <p>Discover and deploy powerful AI agents for your workflows</p>
      </div>

      {/* Featured Agents Carousel */}
      {featured.length > 0 && (
        <section className="featured-section">
          <h2>Featured Agents</h2>
          <div className="featured-carousel">
            {featured.map(agent => (
              <div key={agent.id} className="featured-card">
                <div className="featured-badge">Featured</div>
                <h3>{agent.name}</h3>
                <p>{agent.description}</p>
                <div className="featured-rating">
                  <Star size={18} fill="currentColor" />
                  <span>{agent.average_rating.toFixed(1)}</span>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Trending Agents Section */}
      {trending.length > 0 && (
        <section className="trending-section">
          <div className="section-header">
            <h2><TrendingUp size={24} /> Trending Now</h2>
            <p>Most popular agents this month</p>
          </div>
          <div className="trending-grid">
            {trending.map(agent => (
              <div key={agent.id} className="trending-card">
                <span className="trending-badge">🔥 Trending</span>
                <h4>{agent.name}</h4>
                <p>{agent.description}</p>
                <div className="trending-stats">
                  <span>{agent.deployments} active deployments</span>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Search & Filter Section */}
      <section className="search-section">
        <div className="search-bar">
          <Search size={20} />
          <input
            type="text"
            placeholder="Search agents by name, capability, or description..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="search-input"
          />
        </div>

        <button
          className={`filter-toggle ${showFilters ? 'active' : ''}`}
          onClick={() => setShowFilters(!showFilters)}
        >
          <Filter size={20} />
          Filters
        </button>

        {showFilters && (
          <div className="filter-panel">
            <div className="filter-group">
              <label>Category</label>
              <select value={category} onChange={(e) => setCategory(e.target.value)}>
                {categories.map(cat => (
                  <option key={cat.id} value={cat.id}>{cat.label}</option>
                ))}
              </select>
            </div>

            <div className="filter-group">
              <label>Sort By</label>
              <select value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
                {sortOptions.map(opt => (
                  <option key={opt.id} value={opt.id}>{opt.label}</option>
                ))}
              </select>
            </div>

            <div className="filter-group">
              <label>Minimum Rating: {minRating.toFixed(1)}</label>
              <input
                type="range"
                min="0"
                max="5"
                step="0.5"
                value={minRating}
                onChange={(e) => setMinRating(parseFloat(e.target.value))}
                className="rating-slider"
              />
            </div>

            <div className="filter-group checkbox">
              <input
                type="checkbox"
                id="paid-only"
                checked={isPaidOnly}
                onChange={(e) => setIsPaidOnly(e.target.checked)}
              />
              <label htmlFor="paid-only">Paid Agents Only</label>
            </div>
          </div>
        )}

        <div className="view-toggle">
          <button
            className={`view-btn ${viewMode === 'grid' ? 'active' : ''}`}
            onClick={() => setViewMode('grid')}
          >
            Grid
          </button>
          <button
            className={`view-btn ${viewMode === 'list' ? 'active' : ''}`}
            onClick={() => setViewMode('list')}
          >
            List
          </button>
        </div>
      </section>

      {/* Results */}
      <section className="results-section">
        <div className="results-header">
          <h2>
            {searchQuery || category !== 'all'
              ? `Search Results${searchQuery ? ` for "${searchQuery}"` : ''}`
              : 'All Agents'}
          </h2>
          <p>{totalCount} agents found</p>
        </div>

        {loading && <div className="loading">Loading agents...</div>}

        {!loading && agents.length === 0 && (
          <div className="no-results">
            <AlertCircle size={48} />
            <h3>No agents found</h3>
            <p>Try adjusting your search criteria</p>
          </div>
        )}

        <div className={`agents-${viewMode}`}>
          {agents.map(agent => (
            viewMode === 'grid' ? (
              <AgentCard key={agent.id} agent={agent} />
            ) : (
              <AgentListItem key={agent.id} agent={agent} />
            )
          ))}
        </div>

        {agents.length > 0 && offset + limit < totalCount && (
          <button className="load-more-btn" onClick={loadMore}>
            Load More Agents
          </button>
        )}
      </section>

      {/* Agent Detail Modal */}
      {selectedAgent && (
        <div className="modal-overlay" onClick={() => setSelectedAgent(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close" onClick={() => setSelectedAgent(null)}>×</button>
            
            <div className="modal-header">
              {selectedAgent.icon_url && (
                <img src={selectedAgent.icon_url} alt={selectedAgent.name} />
              )}
              <h2>{selectedAgent.name}</h2>
            </div>

            <div className="modal-body">
              <p>{selectedAgent.full_description || selectedAgent.description}</p>

              <div className="modal-specs">
                <div className="spec">
                  <strong>Type:</strong> {selectedAgent.agent_type}
                </div>
                <div className="spec">
                  <strong>Model:</strong> {selectedAgent.model_name}
                </div>
                <div className="spec">
                  <strong>Capabilities:</strong>
                  <div className="capabilities-list">
                    {selectedAgent.capabilities?.map(cap => (
                      <span key={cap} className="capability-badge">{cap}</span>
                    ))}
                  </div>
                </div>
              </div>

              <div className="modal-actions">
                <button className="btn-primary">Deploy Agent</button>
                <button className="btn-secondary">Clone & Customize</button>
                <button className="btn-secondary">View Documentation</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AgentMarketplace;
