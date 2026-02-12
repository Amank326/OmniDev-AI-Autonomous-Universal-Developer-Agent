/**
 * ReportBuilder Component
 * Interactive report creation and customization interface
 */

import React, { useState, useCallback } from 'react';

const ReportBuilder = ({ workspaceId, onReportGenerated, onError }) => {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    name: '',
    reportType: 'task_summary',
    timePeriod: 7,
    format: 'json',
    sections: [],
    includeCharts: true,
    includeSummary: true,
    includeRecommendations: true,
  });

  const [generatedReportId, setGeneratedReportId] = useState(null);
  const [generating, setGenerating] = useState(false);
  const [progress, setProgress] = useState(0);
  const [savedReports, setSavedReports] = useState([]);
  const [loadingSavedReports, setLoadingSavedReports] = useState(false);

  const reportTypes = [
    { value: 'task_summary', label: '📋 Task Summary', description: 'Overview of task completion and status' },
    { value: 'agent_performance', label: '🤖 Agent Performance', description: 'Agent efficiency and task completion metrics' },
    { value: 'system_health', label: '🏥 System Health', description: 'System status and resource utilization' },
    { value: 'trends', label: '📈 Trends Analysis', description: 'Historical trends and forecasts' },
    { value: 'custom', label: '⚙️ Custom', description: 'Build a custom report with selected sections' },
  ];

  const availableSections = {
    task_summary: ['overview', 'status_breakdown', 'timeline', 'top_performers'],
    agent_performance: ['agent_stats', 'workload', 'success_rates', 'trends'],
    system_health: ['overall_health', 'component_status', 'resource_usage', 'alerts'],
    trends: ['metric_trends', 'patterns', 'forecasts', 'recommendations'],
  };

  const formats = [
    { value: 'json', label: 'JSON', icon: '📄' },
    { value: 'csv', label: 'CSV', icon: '📊' },
    { value: 'pdf', label: 'PDF', icon: '📑' },
    { value: 'html', label: 'HTML', icon: '🌐' },
    { value: 'markdown', label: 'Markdown', icon: '📝' },
  ];

  // Fetch saved reports
  const loadSavedReports = useCallback(async () => {
    setLoadingSavedReports(true);
    try {
      const response = await fetch(
        `/api/v1/analytics/reports?workspace_id=${workspaceId}&limit=10`
      );
      if (response.ok) {
        const data = await response.json();
        setSavedReports(data.reports || []);
      }
    } catch (error) {
      onError?.(error);
    } finally {
      setLoadingSavedReports(false);
    }
  }, [workspaceId, onError]);

  // Generate report
  const handleGenerateReport = async () => {
    if (!formData.name) {
      onError?.(new Error('Please enter a report name'));
      return;
    }

    setGenerating(true);
    setProgress(0);

    try {
      const response = await fetch('/api/v1/analytics/reports/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          workspace_id: workspaceId,
          report_name: formData.name,
          report_type: formData.reportType,
          time_period_days: formData.timePeriod,
          format: formData.format,
          sections: formData.sections.length > 0 ? formData.sections : undefined,
        }),
      });

      if (!response.ok) throw new Error('Failed to generate report');

      const data = await response.json();
      setGeneratedReportId(data.report_id);
      setProgress(100);

      // Simulate progress updates
      for (let i = 0; i < 5; i++) {
        await new Promise(resolve => setTimeout(resolve, 300));
        setProgress(20 + (i * 15));
      }

      onReportGenerated?.(data);
      loadSavedReports();
      setStep(4);
    } catch (error) {
      onError?.(error);
    } finally {
      setGenerating(false);
    }
  };

  // Export report
  const handleExportReport = async (reportId, format) => {
    try {
      const response = await fetch(`/api/v1/analytics/reports/${reportId}/export`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ format }),
      });

      if (!response.ok) throw new Error('Failed to export report');

      const data = await response.json();
      // In real app, would trigger download
      window.open(data.download_url);
    } catch (error) {
      onError?.(error);
    }
  };

  return (
    <div className="report-builder">
      <style>{`
        .report-builder {
          max-width: 900px;
          margin: 0 auto;
          padding: 20px;
        }
        
        .rb-header {
          margin-bottom: 30px;
        }
        
        .rb-title {
          font-size: 28px;
          font-weight: bold;
          color: #333;
          margin-bottom: 10px;
        }
        
        .rb-subtitle {
          color: #666;
          font-size: 14px;
        }
        
        .stepper {
          display: flex;
          gap: 20px;
          margin-bottom: 30px;
          position: relative;
        }
        
        .step {
          flex: 1;
          text-align: center;
        }
        
        .step-number {
          width: 40px;
          height: 40px;
          margin: 0 auto 8px;
          border-radius: 50%;
          background: #e5e7eb;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: bold;
          color: #666;
          transition: all 0.2s;
        }
        
        .step.active .step-number {
          background: #2563eb;
          color: white;
        }
        
        .step.completed .step-number {
          background: #10b981;
          color: white;
        }
        
        .step-label {
          font-size: 13px;
          color: #666;
          font-weight: 500;
        }
        
        .step.active .step-label {
          color: #2563eb;
          font-weight: 600;
        }
        
        .card {
          background: white;
          border: 1px solid #e5e7eb;
          border-radius: 8px;
          padding: 25px;
          margin-bottom: 20px;
        }
        
        .card-title {
          font-size: 18px;
          font-weight: 600;
          color: #333;
          margin-bottom: 20px;
        }
        
        .form-group {
          margin-bottom: 20px;
        }
        
        .form-label {
          display: block;
          font-weight: 600;
          margin-bottom: 8px;
          color: #333;
          font-size: 14px;
        }
        
        .form-input,
        .form-select,
        .form-textarea {
          width: 100%;
          padding: 10px;
          border: 1px solid #d1d5db;
          border-radius: 4px;
          font-size: 14px;
          font-family: inherit;
        }
        
        .form-input:focus,
        .form-select:focus,
        .form-textarea:focus {
          outline: none;
          border-color: #2563eb;
          box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
        }
        
        .form-helper {
          font-size: 12px;
          color: #666;
          margin-top: 4px;
        }
        
        .grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
          gap: 12px;
        }
        
        .card-option {
          padding: 15px;
          border: 2px solid #e5e7eb;
          border-radius: 8px;
          cursor: pointer;
          transition: all 0.2s;
          text-align: center;
        }
        
        .card-option:hover {
          border-color: #2563eb;
          background: #f0f9ff;
        }
        
        .card-option.selected {
          border-color: #2563eb;
          background: #eff6ff;
        }
        
        .card-option-icon {
          font-size: 28px;
          margin-bottom: 8px;
        }
        
        .card-option-label {
          font-weight: 600;
          font-size: 13px;
          color: #333;
          margin-bottom: 4px;
        }
        
        .card-option-desc {
          font-size: 11px;
          color: #666;
        }
        
        .checkbox-group {
          display: flex;
          flex-direction: column;
          gap: 10px;
        }
        
        .checkbox-item {
          display: flex;
          align-items: center;
          gap: 8px;
        }
        
        .checkbox-item input[type="checkbox"] {
          cursor: pointer;
          width: 18px;
          height: 18px;
        }
        
        .checkbox-item label {
          cursor: pointer;
          font-size: 14px;
          color: #333;
        }
        
        .buttons {
          display: flex;
          gap: 10px;
          justify-content: space-between;
          margin-top: 25px;
        }
        
        .btn {
          padding: 10px 20px;
          border: none;
          border-radius: 4px;
          font-weight: 600;
          cursor: pointer;
          font-size: 14px;
          transition: all 0.2s;
        }
        
        .btn-primary {
          background: #2563eb;
          color: white;
        }
        
        .btn-primary:hover {
          background: #1d4ed8;
        }
        
        .btn-primary:disabled {
          background: #9ca3af;
          cursor: not-allowed;
        }
        
        .btn-secondary {
          background: #e5e7eb;
          color: #333;
        }
        
        .btn-secondary:hover {
          background: #d1d5db;
        }
        
        .progress-bar {
          width: 100%;
          height: 6px;
          background: #e5e7eb;
          border-radius: 3px;
          overflow: hidden;
          margin-bottom: 10px;
        }
        
        .progress-fill {
          height: 100%;
          background: linear-gradient(90deg, #2563eb, #10b981);
          transition: width 0.3s;
        }
        
        .success-message {
          background: #d1fae5;
          border-left: 4px solid #10b981;
          padding: 15px;
          border-radius: 4px;
          margin-bottom: 20px;
        }
        
        .success-message strong {
          color: #065f46;
        }
        
        .success-message p {
          color: #047857;
          font-size: 14px;
          margin: 5px 0;
        }
        
        .saved-reports {
          margin-top: 20px;
        }
        
        .reports-list {
          display: grid;
          gap: 10px;
          max-height: 300px;
          overflow-y: auto;
        }
        
        .report-item {
          padding: 12px;
          background: #f9fafb;
          border: 1px solid #e5e7eb;
          border-radius: 4px;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        
        .report-item-info {
          flex: 1;
        }
        
        .report-item-name {
          font-weight: 600;
          color: #333;
          font-size: 13px;
        }
        
        .report-item-meta {
          font-size: 12px;
          color: #666;
          margin-top: 3px;
        }
        
        .report-item-actions {
          display: flex;
          gap: 5px;
        }
        
        .btn-small {
          padding: 4px 8px;
          font-size: 11px;
          background: white;
          border: 1px solid #d1d5db;
          border-radius: 4px;
          cursor: pointer;
          transition: all 0.2s;
        }
        
        .btn-small:hover {
          background: #2563eb;
          color: white;
          border-color: #2563eb;
        }
      `}</style>

      <div className="rb-header">
        <div className="rb-title">📋 Report Builder</div>
        <div className="rb-subtitle">Create comprehensive reports for your workspace</div>
      </div>

      <div className="stepper">
        {['Details', 'Content', 'Format', 'Review'].map((label, idx) => (
          <div key={idx + 1} className={`step ${step > idx + 1 ? 'completed' : ''} ${step === idx + 1 ? 'active' : ''}`}>
            <div className="step-number">{step > idx + 1 ? '✓' : idx + 1}</div>
            <div className="step-label">{label}</div>
          </div>
        ))}
      </div>

      {step === 1 && (
        <div className="card">
          <div className="card-title">Report Details</div>

          <div className="form-group">
            <label className="form-label">Report Name *</label>
            <input
              type="text"
              className="form-input"
              placeholder="e.g., Weekly Task Summary"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Report Type *</label>
            <div className="grid">
              {reportTypes.map(type => (
                <div
                  key={type.value}
                  className={`card-option ${formData.reportType === type.value ? 'selected' : ''}`}
                  onClick={() => setFormData({ ...formData, reportType: type.value })}
                >
                  <div className="card-option-label">{type.label}</div>
                  <div className="card-option-desc">{type.description}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Time Period</label>
            <select
              className="form-select"
              value={formData.timePeriod}
              onChange={(e) => setFormData({ ...formData, timePeriod: parseInt(e.target.value) })}
            >
              <option value={1}>Last 24 hours</option>
              <option value={7}>Last 7 days</option>
              <option value={30}>Last 30 days</option>
              <option value={90}>Last 90 days</option>
            </select>
          </div>

          <div className="buttons">
            <button className="btn btn-secondary">Cancel</button>
            <button className="btn btn-primary" onClick={() => setStep(2)}>
              Next: Select Content
            </button>
          </div>
        </div>
      )}

      {step === 2 && (
        <div className="card">
          <div className="card-title">Report Content</div>

          {formData.reportType !== 'custom' && (
            <div className="form-group">
              <label className="form-label">Included Sections</label>
              <div className="checkbox-group">
                {(availableSections[formData.reportType] || []).map(section => (
                  <div key={section} className="checkbox-item">
                    <input type="checkbox" id={section} defaultChecked />
                    <label htmlFor={section}>{section.replace('_', ' ').toUpperCase()}</label>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="form-group">
            <label className="form-label">Additional Options</label>
            <div className="checkbox-group">
              <div className="checkbox-item">
                <input
                  type="checkbox"
                  id="charts"
                  checked={formData.includeCharts}
                  onChange={(e) => setFormData({ ...formData, includeCharts: e.target.checked })}
                />
                <label htmlFor="charts">Include Charts & Visualizations</label>
              </div>
              <div className="checkbox-item">
                <input
                  type="checkbox"
                  id="summary"
                  checked={formData.includeSummary}
                  onChange={(e) => setFormData({ ...formData, includeSummary: e.target.checked })}
                />
                <label htmlFor="summary">Include Executive Summary</label>
              </div>
              <div className="checkbox-item">
                <input
                  type="checkbox"
                  id="recommendations"
                  checked={formData.includeRecommendations}
                  onChange={(e) => setFormData({ ...formData, includeRecommendations: e.target.checked })}
                />
                <label htmlFor="recommendations">Include Recommendations</label>
              </div>
            </div>
          </div>

          <div className="buttons">
            <button className="btn btn-secondary" onClick={() => setStep(1)}>
              Back
            </button>
            <button className="btn btn-primary" onClick={() => setStep(3)}>
              Next: Select Format
            </button>
          </div>
        </div>
      )}

      {step === 3 && (
        <div className="card">
          <div className="card-title">Report Format</div>

          <div className="form-group">
            <label className="form-label">Output Format *</label>
            <div className="grid">
              {formats.map(fmt => (
                <div
                  key={fmt.value}
                  className={`card-option ${formData.format === fmt.value ? 'selected' : ''}`}
                  onClick={() => setFormData({ ...formData, format: fmt.value })}
                >
                  <div className="card-option-icon">{fmt.icon}</div>
                  <div className="card-option-label">{fmt.label}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="buttons">
            <button className="btn btn-secondary" onClick={() => setStep(2)}>
              Back
            </button>
            <button className="btn btn-primary" onClick={() => setStep(4)}>
              Review & Generate
            </button>
          </div>
        </div>
      )}

      {step === 4 && !generatedReportId && (
        <div className="card">
          <div className="card-title">Review & Generate</div>

          <div style={{ marginBottom: '20px' }}>
            <p style={{ marginBottom: '8px' }}>
              <strong>Report Name:</strong> {formData.name}
            </p>
            <p style={{ marginBottom: '8px' }}>
              <strong>Type:</strong> {reportTypes.find(t => t.value === formData.reportType)?.label}
            </p>
            <p style={{ marginBottom: '8px' }}>
              <strong>Period:</strong> Last {formData.timePeriod} days
            </p>
            <p style={{ marginBottom: '8px' }}>
              <strong>Format:</strong> {formats.find(f => f.value === formData.format)?.label}
            </p>
          </div>

          <div className="buttons">
            <button className="btn btn-secondary" onClick={() => setStep(3)}>
              Back
            </button>
            <button
              className="btn btn-primary"
              onClick={handleGenerateReport}
              disabled={generating}
            >
              {generating ? `Generating... ${progress}%` : 'Generate Report'}
            </button>
          </div>
        </div>
      )}

      {generatedReportId && (
        <div className="card">
          <div className="success-message">
            <strong>✓ Report Generated Successfully!</strong>
            <p>Your report has been created and is ready for download.</p>
          </div>

          <div className="form-group">
            <label className="form-label">Export Report</label>
            <div className="grid">
              {formats.map(fmt => (
                <button
                  key={fmt.value}
                  className="btn btn-secondary"
                  onClick={() => handleExportReport(generatedReportId, fmt.value)}
                  style={{ width: '100%' }}
                >
                  {fmt.icon} {fmt.label}
                </button>
              ))}
            </div>
          </div>

          <div className="saved-reports">
            <h3 style={{ marginBottom: '10px', fontSize: '14px', fontWeight: '600' }}>Recent Reports</h3>
            {loadingSavedReports ? (
              <p style={{ textAlign: 'center', color: '#666' }}>Loading reports...</p>
            ) : savedReports.length > 0 ? (
              <div className="reports-list">
                {savedReports.map((report) => (
                  <div key={report.id} className="report-item">
                    <div className="report-item-info">
                      <div className="report-item-name">{report.name}</div>
                      <div className="report-item-meta">
                        {report.type} • {new Date(report.generated_at).toLocaleDateString()}
                      </div>
                    </div>
                    <div className="report-item-actions">
                      <button className="btn-small">View</button>
                      <button className="btn-small">Delete</button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p style={{ textAlign: 'center', color: '#999', fontSize: '13px' }}>No saved reports</p>
            )}
          </div>

          <div className="buttons">
            <button
              className="btn btn-primary"
              onClick={() => {
                setGeneratedReportId(null);
                setFormData({
                  name: '',
                  reportType: 'task_summary',
                  timePeriod: 7,
                  format: 'json',
                  sections: [],
                  includeCharts: true,
                  includeSummary: true,
                  includeRecommendations: true,
                });
                setStep(1);
              }}
            >
              Create Another Report
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ReportBuilder;
