/**
 * Onboarding Journey Component
 * Visualizes personalized onboarding progress with milestones and celebrations
 * Uses: onboarding_optimization_service (journey tracking)
 */

import React, { useState, useEffect } from 'react';
import './OnboardingJourney.css';

const OnboardingJourney = ({ customerId, apiBaseUrl = '/api/v1' }) => {
  // ========================================================================
  // STATE MANAGEMENT
  // ========================================================================

  const [progress, setProgress] = useState(null);
  const [journeyPhases, setJourneyPhases] = useState([]);
  const [milestones, setMilestones] = useState([]);
  const [celebrationActive, setCelebrationActive] = useState(false);
  const [celebrationMessage, setCelebrationMessage] = useState('');
  const [selectedPhase, setSelectedPhase] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // ========================================================================
  // DATA FETCHING
  // ========================================================================

  useEffect(() => {
    const fetchOnboardingData = async () => {
      try {
        setLoading(true);
        const headers = { 'Authorization': `Bearer ${localStorage.getItem('token')}` };

        // Fetch onboarding progress
        const progressRes = await fetch(
          `${apiBaseUrl}/success/onboarding/${customerId}/progress`,
          { headers }
        );
        const progressData = await progressRes.json();
        setProgress(progressData);

        // Build journey phases from API response
        const phases = progressData.phases_completed
          ? [
              ...progressData.phases_completed.map(p => ({
                name: p,
                status: 'completed',
              })),
              {
                name: progressData.current_phase,
                status: 'active',
              },
              ...progressData.phases_remaining.map(p => ({
                name: p,
                status: 'upcoming',
              })),
            ]
          : [];
        setJourneyPhases(phases);

        // Build milestone list
        const allMilestones = [
          ...(progressData.milestones_achieved || []).map(m => ({
            name: m,
            achieved: true,
          })),
          {
            name: progressData.next_milestone,
            achieved: false,
            current: true,
          },
        ];
        setMilestones(allMilestones);

        setError(null);
      } catch (err) {
        setError(err.message);
        console.error('Error fetching onboarding data:', err);
      } finally {
        setLoading(false);
      }
    };

    if (customerId) {
      fetchOnboardingData();
    }
  }, [customerId, apiBaseUrl]);

  // ========================================================================
  // MILESTONE TRACKING
  // ========================================================================

  const handleMilestoneAchieved = async (milestoneId) => {
    try {
      const headers = {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json',
      };

      const response = await fetch(
        `${apiBaseUrl}/success/onboarding/${customerId}/milestone/${milestoneId}`,
        {
          method: 'POST',
          headers,
          body: JSON.stringify({}),
        }
      );

      const data = await response.json();

      // Trigger celebration
      setCelebrationMessage(data.celebration_message);
      setCelebrationActive(true);
      setTimeout(() => setCelebrationActive(false), 3000);

      // Refresh data
      const progressRes = await fetch(
        `${apiBaseUrl}/success/onboarding/${customerId}/progress`,
        { headers }
      );
      const updatedProgress = await progressRes.json();
      setProgress(updatedProgress);
    } catch (err) {
      console.error('Error tracking milestone:', err);
    }
  };

  // ========================================================================
  // RENDERING HELPERS
  // ========================================================================

  const getPhaseIcon = (phase) => {
    const iconMap = {
      welcome: '👋',
      setup: '⚙️',
      first_success: '🎯',
      exploration: '🔍',
      optimization: '⚡',
      success: '🏆',
    };
    return iconMap[phase] || '📍';
  };

  const getMilestoneIcon = (milestone) => {
    const iconMap = {
      account_created: '📝',
      profile_completed: '✅',
      first_project: '📁',
      first_execution: '▶️',
      team_invited: '👥',
      integration_connected: '🔗',
      first_automation: '🤖',
      team_active: '🎉',
      expanded_usage: '📈',
      advanced_features: '⭐',
    };
    return iconMap[milestone] || '🎯';
  };

  const getMilestoneLabel = (milestone) => {
    return milestone.replace(/_/g, ' ').split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
  };

  // ========================================================================
  // MAIN RENDER
  // ========================================================================

  if (loading) return <div className="journey-loading">Loading onboarding journey...</div>;
  if (error) return <div className="journey-error">Error: {error}</div>;
  if (!progress) return <div className="journey-error">No onboarding data available</div>;

  const completionPercent = progress.completion_percent || 0;
  const daysRemaining = progress.days_remaining || 0;
  const segment = progress.segment || 'Unknown';
  const onTrack = progress.on_track !== false;

  return (
    <div className="onboarding-journey">
      {/* ================================================================ */}
      {/* HEADER */}
      {/* ================================================================ */}
      <div className="journey-header">
        <h1>Onboarding Journey</h1>
        <p className="segment-label">Segment: <strong>{segment.replace(/_/g, ' ').toUpperCase()}</strong></p>
      </div>

      {/* ================================================================ */}
      {/* CELEBRATION ANIMATION */}
      {/* ================================================================ */}
      {celebrationActive && (
        <div className="celebration-banner">
          <div className="celebration-content">
            <span className="celebration-emoji">🎉</span>
            <span className="celebration-text">{celebrationMessage}</span>
            <span className="celebration-emoji">🎉</span>
          </div>
          <div className="confetti"></div>
        </div>
      )}

      {/* ================================================================ */}
      {/* PROGRESS BAR */}
      {/* ================================================================ */}
      <div className="progress-card">
        <div className="progress-header">
          <h2>Progress</h2>
          <span className={`status-badge ${onTrack ? 'on-track' : 'off-track'}`}>
            {onTrack ? '✓ On Track' : '⚠️ Off Track'}
          </span>
        </div>

        <div className="progress-bar-container">
          <div className="progress-bar">
            <div
              className="progress-fill"
              style={{ width: `${completionPercent}%` }}
            >
              <span className="progress-percent">{completionPercent}%</span>
            </div>
          </div>
        </div>

        <div className="progress-stats">
          <div className="stat">
            <span className="stat-label">Current Phase</span>
            <span className="stat-value">
              {getPhaseIcon(progress.current_phase)} {progress.current_phase.replace(/_/g, ' ').toUpperCase()}
            </span>
          </div>
          <div className="stat">
            <span className="stat-label">Days in Onboarding</span>
            <span className="stat-value">{progress.days_in_onboarding} days</span>
          </div>
          <div className="stat">
            <span className="stat-label">Days Remaining</span>
            <span className={`stat-value ${daysRemaining < 0 ? 'overdue' : ''}`}>
              {daysRemaining > 0 ? `${daysRemaining} days` : 'Overdue'}
            </span>
          </div>
        </div>
      </div>

      {/* ================================================================ */}
      {/* JOURNEY TIMELINE */}
      {/* ================================================================ */}
      <div className="timeline-card">
        <h2>Journey Phases</h2>
        <div className="timeline">
          {journeyPhases.map((phase, idx) => (
            <div key={idx} className="timeline-item">
              <div className={`timeline-node ${phase.status}`}>
                <span className="node-icon">{getPhaseIcon(phase.name)}</span>
              </div>

              <div
                className={`timeline-content ${phase.status}`}
                onClick={() => setSelectedPhase(selectedPhase === idx ? null : idx)}
              >
                <h3 className="phase-name">{phase.name.replace(/_/g, ' ').toUpperCase()}</h3>

                {phase.status === 'completed' && (
                  <span className="phase-badge completed">✓ Completed</span>
                )}
                {phase.status === 'active' && (
                  <span className="phase-badge active">🔄 In Progress</span>
                )}
                {phase.status === 'upcoming' && (
                  <span className="phase-badge upcoming">Upcoming</span>
                )}

                {selectedPhase === idx && (
                  <div className="phase-details">
                    <p>Focus on this phase to build momentum and unlock the next stage.</p>
                    <button className="phase-action-btn">Get Help</button>
                  </div>
                )}
              </div>

              {idx < journeyPhases.length - 1 && (
                <div className="timeline-connector"></div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* ================================================================ */}
      {/* MILESTONE TRACKER */}
      {/* ================================================================ */}
      <div className="milestones-card">
        <h2>Key Milestones</h2>
        <div className="milestones-grid">
          {milestones.map((milestone, idx) => (
            <div key={idx} className={`milestone ${milestone.achieved ? 'achieved' : ''} ${milestone.current ? 'current' : ''}`}>
              <div className="milestone-icon">
                <span className="icon">{getMilestoneIcon(milestone.name)}</span>
                {milestone.achieved && <span className="checkmark">✓</span>}
              </div>

              <div className="milestone-info">
                <h4>{getMilestoneLabel(milestone.name)}</h4>
                {milestone.achieved && <p className="achieved-date">Achieved!</p>}
                {milestone.current && (
                  <>
                    <p className="current-label">Current Target</p>
                    <button
                      className="milestone-btn"
                      onClick={() => handleMilestoneAchieved(milestone.name)}
                    >
                      Mark as Complete
                    </button>
                  </>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ================================================================ */}
      {/* SUCCESS TIPS */}
      {/* ================================================================ */}
      <div className="tips-card">
        <h2>💡 Success Tips for {segment.replace(/_/g, ' ').toUpperCase()}</h2>
        <div className="tips-list">
          {segment === 'startup' && (
            <>
              <div className="tip">Start with a single workflow - don't try to automate everything at once</div>
              <div className="tip">Invite your team to collaborate - you're not alone in this</div>
              <div className="tip">Check out our community for best practices and advice</div>
            </>
          )}
          {segment === 'growing_team' && (
            <>
              <div className="tip">Set up team roles and permissions to scale collaboration</div>
              <div className="tip">Connect your existing tools for seamless integration</div>
              <div className="tip">Create shared automations your whole team can use</div>
            </>
          )}
          {segment === 'enterprise' && (
            <>
              <div className="tip">Work with our implementation team for custom setup</div>
              <div className="tip">Configure SSO and audit logging for compliance</div>
              <div className="tip">Build organization-wide automation standards</div>
            </>
          )}
          {segment === 'technical' && (
            <>
              <div className="tip">Explore our API and webhooks for advanced use cases</div>
              <div className="tip">Use our SDK for faster development</div>
              <div className="tip">Check out code examples and documentation</div>
            </>
          )}
        </div>
      </div>

      {/* ================================================================ */}
      {/* NEXT ACTIONS */}
      {/* ================================================================ */}
      <div className="next-actions-card">
        <h2>📋 What's Next?</h2>
        <p className="next-milestone-label">Current Target: {getMilestoneLabel(progress.next_milestone)}</p>
        <div className="action-items">
          <div className="action-item">
            <span className="action-number">1</span>
            <span className="action-text">Complete all activities in the current phase</span>
          </div>
          <div className="action-item">
            <span className="action-number">2</span>
            <span className="action-text">Achieve your next milestone</span>
          </div>
          <div className="action-item">
            <span className="action-number">3</span>
            <span className="action-text">Progress to the next phase of your journey</span>
          </div>
        </div>
        <p className="encouragement">You're {completionPercent}% of the way there! Keep going! 🚀</p>
      </div>
    </div>
  );
};

export default OnboardingJourney;
