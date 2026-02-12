"""
TierSelector.jsx - Tier selection and comparison UI component
Displays tiers with interactive comparison, pricing details, and upgrade/downgrade flow
"""

import React, { useState, useEffect } from 'react';
import axios from 'axios';

const TierSelector = ({ customerId, currentTier, onTierChange }) => {
  const [tiers, setTiers] = useState([]);
  const [selectedTier, setSelectedTier] = useState(currentTier);
  const [billingCycle, setBillingCycle] = useState('monthly');
  const [showComparison, setShowComparison] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [upgradeDetails, setUpgradeDetails] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);

  // Fetch available tiers
  useEffect(() => {
    const fetchTiers = async () => {
      try {
        const response = await axios.get('/api/v1/tiers/');
        setTiers(response.data.data);
        setLoading(false);
      } catch (err) {
        setError('Failed to load tiers');
        setLoading(false);
      }
    };

    fetchTiers();
  }, []);

  // Get tier by level
  const getTierData = (level) => {
    return tiers.find(t => t.level === level);
  };

  // Format price based on billing cycle
  const formatPrice = (price, cycle = 'monthly') => {
    const displayPrice = cycle === 'annual' ? price * 10 : price; // Assuming 10% discount for annual
    return `$${displayPrice.toFixed(2)}/${cycle === 'annual' ? 'year' : 'month'}`;
  };

  // Calculate upgrade cost with proration
  const calculateUpgradeCost = async (newTier) => {
    try {
      const tierData = getTierData(newTier);
      const currentTierData = getTierData(currentTier);
      
      if (tierData.price > currentTierData.price) {
        // Calculate pro-rata credit
        const monthlyDifference = tierData.price - currentTierData.price;
        const proRataCredit = (monthlyDifference / 30) * 15; // Assuming mid-month upgrade
        
        setUpgradeDetails({
          currentPrice: currentTierData.price,
          newPrice: tierData.price,
          difference: monthlyDifference,
          prorataCredit: proRataCredit,
          immediateCharge: monthlyDifference - proRataCredit,
        });
      } else {
        setUpgradeDetails(null);
      }
    } catch (err) {
      console.error('Failed to calculate upgrade cost:', err);
    }
  };

  // Handle tier selection
  const handleSelectTier = (tier) => {
    setSelectedTier(tier);
    if (tier !== currentTier) {
      calculateUpgradeCost(tier);
    } else {
      setUpgradeDetails(null);
    }
  };

  // Process subscription change
  const handleSubscriptionChange = async () => {
    setIsProcessing(true);
    try {
      const endpoint = selectedTier > currentTier ? 'upgrade' : 'downgrade';
      const response = await axios.post(
        `/api/v1/tiers/${customerId}/${endpoint}`,
        {
          tier: selectedTier,
          billing_cycle: billingCycle,
          proration: true,
          reason: 'Customer-initiated change',
        }
      );

      onTierChange(selectedTier);
      setError(null);
      // Show success message
      alert(`Successfully ${endpoint}d to ${selectedTier} tier`);
    } catch (err) {
      setError(`Failed to ${selectedTier > currentTier ? 'upgrade' : 'downgrade'} tier`);
    } finally {
      setIsProcessing(false);
    }
  };

  if (loading) {
    return <div className="tier-selector loading">Loading tiers...</div>;
  }

  const tierLevels = ['Starter', 'Professional', 'Enterprise', 'Custom'];
  const tierColors = {
    'Starter': '#E8F5E9',
    'Professional': '#E3F2FD',
    'Enterprise': '#FFF3E0',
    'Custom': '#F3E5F5',
  };

  const tierIcons = {
    'Starter': '⭐',
    'Professional': '⭐⭐',
    'Enterprise': '⭐⭐⭐',
    'Custom': '🎯',
  };

  return (
    <div className="tier-selector-container">
      <div className="tier-selector-header">
        <h1>Choose Your Plan</h1>
        <p>Scale your AI operations with the perfect tier for your needs</p>
        
        {/* Billing Cycle Toggle */}
        <div className="billing-toggle">
          <button
            className={`toggle-btn ${billingCycle === 'monthly' ? 'active' : ''}`}
            onClick={() => setBillingCycle('monthly')}
          >
            Monthly
          </button>
          <button
            className={`toggle-btn ${billingCycle === 'annual' ? 'active' : ''}`}
            onClick={() => setBillingCycle('annual')}
          >
            Annual (Save 10%)
          </button>
        </div>
      </div>

      {/* Tier Grid */}
      <div className="tier-grid">
        {tierLevels.map((level) => {
          const tier = getTierData(level);
          const isCurrent = level === currentTier;
          const isSelected = level === selectedTier;

          return (
            <div
              key={level}
              className={`tier-card ${isCurrent ? 'current' : ''} ${isSelected ? 'selected' : ''}`}
              style={{ backgroundColor: tierColors[level] }}
            >
              {/* Badge */}
              {isCurrent && <span className="badge current-badge">Current Plan</span>}
              {isSelected && isCurrent === false && <span className="badge selected-badge">Selected</span>}

              {/* Tier Header */}
              <div className="tier-header">
                <div className="tier-icon">{tierIcons[level]}</div>
                <h2 className="tier-name">{level}</h2>
                <p className="tier-description">{tier?.description || ''}</p>
              </div>

              {/* Pricing */}
              <div className="tier-pricing">
                <div className="price-display">
                  <span className="currency">$</span>
                  <span className="amount">{billingCycle === 'annual' ? Math.round(tier?.price * 10) : tier?.price}</span>
                  <span className="period">/{billingCycle === 'annual' ? 'year' : 'month'}</span>
                </div>
                {billingCycle === 'annual' && (
                  <p className="savings">Save 10% with annual billing</p>
                )}
              </div>

              {/* Key Features */}
              <div className="tier-features">
                <h4>Key Features</h4>
                <ul>
                  <li>✓ {tier?.max_agents || 'Unlimited'} Agents</li>
                  <li>✓ {tier?.executions_per_month?.toLocaleString() || 'Unlimited'} Executions/month</li>
                  <li>✓ {tier?.max_api_calls?.toLocaleString() || 'Unlimited'} API Calls/month</li>
                  <li>✓ {tier?.max_users || 'Unlimited'} Team Members</li>
                  <li>✓ {tier?.max_storage_gb || 'Unlimited'}GB Storage</li>
                  <li>✓ {tier?.sla || 'Standard'} SLA</li>
                  {tier?.features?.includes('SSO') && <li>✓ SSO Authentication</li>}
                  {tier?.features?.includes('white_label') && <li>✓ White Labeling</li>}
                  {tier?.features?.includes('audit_logs') && <li>✓ Audit Logs</li>}
                </ul>
              </div>

              {/* Support Level */}
              <div className="tier-support">
                <p className="support-level">
                  <strong>Support:</strong> {tier?.support || 'Standard'}
                </p>
              </div>

              {/* Action Buttons */}
              <div className="tier-actions">
                {isCurrent ? (
                  <button className="btn btn-primary" disabled>
                    Your Current Plan
                  </button>
                ) : (
                  <button
                    className={`btn btn-primary ${isSelected ? 'selected' : ''}`}
                    onClick={() => handleSelectTier(level)}
                  >
                    {isSelected ? 'Selected' : 'Select Plan'}
                  </button>
                )}
              </div>

              {/* Upgrade Cost Display */}
              {isSelected && isCurrent === false && upgradeDetails && (
                <div className="upgrade-details">
                  <h5>Upgrade Summary</h5>
                  <div className="cost-breakdown">
                    <div className="cost-row">
                      <span>Current Plan:</span>
                      <span>${upgradeDetails.currentPrice}/month</span>
                    </div>
                    <div className="cost-row">
                      <span>New Plan:</span>
                      <span>${upgradeDetails.newPrice}/month</span>
                    </div>
                    <div className="cost-row">
                      <span>Monthly Difference:</span>
                      <span>+${upgradeDetails.difference.toFixed(2)}</span>
                    </div>
                    <div className="cost-row proration">
                      <span>Pro-rata Credit:</span>
                      <span>-${upgradeDetails.prorataCredit.toFixed(2)}</span>
                    </div>
                    <div className="cost-row total">
                      <span>Immediate Charge:</span>
                      <span className="highlight">${upgradeDetails.immediateCharge.toFixed(2)}</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Comparison Table */}
      <div className="comparison-section">
        <button
          className="btn btn-secondary"
          onClick={() => setShowComparison(!showComparison)}
        >
          {showComparison ? 'Hide' : 'Show'} Detailed Comparison
        </button>

        {showComparison && (
          <table className="comparison-table">
            <thead>
              <tr>
                <th>Feature</th>
                {tierLevels.map(level => <th key={level}>{level}</th>)}
              </tr>
            </thead>
            <tbody>
              <tr>
                <td><strong>Price</strong></td>
                {tierLevels.map(level => (
                  <td key={level}>{formatPrice(getTierData(level)?.price, billingCycle)}</td>
                ))}
              </tr>
              <tr>
                <td><strong>Agents</strong></td>
                {tierLevels.map(level => (
                  <td key={level}>{getTierData(level)?.max_agents || 'Unlimited'}</td>
                ))}
              </tr>
              <tr>
                <td><strong>Executions/month</strong></td>
                {tierLevels.map(level => (
                  <td key={level}>{getTierData(level)?.executions_per_month?.toLocaleString() || 'Unlimited'}</td>
                ))}
              </tr>
              <tr>
                <td><strong>API Calls/month</strong></td>
                {tierLevels.map(level => (
                  <td key={level}>{getTierData(level)?.max_api_calls?.toLocaleString() || 'Unlimited'}</td>
                ))}
              </tr>
              <tr>
                <td><strong>Storage</strong></td>
                {tierLevels.map(level => (
                  <td key={level}>{getTierData(level)?.max_storage_gb || 'Unlimited'}GB</td>
                ))}
              </tr>
              <tr>
                <td><strong>Team Members</strong></td>
                {tierLevels.map(level => (
                  <td key={level}>{getTierData(level)?.max_users || 'Unlimited'}</td>
                ))}
              </tr>
              <tr>
                <td><strong>Support SLA</strong></td>
                {tierLevels.map(level => (
                  <td key={level}>{getTierData(level)?.sla || 'Standard'}</td>
                ))}
              </tr>
              <tr>
                <td><strong>Support Tier</strong></td>
                {tierLevels.map(level => (
                  <td key={level}>{getTierData(level)?.support || 'Email'}</td>
                ))}
              </tr>
            </tbody>
          </table>
        )}
      </div>

      {/* CTA Section */}
      {selectedTier !== currentTier && (
        <div className="cta-section">
          {error && <div className="error-message">{error}</div>}
          <button
            className="btn btn-success"
            onClick={handleSubscriptionChange}
            disabled={isProcessing}
          >
            {isProcessing ? 'Processing...' : `${selectedTier > currentTier ? 'Upgrade' : 'Downgrade'} to ${selectedTier}`}
          </button>
        </div>
      )}

      {/* Styles */}
      <style>{`
        .tier-selector-container {
          padding: 40px 20px;
          max-width: 1400px;
          margin: 0 auto;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
        }

        .tier-selector-header {
          text-align: center;
          margin-bottom: 50px;
        }

        .tier-selector-header h1 {
          font-size: 2.5em;
          margin: 0 0 10px 0;
          color: #222;
        }

        .tier-selector-header p {
          font-size: 1.1em;
          color: #666;
          margin: 0 0 30px 0;
        }

        .billing-toggle {
          display: flex;
          justify-content: center;
          gap: 10px;
          margin-bottom: 20px;
        }

        .toggle-btn {
          padding: 10px 20px;
          border: 2px solid #ddd;
          background: white;
          border-radius: 6px;
          cursor: pointer;
          font-size: 1em;
          transition: all 0.3s;
        }

        .toggle-btn.active {
          border-color: #2196F3;
          background: #2196F3;
          color: white;
        }

        .tier-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
          gap: 30px;
          margin-bottom: 50px;
        }

        .tier-card {
          border-radius: 12px;
          padding: 30px;
          border: 2px solid transparent;
          position: relative;
          transition: all 0.3s;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }

        .tier-card.current {
          border-color: #4CAF50;
          box-shadow: 0 4px 12px rgba(76, 175, 80, 0.2);
        }

        .tier-card.selected {
          border-color: #2196F3;
          box-shadow: 0 4px 12px rgba(33, 150, 243, 0.2);
        }

        .tier-card:hover {
          transform: translateY(-5px);
          box-shadow: 0 8px 16px rgba(0, 0, 0, 0.15);
        }

        .badge {
          position: absolute;
          top: 10px;
          right: 10px;
          padding: 6px 12px;
          border-radius: 20px;
          font-size: 0.8em;
          font-weight: 600;
        }

        .current-badge {
          background: #4CAF50;
          color: white;
        }

        .selected-badge {
          background: #2196F3;
          color: white;
        }

        .tier-header {
          text-align: center;
          margin-bottom: 20px;
        }

        .tier-icon {
          font-size: 2.5em;
          margin-bottom: 10px;
        }

        .tier-name {
          font-size: 1.8em;
          margin: 10px 0;
          color: #222;
        }

        .tier-description {
          color: #666;
          font-size: 0.9em;
          margin: 0;
        }

        .tier-pricing {
          text-align: center;
          margin-bottom: 25px;
          padding-bottom: 25px;
          border-bottom: 1px solid rgba(0, 0, 0, 0.1);
        }

        .price-display {
          display: flex;
          justify-content: center;
          align-items: flex-start;
          margin-bottom: 8px;
        }

        .currency {
          font-size: 1.2em;
          margin-right: 2px;
          color: #666;
        }

        .amount {
          font-size: 2.5em;
          font-weight: bold;
          color: #222;
        }

        .period {
          color: #666;
          font-size: 1em;
          margin-left: 5px;
        }

        .savings {
          font-size: 0.85em;
          color: #4CAF50;
          font-weight: 600;
          margin: 0;
        }

        .tier-features {
          margin-bottom: 20px;
        }

        .tier-features h4 {
          margin: 0 0 15px 0;
          color: #222;
          font-size: 1em;
        }

        .tier-features ul {
          list-style: none;
          padding: 0;
          margin: 0;
        }

        .tier-features li {
          padding: 8px 0;
          color: #555;
          font-size: 0.95em;
          border-bottom: 1px solid rgba(0, 0, 0, 0.05);
        }

        .tier-support {
          margin-bottom: 20px;
          padding: 15px;
          background: rgba(255, 255, 255, 0.5);
          border-radius: 6px;
        }

        .support-level {
          margin: 0;
          color: #666;
          font-size: 0.95em;
        }

        .tier-actions {
          margin-bottom: 15px;
        }

        .btn {
          width: 100%;
          padding: 12px;
          border: none;
          border-radius: 6px;
          font-size: 1em;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.3s;
        }

        .btn-primary {
          background: #2196F3;
          color: white;
        }

        .btn-primary:hover:not(:disabled) {
          background: #1976D2;
        }

        .btn-primary:disabled {
          background: #ccc;
          cursor: not-allowed;
        }

        .btn-primary.selected {
          background: #1976D2;
          border: 2px solid #0D47A1;
        }

        .upgrade-details {
          background: #E8F5E9;
          padding: 15px;
          border-radius: 6px;
          margin-top: 15px;
        }

        .upgrade-details h5 {
          margin: 0 0 12px 0;
          color: #2E7D32;
          font-size: 0.95em;
        }

        .cost-breakdown {
          font-size: 0.9em;
        }

        .cost-row {
          display: flex;
          justify-content: space-between;
          padding: 6px 0;
          color: #555;
          border-bottom: 1px solid rgba(0, 0, 0, 0.05);
        }

        .cost-row.proration {
          color: #2E7D32;
          font-weight: 600;
        }

        .cost-row.total {
          border-top: 2px solid #4CAF50;
          margin-top: 8px;
          padding-top: 8px;
          font-weight: 600;
          color: #1B5E20;
        }

        .highlight {
          color: #2E7D32;
          font-weight: bold;
        }

        .comparison-section {
          text-align: center;
          margin: 40px 0;
        }

        .btn-secondary {
          background: #757575;
          color: white;
          padding: 10px 20px;
          border: none;
          border-radius: 6px;
          cursor: pointer;
          font-weight: 600;
        }

        .btn-secondary:hover {
          background: #616161;
        }

        .comparison-table {
          width: 100%;
          border-collapse: collapse;
          margin-top: 20px;
          background: white;
          border-radius: 8px;
          overflow: hidden;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }

        .comparison-table thead {
          background: #f5f5f5;
        }

        .comparison-table th,
        .comparison-table td {
          padding: 12px;
          text-align: left;
          border-bottom: 1px solid #eee;
        }

        .comparison-table th {
          font-weight: 600;
          color: #222;
        }

        .comparison-table tbody tr:last-child td {
          border-bottom: none;
        }

        .cta-section {
          text-align: center;
          padding: 30px;
          background: #f9f9f9;
          border-radius: 8px;
          margin-top: 40px;
        }

        .error-message {
          background: #ffebee;
          color: #c62828;
          padding: 15px;
          border-radius: 6px;
          margin-bottom: 15px;
          border-left: 4px solid #c62828;
        }

        .btn-success {
          background: #4CAF50;
          color: white;
          padding: 14px 30px;
          font-size: 1.1em;
        }

        .btn-success:hover:not(:disabled) {
          background: #45a049;
        }

        .btn-success:disabled {
          background: #ccc;
          cursor: not-allowed;
        }

        .tier-selector.loading {
          text-align: center;
          padding: 50px;
          font-size: 1.2em;
          color: #666;
        }

        @media (max-width: 768px) {
          .tier-grid {
            grid-template-columns: 1fr;
          }

          .tier-selector-header h1 {
            font-size: 1.8em;
          }

          .comparison-table {
            font-size: 0.9em;
          }

          .comparison-table th,
          .comparison-table td {
            padding: 8px;
          }
        }
      `}</style>
    </div>
  );
};

export default TierSelector;
