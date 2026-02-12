/**
 * Phase 26: Shared Insights Feed Component
 * Real-time insights feed with reactions, comments, consensus scoring
 */

import React, { useState, useEffect, useCallback } from 'react';

const SharedInsightsFeed = ({ workspaceId, userId, apiBaseUrl = 'http://localhost:5000' }) => {
  // Data state
  const [insights, setInsights] = useState([]);
  const [trendingInsights, setTrendingInsights] = useState([]);
  const [loading, setLoading] = useState(false);
  
  // UI state
  const [activeTab, setActiveTab] = useState('recent');
  const [expandedInsight, setExpandedInsight] = useState(null);
  const [showComments, setShowComments] = useState({});
  const [newComment, setNewComment] = useState({});
  const [userReactions, setUserReactions] = useState({});
  
  // Filter & Sort
  const [sortBy, setSortBy] = useState('recent');
  const [filterSeverity, setFilterSeverity] = useState('all');


  // ========================================================================
  // LIFECYCLE
  // ========================================================================

  useEffect(() => {
    loadInsightFeed();
    loadTrendingInsights();
  }, [workspaceId]);


  // ========================================================================
  // DATA LOADING
  // ========================================================================

  const loadInsightFeed = useCallback(async () => {
    try {
      setLoading(true);
      const response = await fetch(
        `${apiBaseUrl}/api/v1/collaboration/workspaces/${workspaceId}/insight-feed?limit=20&sort=${sortBy}`
      );
      const data = await response.json();
      setInsights(data.insights || []);
    } catch (error) {
      console.error('Failed to load insights:', error);
    } finally {
      setLoading(false);
    }
  }, [workspaceId, sortBy, apiBaseUrl]);

  const loadTrendingInsights = useCallback(async () => {
    try {
      const response = await fetch(
        `${apiBaseUrl}/api/v1/collaboration/workspaces/${workspaceId}/trending-insights?limit=5`
      );
      const data = await response.json();
      setTrendingInsights(data.insights || []);
    } catch (error) {
      console.error('Failed to load trending insights:', error);
    }
  }, [workspaceId, apiBaseUrl]);


  // ========================================================================
  // REACTIONS & CONSENSUS
  // ========================================================================

  const reactionTypes = [
    { type: 'thumbs_up', emoji: '👍', label: 'Agree' },
    { type: 'thumbs_down', emoji: '👎', label: 'Disagree' },
    { type: 'lightbulb', emoji: '💡', label: 'Insightful' },
    { type: 'warning', emoji: '⚠️', label: 'Important' },
    { type: 'fire', emoji: '🔥', label: 'Critical' },
    { type: 'thinking', emoji: '🤔', label: 'Interesting' }
  ];

  const handleAddReaction = useCallback(async (insightId, reactionType) => {
    try {
      const response = await fetch(
        `${apiBaseUrl}/api/v1/collaboration/insights/${insightId}/reactions`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_id: userId,
            reaction_type: reactionType
          })
        }
      );
      
      if (response.ok) {
        // Update local state
        const newReactions = { ...userReactions };
        if (!newReactions[insightId]) newReactions[insightId] = [];
        newReactions[insightId].push(reactionType);
        setUserReactions(newReactions);
        
        // Reload insights to get updated reactions
        loadInsightFeed();
      }
    } catch (error) {
      console.error('Failed to add reaction:', error);
    }
  }, [userId, apiBaseUrl, userReactions, loadInsightFeed]);

  const calculateConsensusScore = (reactions) => {
    if (!reactions) return 0;
    const agree = reactions.filter(r => r.type === 'thumbs_up').length;
    const disagree = reactions.filter(r => r.type === 'thumbs_down').length;
    const total = Object.values(reactions).reduce((sum, r) => sum + r.length, 0);
    
    if (total === 0) return 0;
    return ((agree - disagree) / total);
  };

  const getConsensusColor = (score) => {
    if (score > 0.5) return '#2ecc71'; // Strong agreement
    if (score > 0) return '#f39c12'; // Some agreement
    if (score === 0) return '#bdc3c7'; // Neutral
    return '#e74c3c'; // Disagreement
  };


  // ========================================================================
  // COMMENTS
  // ========================================================================

  const handleAddComment = useCallback(async (insightId) => {
    const comment = newComment[insightId];
    if (!comment || !comment.trim()) return;

    try {
      const response = await fetch(
        `${apiBaseUrl}/api/v1/collaboration/insights/${insightId}/comments`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_id: userId,
            text: comment
          })
        }
      );

      if (response.ok) {
        const updatedComment = { ...newComment };
        delete updatedComment[insightId];
        setNewComment(updatedComment);
        loadInsightFeed();
      }
    } catch (error) {
      console.error('Failed to add comment:', error);
    }
  }, [userId, newComment, apiBaseUrl, loadInsightFeed]);

  const getCommentCount = (insight) => {
    return insight.comments ? insight.comments.length : 0;
  };


  // ========================================================================
  // RENDER: TRENDING SIDEBAR
  // ========================================================================

  const renderTrendingSidebar = () => {
    return (
      <div style={{
        width: '280px',
        backgroundColor: '#f5f5f5',
        padding: '20px',
        borderLeft: '1px solid #ddd',
        maxHeight: 'calc(100vh - 80px)',
        overflowY: 'auto'
      }}>
        <h3 style={{ marginTop: 0, marginBottom: '15px' }}>Trending</h3>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {trendingInsights.map(insight => (
            <div
              key={insight.id}
              onClick={() => {
                setExpandedInsight(insight.id);
                setActiveTab('recent');
              }}
              style={{
                padding: '12px',
                backgroundColor: 'white',
                borderRadius: '6px',
                cursor: 'pointer',
                borderLeft: '3px solid #f39c12',
                transition: 'all 0.2s',
                ':hover': {
                  backgroundColor: '#f9f9f9'
                }
              }}
            >
              <div style={{
                fontSize: '12px',
                fontWeight: '600',
                marginBottom: '4px',
                color: '#2c3e50'
              }}>
                {insight.title || 'Unnamed Insight'}
              </div>
              <div style={{
                fontSize: '11px',
                color: '#999',
                marginBottom: '6px'
              }}>
                {insight.total_reactions || 0} reactions
              </div>
              <div style={{
                display: 'flex',
                gap: '3px',
                flexWrap: 'wrap'
              }}>
                {reactionTypes.map(r => {
                  const count = insight.reactions?.[r.type] || 0;
                  return count > 0 ? (
                    <span
                      key={r.type}
                      style={{
                        fontSize: '10px',
                        backgroundColor: '#e8e8e8',
                        padding: '2px 6px',
                        borderRadius: '3px'
                      }}
                    >
                      {r.emoji} {count}
                    </span>
                  ) : null;
                })}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };


  // ========================================================================
  // RENDER: INSIGHT CARD
  // ========================================================================

  const renderInsightCard = (insight) => {
    const consensusScore = calculateConsensusScore(insight.reactions);
    const reactionCounts = insight.reactions || {};
    const totalReactions = Object.values(reactionCounts).reduce((sum, r) => sum + r, 0);
    const commentCount = getCommentCount(insight);
    const isExpanded = expandedInsight === insight.id;

    return (
      <div
        key={insight.id}
        style={{
          backgroundColor: 'white',
          borderRadius: '8px',
          marginBottom: '15px',
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
          overflow: 'hidden',
          transition: 'all 0.2s'
        }}
      >
        {/* Header */}
        <div style={{
          padding: '16px',
          borderBottom: isExpanded ? '1px solid #eee' : 'none',
          cursor: 'pointer',
          backgroundColor: isExpanded ? '#f9f9f9' : 'white'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
            <div style={{ flex: 1 }}>
              <h3 style={{ margin: '0 0 8px 0', fontSize: '16px' }}>
                {insight.title || 'Unnamed Insight'}
              </h3>
              <div style={{ fontSize: '13px', color: '#666', marginBottom: '8px' }}>
                {insight.description || insight.content}
              </div>
              <div style={{ fontSize: '11px', color: '#999' }}>
                By {insight.created_by} • {insight.created_at}
              </div>
            </div>

            {/* Consensus Badge */}
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              marginLeft: '15px'
            }}>
              <div style={{
                fontSize: '24px',
                fontWeight: 'bold',
                color: getConsensusColor(consensusScore),
                textAlign: 'center'
              }}>
                {(consensusScore * 100).toFixed(0)}%
              </div>
              <div style={{ fontSize: '10px', color: '#999' }}>
                Consensus
              </div>
            </div>
          </div>
        </div>

        {/* Reactions Bar */}
        <div style={{
          padding: '12px 16px',
          backgroundColor: '#fafafa',
          borderBottom: isExpanded ? '1px solid #eee' : 'none',
          display: 'flex',
          gap: '6px',
          flexWrap: 'wrap'
        }}>
          {reactionTypes.map(reaction => {
            const count = reactionCounts[reaction.type] || 0;
            const userHasReacted = userReactions[insight.id]?.includes(reaction.type);

            return (
              <button
                key={reaction.type}
                onClick={() => handleAddReaction(insight.id, reaction.type)}
                style={{
                  padding: '6px 10px',
                  backgroundColor: userHasReacted ? '#e8f4f8' : '#f0f0f0',
                  border: userHasReacted ? '1px solid #3498db' : '1px solid #ddd',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '12px',
                  color: userHasReacted ? '#3498db' : '#666',
                  fontWeight: userHasReacted ? '600' : '400',
                  transition: 'all 0.2s'
                }}
              >
                {reaction.emoji} {count > 0 ? count : ''}
              </button>
            );
          })}
        </div>

        {/* Comments Section (Expanded) */}
        {isExpanded && (
          <div style={{ padding: '16px', borderTop: '1px solid #eee' }}>
            {/* Comments */}
            <div style={{ marginBottom: '15px' }}>
              <h4 style={{ margin: '0 0 12px 0', fontSize: '13px' }}>
                Comments ({commentCount})
              </h4>

              {insight.comments && insight.comments.map(comment => (
                <div
                  key={comment.id}
                  style={{
                    padding: '10px',
                    marginBottom: '10px',
                    backgroundColor: '#f9f9f9',
                    borderRadius: '4px',
                    fontSize: '13px'
                  }}
                >
                  <div style={{ fontWeight: '600', marginBottom: '3px' }}>
                    {comment.created_by}
                  </div>
                  <div style={{ color: '#666', marginBottom: '3px' }}>
                    {comment.text}
                  </div>
                  <div style={{ fontSize: '11px', color: '#999' }}>
                    {comment.created_at}
                  </div>
                </div>
              ))}
            </div>

            {/* Add Comment */}
            <div style={{
              display: 'flex',
              gap: '8px',
              marginTop: '12px'
            }}>
              <textarea
                value={newComment[insight.id] || ''}
                onChange={(e) => setNewComment({
                  ...newComment,
                  [insight.id]: e.target.value
                })}
                placeholder="Add a comment..."
                style={{
                  flex: 1,
                  padding: '8px',
                  borderRadius: '4px',
                  border: '1px solid #ddd',
                  fontFamily: 'sans-serif',
                  fontSize: '12px',
                  minHeight: '60px',
                  resize: 'vertical'
                }}
              />
              <button
                onClick={() => handleAddComment(insight.id)}
                style={{
                  padding: '8px 12px',
                  backgroundColor: '#3498db',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '12px',
                  fontWeight: '600',
                  whiteSpace: 'nowrap'
                }}
              >
                Post
              </button>
            </div>

            {/* Follow Button */}
            <button
              style={{
                marginTop: '12px',
                padding: '8px 12px',
                backgroundColor: '#f0f0f0',
                border: '1px solid #ddd',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '12px'
              }}
            >
              🔔 Follow
            </button>
          </div>
        )}

        {/* Click to expand */}
        {!isExpanded && (
          <div
            onClick={() => setExpandedInsight(insight.id)}
            style={{
              padding: '12px 16px',
              textAlign: 'center',
              color: '#3498db',
              fontSize: '12px',
              fontWeight: '600',
              cursor: 'pointer',
              backgroundColor: '#f9f9f9'
            }}
          >
            {commentCount} comments → Click to expand
          </div>
        )}
      </div>
    );
  };


  // ========================================================================
  // MAIN RENDER
  // ========================================================================

  return (
    <div style={{
      display: 'flex',
      height: '100vh',
      backgroundColor: '#ecf0f1',
      fontFamily: 'sans-serif'
    }}>
      {/* Main Feed */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        {/* Header */}
        <div style={{
          padding: '20px',
          backgroundColor: 'white',
          borderBottom: '1px solid #ddd',
          boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
        }}>
          <h1 style={{ margin: '0 0 15px 0' }}>Shared Insights Feed</h1>
          
          {/* Controls */}
          <div style={{ display: 'flex', gap: '10px' }}>
            <button
              onClick={() => setActiveTab('recent')}
              style={{
                padding: '8px 16px',
                backgroundColor: activeTab === 'recent' ? '#3498db' : '#f0f0f0',
                color: activeTab === 'recent' ? 'white' : '#666',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontWeight: '600'
              }}
            >
              Recent
            </button>
            <button
              onClick={() => setActiveTab('trending')}
              style={{
                padding: '8px 16px',
                backgroundColor: activeTab === 'trending' ? '#3498db' : '#f0f0f0',
                color: activeTab === 'trending' ? 'white' : '#666',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontWeight: '600'
              }}
            >
              Trending
            </button>
            
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              style={{
                marginLeft: 'auto',
                padding: '8px 12px',
                borderRadius: '4px',
                border: '1px solid #bdc3c7',
                backgroundColor: 'white'
              }}
            >
              <option value="recent">Most Recent</option>
              <option value="trending">Most Trending</option>
              <option value="consensus">Highest Consensus</option>
            </select>
          </div>
        </div>

        {/* Feed */}
        <div style={{
          flex: 1,
          overflowY: 'auto',
          padding: '20px',
          maxWidth: '900px',
          margin: '0 auto',
          width: '100%'
        }}>
          {loading ? (
            <div style={{ textAlign: 'center', color: '#999' }}>
              Loading insights...
            </div>
          ) : insights.length > 0 ? (
            insights.map(insight => renderInsightCard(insight))
          ) : (
            <div style={{
              textAlign: 'center',
              color: '#999',
              padding: '40px 20px'
            }}>
              No insights shared yet
            </div>
          )}
        </div>
      </div>

      {/* Trending Sidebar */}
      {renderTrendingSidebar()}
    </div>
  );
};

export default SharedInsightsFeed;
