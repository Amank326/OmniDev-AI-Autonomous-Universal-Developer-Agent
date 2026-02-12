"""
UpsellManager.jsx - Upsell campaign management and conversion tracking UI
Displays upsell opportunities, campaign performance, engagement metrics, and conversion funnel
"""

import React, { useState, useEffect } from 'react';
import axios from 'axios';

const UpsellManager = ({ customerId, currentTier }) => {
  const [opportunities, setOpportunities] = useState([]);
  const [campaigns, setCampaigns] = useState([]);
  const [conversionFunnel, setConversionFunnel] = useState(null);
  const [engagementScore, setEngagementScore] = useState(null);
  const [selectedOpportunity, setSelectedOpportunity] = useState(null);
  const [showCampaignBuilder, setShowCampaignBuilder] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isCreatingCampaign, setIsCreatingCampaign] = useState(false);

  const [campaignForm, setCampaignForm] = useState({
    targetTier: '',
    opportunityType: '',
    messaging: {
      headline: '',
      subheadline: '',
      cta: '',
    },
    triggerCondition: '',
  });

  // Fetch upsell data on mount and periodically
  useEffect(() => {
    const fetchUpsellData = async () => {
      try {
        const [oppResponse, funnelResponse, engagementResponse] = await Promise.all([
          axios.post(`/api/v1/tiers/${customerId}/upsell/opportunities`, {
            current_tier: currentTier,
          }),
          axios.get(`/api/v1/tiers/${customerId}/conversion-funnel`),
          axios.post(`/api/v1/tiers/${customerId}/engagement-score`, {
            engagement_data: {},
          }),
        ]);

        setOpportunities(oppResponse.data.data || []);
        setConversionFunnel(funnelResponse.data.data);
        setEngagementScore(engagementResponse.data.data);
        setError(null);
      } catch (err) {
        setError('Failed to load upsell data');
      } finally {
        setLoading(false);
      }
    };

    fetchUpsellData();
    // Refresh every 5 minutes
    const interval = setInterval(fetchUpsellData, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [customerId, currentTier]);

  // Get opportunity color based on type
  const getOpportunityColor = (type) => {
    const colors = {
      'USAGE_APPROACHING': '#FFA726',
      'FEATURE_REQUEST': '#42A5F5',
      'CHURN_RISK': '#EF5350',
      'ENGAGEMENT_LOW': '#AB47BC',
      'EXPANSION_POTENTIAL': '#66BB6A',
      'COMPETITIVE': '#EC407A',
    };
    return colors[type] || '#757575';
  };

  // Get opportunity icon
  const getOpportunityIcon = (type) => {
    const icons = {
      'USAGE_APPROACHING': '📊',
      'FEATURE_REQUEST': '✨',
      'CHURN_RISK': '⚠️',
      'ENGAGEMENT_LOW': '😴',
      'EXPANSION_POTENTIAL': '📈',
      'COMPETITIVE': '🎯',
    };
    return icons[type] || '💡';
  };

  // Track campaign event
  const trackEvent = async (campaignId, eventType) => {
    try {
      await axios.post(
        `/api/v1/tiers/campaigns/${campaignId}/track/${eventType}`,
        { customer_id: customerId }
      );
      // Refetch funnel data to update metrics
      const funnelResponse = await axios.get(`/api/v1/tiers/${customerId}/conversion-funnel`);
      setConversionFunnel(funnelResponse.data.data);
    } catch (err) {
      console.error('Failed to track event:', err);
    }
  };

  // Create campaign from opportunity
  const handleCreateCampaign = async (opportunity) => {
    setSelectedOpportunity(opportunity);
    setCampaignForm({
      targetTier: opportunity.recommended_tier || '',
      opportunityType: opportunity.type,
      messaging: {
        headline: `Unlock ${opportunity.type.replace('_', ' ').toLowerCase()} with ${opportunity.recommended_tier || 'Professional'}`,
        subheadline: opportunity.description || '',
        cta: 'Learn More',
      },
      triggerCondition: opportunity.type,
    });
    setShowCampaignBuilder(true);
  };

  // Submit campaign
  const handleSubmitCampaign = async () => {
    setIsCreatingCampaign(true);
    try {
      const response = await axios.post(
        `/api/v1/tiers/${customerId}/upsell/campaign`,
        {
          opportunity_type: campaignForm.opportunityType,
          target_tier: campaignForm.targetTier,
          messaging: campaignForm.messaging,
          trigger_condition: campaignForm.triggerCondition,
        }
      );

      setCampaigns([...campaigns, response.data.data]);
      setShowCampaignBuilder(false);
      setSelectedOpportunity(null);
      setError(null);
    } catch (err) {
      setError('Failed to create campaign');
    } finally {
      setIsCreatingCampaign(false);
    }
  };

  if (loading) {
    return <div className="upsell-manager loading">Loading upsell opportunities...</div>;
  }

  return (
    <div className="upsell-manager-container">
      <div className="upsell-header">
        <h1>🚀 Upsell Manager</h1>
        <p>Identify and optimize growth opportunities for your account</p>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {/* Engagement Score Card */}
      {engagementScore && (
        <div className="engagement-card">
          <div className="engagement-header">
            <h3>Engagement Score</h3>
            <span className="engagement-level">{engagementScore.level.toUpperCase()}</span>
          </div>
          <div className="engagement-visual">
            <div className="score-circle">
              <div className="score-value">{Math.round(engagementScore.score)}</div>
              <div className="score-label">/ 100</div>
            </div>
            <div className="engagement-breakdown">
              <div className="breakdown-item">
                <label>Logins</label>
                <div className="bar" style={{ width: `${engagementScore.components.login_frequency}%` }}></div>
                <span>{engagementScore.components.login_frequency}pts</span>
              </div>
              <div className="breakdown-item">
                <label>Features</label>
                <div className="bar" style={{ width: `${engagementScore.components.feature_adoption}%` }}></div>
                <span>{engagementScore.components.feature_adoption}pts</span>
              </div>
              <div className="breakdown-item">
                <label>API Usage</label>
                <div className="bar" style={{ width: `${engagementScore.components.api_usage}%` }}></div>
                <span>{engagementScore.components.api_usage}pts</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Opportunities Grid */}
      <div className="opportunities-section">
        <h2>📌 Upsell Opportunities</h2>
        <div className="opportunities-grid">
          {opportunities.length > 0 ? (
            opportunities.map((opp, idx) => (
              <div
                key={idx}
                className="opportunity-card"
                style={{ borderLeftColor: getOpportunityColor(opp.type) }}
              >
                <div className="opp-header">
                  <span className="opp-icon">{getOpportunityIcon(opp.type)}</span>
                  <h3>{opp.type.replace('_', ' ')}</h3>
                  <span className="severity-badge" style={{
                    backgroundColor: getOpportunityColor(opp.type),
                  }}>
                    {opp.severity || 'Medium'}
                  </span>
                </div>

                <p className="opp-description">{opp.description}</p>

                {opp.recommended_tier && (
                  <div className="recommended-tier">
                    <strong>Recommended Tier:</strong> {opp.recommended_tier}
                  </div>
                )}

                {opp.potential_revenue && (
                  <div className="potential-revenue">
                    <strong>Potential MRR:</strong> ${opp.potential_revenue}
                  </div>
                )}

                <button
                  className="btn btn-primary"
                  onClick={() => handleCreateCampaign(opp)}
                >
                  Create Campaign
                </button>
              </div>
            ))
          ) : (
            <div className="no-opportunities">
              <p>No active upsell opportunities at this time.</p>
            </div>
          )}
        </div>
      </div>

      {/* Campaign Builder Modal */}
      {showCampaignBuilder && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div className="modal-header">
              <h2>Create Upsell Campaign</h2>
              <button
                className="close-btn"
                onClick={() => setShowCampaignBuilder(false)}
              >
                ✕
              </button>
            </div>

            <div className="form-group">
              <label>Target Tier</label>
              <select
                value={campaignForm.targetTier}
                onChange={(e) => setCampaignForm({
                  ...campaignForm,
                  targetTier: e.target.value,
                })}
              >
                <option value="">Select a tier...</option>
                <option value="Professional">Professional</option>
                <option value="Enterprise">Enterprise</option>
                <option value="Custom">Custom</option>
              </select>
            </div>

            <div className="form-group">
              <label>Campaign Headline</label>
              <input
                type="text"
                value={campaignForm.messaging.headline}
                onChange={(e) => setCampaignForm({
                  ...campaignForm,
                  messaging: { ...campaignForm.messaging, headline: e.target.value },
                })}
                placeholder="e.g., Upgrade to Professional for Advanced Analytics"
              />
            </div>

            <div className="form-group">
              <label>Subheadline</label>
              <textarea
                value={campaignForm.messaging.subheadline}
                onChange={(e) => setCampaignForm({
                  ...campaignForm,
                  messaging: { ...campaignForm.messaging, subheadline: e.target.value },
                })}
                placeholder="Additional details about the opportunity..."
                rows="3"
              />
            </div>

            <div className="form-group">
              <label>Call to Action</label>
              <input
                type="text"
                value={campaignForm.messaging.cta}
                onChange={(e) => setCampaignForm({
                  ...campaignForm,
                  messaging: { ...campaignForm.messaging, cta: e.target.value },
                })}
                placeholder="e.g., Upgrade Now"
              />
            </div>

            <div className="modal-actions">
              <button
                className="btn btn-secondary"
                onClick={() => setShowCampaignBuilder(false)}
              >
                Cancel
              </button>
              <button
                className="btn btn-success"
                onClick={handleSubmitCampaign}
                disabled={isCreatingCampaign}
              >
                {isCreatingCampaign ? 'Creating...' : 'Create Campaign'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Conversion Funnel */}
      {conversionFunnel && (
        <div className="conversion-funnel-section">
          <h2>📊 Conversion Funnel</h2>
          <div className="funnel-container">
            {conversionFunnel.stages && Object.entries(conversionFunnel.stages).map(([stage, count], idx) => {
              const totalAtStart = Object.values(conversionFunnel.stages)[0];
              const percentage = totalAtStart ? (count / totalAtStart) * 100 : 0;
              const conversionRate = idx > 0 ? 
                ((count / Object.values(conversionFunnel.stages)[idx - 1]) * 100).toFixed(1) : 
                '100.0';

              return (
                <div key={stage} className="funnel-stage">
                  <div className="stage-bar" style={{
                    width: `${percentage}%`,
                    backgroundColor: ['#4CAF50', '#66BB6A', '#81C784', '#A5D6A7', '#C8E6C9', '#E8F5E9'][idx],
                  }}>
                    <div className="stage-label">
                      <strong>{stage.replace('_', ' ')}</strong>
                      <span className="stage-count">{count}</span>
                    </div>
                  </div>
                  {idx > 0 && (
                    <div className="conversion-metric">
                      {conversionRate}% conversion
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Active Campaigns */}
      {campaigns.length > 0 && (
        <div className="campaigns-section">
          <h2>📧 Active Campaigns</h2>
          <div className="campaigns-grid">
            {campaigns.map((campaign, idx) => (
              <div key={idx} className="campaign-card">
                <h3>{campaign.messaging?.headline || 'Campaign'}</h3>
                <div className="campaign-metrics">
                  <div className="metric">
                    <span className="label">Views</span>
                    <span className="value">{campaign.metrics?.views || 0}</span>
                  </div>
                  <div className="metric">
                    <span className="label">Clicks</span>
                    <span className="value">{campaign.metrics?.clicks || 0}</span>
                  </div>
                  <div className="metric">
                    <span className="label">CTR</span>
                    <span className="value">{campaign.metrics?.ctr || '0'}%</span>
                  </div>
                  <div className="metric">
                    <span className="label">Conversions</span>
                    <span className="value">{campaign.metrics?.conversions || 0}</span>
                  </div>
                </div>
                <div className="campaign-actions">
                  <button
                    className="btn btn-small"
                    onClick={() => trackEvent(campaign.id, 'view')}
                  >
                    View
                  </button>
                  <button
                    className="btn btn-small"
                    onClick={() => trackEvent(campaign.id, 'click')}
                  >
                    Click
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Styles */}
      <style>{`
        .upsell-manager-container {
          padding: 40px 20px;
          max-width: 1200px;
          margin: 0 auto;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        }

        .upsell-header {
          text-align: center;
          margin-bottom: 40px;
        }

        .upsell-header h1 {
          font-size: 2.2em;
          margin: 0 0 10px 0;
          color: #222;
        }

        .upsell-header p {
          font-size: 1.05em;
          color: #666;
          margin: 0;
        }

        .error-banner {
          background: #ffebee;
          color: #c62828;
          padding: 15px;
          border-radius: 6px;
          margin-bottom: 30px;
          border-left: 4px solid #c62828;
        }

        .engagement-card {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          padding: 30px;
          border-radius: 12px;
          margin-bottom: 40px;
          box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        }

        .engagement-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 25px;
        }

        .engagement-header h3 {
          margin: 0;
          font-size: 1.3em;
        }

        .engagement-level {
          background: rgba(255, 255, 255, 0.3);
          padding: 8px 16px;
          border-radius: 20px;
          font-weight: 600;
          font-size: 0.9em;
        }

        .engagement-visual {
          display: grid;
          grid-template-columns: 150px 1fr;
          gap: 30px;
          align-items: center;
        }

        .score-circle {
          text-align: center;
        }

        .score-value {
          font-size: 3em;
          font-weight: bold;
          line-height: 1;
          margin-bottom: 5px;
        }

        .score-label {
          font-size: 0.9em;
          opacity: 0.9;
        }

        .engagement-breakdown {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
          gap: 20px;
        }

        .breakdown-item {
          background: rgba(255, 255, 255, 0.1);
          padding: 15px;
          border-radius: 8px;
        }

        .breakdown-item label {
          display: block;
          font-size: 0.9em;
          margin-bottom: 8px;
          font-weight: 600;
        }

        .breakdown-item .bar {
          background: rgba(255, 255, 255, 0.4);
          height: 6px;
          border-radius: 3px;
          margin-bottom: 8px;
        }

        .breakdown-item span {
          font-size: 0.85em;
          opacity: 0.9;
        }

        .opportunities-section {
          margin-bottom: 50px;
        }

        .opportunities-section h2 {
          font-size: 1.5em;
          margin: 0 0 25px 0;
          color: #222;
        }

        .opportunities-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
          gap: 20px;
        }

        .opportunity-card {
          border-left: 4px solid;
          background: white;
          padding: 20px;
          border-radius: 8px;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
          transition: all 0.3s;
        }

        .opportunity-card:hover {
          transform: translateY(-3px);
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }

        .opp-header {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-bottom: 15px;
        }

        .opp-icon {
          font-size: 1.8em;
        }

        .opp-header h3 {
          margin: 0;
          font-size: 1.1em;
          flex: 1;
        }

        .severity-badge {
          padding: 4px 10px;
          border-radius: 20px;
          color: white;
          font-size: 0.8em;
          font-weight: 600;
        }

        .opp-description {
          color: #666;
          margin: 0 0 12px 0;
          font-size: 0.95em;
        }

        .recommended-tier {
          background: #e3f2fd;
          padding: 10px;
          border-radius: 6px;
          margin-bottom: 10px;
          font-size: 0.9em;
          color: #1565c0;
        }

        .potential-revenue {
          background: #e8f5e9;
          padding: 10px;
          border-radius: 6px;
          margin-bottom: 15px;
          font-size: 0.9em;
          color: #2e7d32;
        }

        .btn {
          padding: 10px 16px;
          border: none;
          border-radius: 6px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.3s;
          font-size: 0.9em;
        }

        .btn-primary {
          background: #2196F3;
          color: white;
          width: 100%;
        }

        .btn-primary:hover {
          background: #1976D2;
        }

        .btn-success {
          background: #4CAF50;
          color: white;
        }

        .btn-success:hover:not(:disabled) {
          background: #45a049;
        }

        .btn-success:disabled {
          background: #ccc;
          cursor: not-allowed;
        }

        .btn-secondary {
          background: #757575;
          color: white;
        }

        .btn-secondary:hover {
          background: #616161;
        }

        .btn-small {
          padding: 6px 12px;
          font-size: 0.85em;
        }

        .no-opportunities {
          text-align: center;
          padding: 40px;
          color: #999;
          background: #f9f9f9;
          border-radius: 8px;
        }

        .modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.5);
          display: flex;
          justify-content: center;
          align-items: center;
          z-index: 1000;
        }

        .modal-content {
          background: white;
          padding: 40px;
          border-radius: 12px;
          max-width: 600px;
          width: 90%;
          box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
        }

        .modal-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 25px;
        }

        .modal-header h2 {
          margin: 0;
          color: #222;
        }

        .close-btn {
          background: none;
          border: none;
          font-size: 1.5em;
          cursor: pointer;
          color: #666;
        }

        .form-group {
          margin-bottom: 20px;
        }

        .form-group label {
          display: block;
          margin-bottom: 8px;
          font-weight: 600;
          color: #222;
        }

        .form-group input,
        .form-group select,
        .form-group textarea {
          width: 100%;
          padding: 10px;
          border: 1px solid #ddd;
          border-radius: 6px;
          font-family: inherit;
          font-size: 0.95em;
        }

        .form-group input:focus,
        .form-group select:focus,
        .form-group textarea:focus {
          outline: none;
          border-color: #2196F3;
          box-shadow: 0 0 0 3px rgba(33, 150, 243, 0.1);
        }

        .modal-actions {
          display: flex;
          gap: 15px;
          margin-top: 30px;
        }

        .modal-actions button {
          flex: 1;
          padding: 12px;
        }

        .conversion-funnel-section {
          background: white;
          padding: 30px;
          border-radius: 8px;
          margin-bottom: 50px;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }

        .conversion-funnel-section h2 {
          font-size: 1.5em;
          margin: 0 0 25px 0;
          color: #222;
        }

        .funnel-container {
          display: flex;
          flex-direction: column;
          gap: 20px;
        }

        .funnel-stage {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .stage-bar {
          height: 60px;
          border-radius: 6px;
          display: flex;
          align-items: center;
          padding-left: 15px;
          color: white;
          font-weight: 600;
          min-width: 150px;
        }

        .stage-label {
          display: flex;
          justify-content: space-between;
          flex: 1;
          gap: 15px;
        }

        .stage-label strong {
          font-size: 0.9em;
        }

        .stage-count {
          background: rgba(255, 255, 255, 0.3);
          padding: 2px 8px;
          border-radius: 12px;
          font-size: 0.8em;
        }

        .conversion-metric {
          font-size: 0.85em;
          color: #666;
          margin-left: 15px;
        }

        .campaigns-section {
          margin-bottom: 50px;
        }

        .campaigns-section h2 {
          font-size: 1.5em;
          margin: 0 0 25px 0;
          color: #222;
        }

        .campaigns-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
          gap: 20px;
        }

        .campaign-card {
          background: white;
          padding: 20px;
          border-radius: 8px;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }

        .campaign-card h3 {
          margin: 0 0 15px 0;
          color: #222;
          font-size: 1em;
        }

        .campaign-metrics {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 12px;
          margin-bottom: 15px;
        }

        .metric {
          background: #f5f5f5;
          padding: 12px;
          border-radius: 6px;
          text-align: center;
        }

        .metric .label {
          display: block;
          font-size: 0.8em;
          color: #666;
          margin-bottom: 5px;
        }

        .metric .value {
          display: block;
          font-size: 1.5em;
          font-weight: 600;
          color: #2196F3;
        }

        .campaign-actions {
          display: flex;
          gap: 10px;
        }

        .upsell-manager.loading {
          text-align: center;
          padding: 50px;
          font-size: 1.2em;
          color: #666;
        }

        @media (max-width: 768px) {
          .engagement-visual {
            grid-template-columns: 1fr;
          }

          .opportunities-grid {
            grid-template-columns: 1fr;
          }

          .campaigns-grid {
            grid-template-columns: 1fr;
          }

          .modal-content {
            width: 95%;
            padding: 25px;
          }
        }
      `}</style>
    </div>
  );
};

export default UpsellManager;
