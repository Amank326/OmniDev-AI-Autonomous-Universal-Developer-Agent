import React, { useState, useEffect } from 'react';
import { Share2, Lock, Unlock, Users, Copy, Trash2, MessageSquare, ThumbsUp, Calendar } from 'lucide-react';

const WorkflowSharing = () => {
  const [activeTab, setActiveTab] = useState('shares');
  const [shares, setShares] = useState([]);
  const [suggestions, setSuggestions] = useState([]);
  const [showShareDialog, setShowShareDialog] = useState(false);
  const [shareConfig, setShareConfig] = useState({
    type: 'user',
    canFork: true,
    canSuggest: true,
    canRate: true
  });

  // Sample data
  useEffect(() => {
    setShares([
      {
        id: '1',
        templateName: 'Email Marketing Automation',
        type: 'user',
        target: 'alex@example.com',
        token: 'share_abc123def456',
        created: '2 days ago',
        accessed: '1 day ago',
        permissions: { canFork: true, canSuggest: true, canRate: true }
      },
      {
        id: '2',
        templateName: 'Data Pipeline',
        type: 'public',
        target: 'Public Link',
        token: 'share_xyz789abc',
        created: '1 week ago',
        accessed: '2 hours ago',
        permissions: { canFork: true, canSuggest: false, canRate: true },
        views: 47
      }
    ]);

    setSuggestions([
      {
        id: '1',
        template: 'Email Marketing',
        type: 'improvement',
        title: 'Add support for A/B testing',
        user: 'Jordan Kim',
        votes: 12,
        status: 'pending',
        date: '3 days ago'
      },
      {
        id: '2',
        template: 'Data Pipeline',
        type: 'bug_fix',
        title: 'Fix timeout issue on large datasets',
        user: 'Sam Chen',
        votes: 5,
        status: 'approved',
        date: '5 days ago'
      },
      {
        id: '3',
        template: 'Social Media Poster',
        type: 'feature',
        title: 'Multi-language support',
        user: 'Riley Park',
        votes: 23,
        status: 'pending',
        date: '1 day ago'
      }
    ]);
  }, []);

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    alert('Share link copied!');
  };

  const ShareCard = ({ share }) => (
    <div className="bg-white rounded-lg shadow-md p-6 mb-4">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="font-bold text-lg">{share.templateName}</h3>
          <p className="text-gray-600 text-sm">
            Shared with {share.type === 'public' ? 'Public Link' : share.target}
          </p>
        </div>
        {share.type === 'public' ? (
          <Unlock className="w-5 h-5 text-green-600" />
        ) : (
          <Lock className="w-5 h-5 text-blue-600" />
        )}
      </div>

      <div className="bg-gray-50 p-3 rounded mb-4">
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={share.token}
            readOnly
            className="flex-1 px-2 py-1 bg-white border border-gray-300 rounded text-sm font-mono"
          />
          <button
            onClick={() => copyToClipboard(share.token)}
            className="p-2 hover:bg-gray-200 rounded transition-colors"
          >
            <Copy className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4 text-sm">
        <div className="flex items-center gap-2">
          <Calendar className="w-4 h-4 text-gray-500" />
          <span className="text-gray-700">Shared {share.created}</span>
        </div>
        {share.accessed && (
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 text-gray-500" />
            <span className="text-gray-700">Accessed {share.accessed}</span>
          </div>
        )}
        {share.views !== undefined && (
          <div className="flex items-center gap-2">
            <Users className="w-4 h-4 text-gray-500" />
            <span className="text-gray-700">{share.views} views</span>
          </div>
        )}
      </div>

      <div className="space-y-2 mb-4 text-sm">
        <label className="flex items-center gap-2">
          <input type="checkbox" defaultChecked={share.permissions.canFork} className="rounded" />
          <span>Can fork</span>
        </label>
        <label className="flex items-center gap-2">
          <input type="checkbox" defaultChecked={share.permissions.canSuggest} className="rounded" />
          <span>Can suggest improvements</span>
        </label>
        <label className="flex items-center gap-2">
          <input type="checkbox" defaultChecked={share.permissions.canRate} className="rounded" />
          <span>Can rate</span>
        </label>
      </div>

      <div className="flex gap-2">
        <button className="flex-1 border border-gray-300 py-2 rounded-lg hover:bg-gray-50 transition-colors text-sm font-medium">
          Edit
        </button>
        <button className="flex-1 border border-red-300 text-red-600 py-2 rounded-lg hover:bg-red-50 transition-colors text-sm font-medium flex items-center justify-center gap-2">
          <Trash2 className="w-4 h-4" />
          Revoke
        </button>
      </div>
    </div>
  );

  const SuggestionCard = ({ suggestion }) => (
    <div className="bg-white rounded-lg shadow-md p-6 mb-4">
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <span className="bg-purple-100 text-purple-700 text-xs px-2 py-1 rounded">
              {suggestion.type}
            </span>
            <span className={`text-xs px-2 py-1 rounded ${
              suggestion.status === 'approved' ? 'bg-green-100 text-green-700' :
              suggestion.status === 'pending' ? 'bg-yellow-100 text-yellow-700' :
              'bg-gray-100 text-gray-700'
            }`}>
              {suggestion.status}
            </span>
          </div>
          <h3 className="font-bold text-lg mb-1">{suggestion.title}</h3>
          <p className="text-gray-600 text-sm">
            on {suggestion.template} • by {suggestion.user} • {suggestion.date}
          </p>
        </div>
      </div>

      <div className="flex items-center gap-4 mb-4">
        <button className="flex items-center gap-2 text-blue-600 hover:text-blue-700 text-sm">
          <ThumbsUp className="w-4 h-4" />
          <span className="font-medium">{suggestion.votes} upvotes</span>
        </button>
        <button className="flex items-center gap-2 text-gray-600 hover:text-gray-700 text-sm">
          <MessageSquare className="w-4 h-4" />
          <span>Comments</span>
        </button>
      </div>

      <div className="flex gap-2">
        {suggestion.status === 'pending' && (
          <>
            <button className="flex-1 bg-green-600 text-white py-2 rounded-lg hover:bg-green-700 transition-colors text-sm font-medium">
              Approve
            </button>
            <button className="flex-1 border border-gray-300 py-2 rounded-lg hover:bg-gray-50 transition-colors text-sm font-medium">
              Review Details
            </button>
          </>
        )}
        {suggestion.status === 'approved' && (
          <>
            <button className="flex-1 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition-colors text-sm font-medium">
              Implement
            </button>
            <button className="flex-1 border border-gray-300 py-2 rounded-lg hover:bg-gray-50 transition-colors text-sm font-medium">
              View Changes
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
          <div className="flex justify-between items-center mb-6">
            <div>
              <h1 className="text-3xl font-bold">Workflow Sharing</h1>
              <p className="text-gray-600">Manage shares and community feedback</p>
            </div>
            <button
              onClick={() => setShowShareDialog(true)}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
            >
              <Share2 className="w-5 h-5" />
              New Share
            </button>
          </div>

          {/* Tabs */}
          <div className="flex gap-4 border-b border-gray-200">
            <button
              onClick={() => setActiveTab('shares')}
              className={`px-4 py-2 font-medium border-b-2 transition-colors ${
                activeTab === 'shares'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-800'
              }`}
            >
              Active Shares ({shares.length})
            </button>
            <button
              onClick={() => setActiveTab('suggestions')}
              className={`px-4 py-2 font-medium border-b-2 transition-colors ${
                activeTab === 'suggestions'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-800'
              }`}
            >
              Community Suggestions ({suggestions.length})
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-6xl mx-auto p-6">
        {activeTab === 'shares' && (
          <div>
            {shares.length === 0 ? (
              <div className="bg-white rounded-lg shadow-md p-12 text-center">
                <Share2 className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600 mb-4">No shares yet</p>
                <button
                  onClick={() => setShowShareDialog(true)}
                  className="text-blue-600 hover:underline"
                >
                  Create your first share
                </button>
              </div>
            ) : (
              shares.map(share => (
                <ShareCard key={share.id} share={share} />
              ))
            )}
          </div>
        )}

        {activeTab === 'suggestions' && (
          <div>
            {suggestions.length === 0 ? (
              <div className="bg-white rounded-lg shadow-md p-12 text-center">
                <MessageSquare className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600">No suggestions yet</p>
              </div>
            ) : (
              suggestions.map(suggestion => (
                <SuggestionCard key={suggestion.id} suggestion={suggestion} />
              ))
            )}
          </div>
        )}
      </div>

      {/* Share Dialog */}
      {showShareDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <h2 className="text-2xl font-bold mb-4">Create New Share</h2>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Share Type
                </label>
                <select
                  value={shareConfig.type}
                  onChange={(e) => setShareConfig({ ...shareConfig, type: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="user">Share with User</option>
                  <option value="team">Share with Team</option>
                  <option value="public">Public Link</option>
                </select>
              </div>

              {shareConfig.type !== 'public' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    {shareConfig.type === 'user' ? 'Email' : 'Team'}
                  </label>
                  <input
                    type="text"
                    placeholder={shareConfig.type === 'user' ? 'user@example.com' : 'Team name'}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              )}

              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700">Permissions</label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={shareConfig.canFork}
                    onChange={(e) => setShareConfig({ ...shareConfig, canFork: e.target.checked })}
                    className="rounded"
                  />
                  <span className="text-sm">Allow forking</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={shareConfig.canSuggest}
                    onChange={(e) => setShareConfig({ ...shareConfig, canSuggest: e.target.checked })}
                    className="rounded"
                  />
                  <span className="text-sm">Allow suggestions</span>
                </label>
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={shareConfig.canRate}
                    onChange={(e) => setShareConfig({ ...shareConfig, canRate: e.target.checked })}
                    className="rounded"
                  />
                  <span className="text-sm">Allow ratings</span>
                </label>
              </div>
            </div>

            <div className="flex gap-2 mt-6">
              <button
                onClick={() => setShowShareDialog(false)}
                className="flex-1 border border-gray-300 py-2 rounded-lg hover:bg-gray-50 transition-colors font-medium"
              >
                Cancel
              </button>
              <button
                onClick={() => setShowShareDialog(false)}
                className="flex-1 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition-colors font-medium"
              >
                Create Share
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default WorkflowSharing;
