/**
 * Phase 22: Report Builder Component
 * Custom report creation, scheduling, export functionality
 * Template selection, metric configuration, delivery options
 */

import React, { useState, useEffect } from 'react';

/**
 * Report Builder Main Component
 * Allows creation, scheduling, and export of custom reports
 */
const ReportBuilder = ({ customerId }) => {
  const [step, setStep] = useState('template'); // template, config, schedule, confirm
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [reportConfig, setReportConfig] = useState({
    name: '',
    description: '',
    sections: [],
    metrics: [],
    filters: {},
    format: 'pdf',
  });
  const [scheduleConfig, setScheduleConfig] = useState({
    frequency: 'once',
    recipients: [],
    deliveryMethod: 'email',
  });
  const [loading, setLoading] = useState(true);

  // Fetch templates
  useEffect(() => {
    const fetchTemplates = async () => {
      try {
        const response = await fetch('/api/v1/analytics/reports/templates');
        const data = await response.json();
        setTemplates(data.templates);
        setLoading(false);
      } catch (error) {
        console.error('Failed to fetch templates:', error);
        setLoading(false);
      }
    };

    fetchTemplates();
  }, []);

  const handleTemplateSelect = (template) => {
    setSelectedTemplate(template);
    setReportConfig({
      ...reportConfig,
      name: `Custom ${template.name}`,
      description: template.description,
      sections: template.sections,
    });
  };

  const handleCreateReport = async () => {
    try {
      const response = await fetch('/api/v1/analytics/reports', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...reportConfig,
          customer_id: customerId,
        }),
      });
      const data = await response.json();
      
      if (scheduleConfig.frequency !== 'once') {
        // Schedule the report
        await fetch(`/api/v1/analytics/reports/${data.report_id}/schedule`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(scheduleConfig),
        });
      }

      // Generate immediately
      await fetch(`/api/v1/analytics/reports/${data.report_id}/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ format: reportConfig.format }),
      });

      alert('Report created successfully!');
      setStep('template');
    } catch (error) {
      console.error('Failed to create report:', error);
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-screen">Loading report builder...</div>;
  }

  return (
    <div className="bg-gray-50 min-h-screen p-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Report Builder</h1>
        <p className="text-gray-600 mt-2">Create custom reports tailored to your needs</p>
      </div>

      {/* Progress Indicator */}
      <div className="mb-8">
        <ProgressIndicator
          steps={['Select Template', 'Configure', 'Schedule', 'Review']}
          currentStep={step}
        />
      </div>

      {/* Step Content */}
      <div className="max-w-4xl mx-auto">
        {step === 'template' && (
          <TemplateSelection
            templates={templates}
            selectedTemplate={selectedTemplate}
            onSelect={(template) => {
              handleTemplateSelect(template);
              setStep('config');
            }}
          />
        )}

        {step === 'config' && (
          <ReportConfiguration
            config={reportConfig}
            setConfig={setReportConfig}
            onNext={() => setStep('schedule')}
            onBack={() => setStep('template')}
          />
        )}

        {step === 'schedule' && (
          <ReportScheduling
            schedule={scheduleConfig}
            setSchedule={setScheduleConfig}
            onNext={() => setStep('confirm')}
            onBack={() => setStep('config')}
          />
        )}

        {step === 'confirm' && (
          <ReportConfirmation
            config={reportConfig}
            schedule={scheduleConfig}
            onBack={() => setStep('schedule')}
            onConfirm={handleCreateReport}
          />
        )}
      </div>
    </div>
  );
};

/**
 * Progress Indicator
 */
const ProgressIndicator = ({ steps, currentStep }) => {
  const stepMap = { 'template': 0, 'config': 1, 'schedule': 2, 'confirm': 3 };
  const currentIndex = stepMap[currentStep] || 0;

  return (
    <div className="flex items-center justify-between">
      {steps.map((step, idx) => (
        <div key={idx} className="flex items-center">
          <div
            className={`w-10 h-10 rounded-full flex items-center justify-center font-bold ${
              idx <= currentIndex
                ? 'bg-blue-600 text-white'
                : 'bg-gray-300 text-gray-600'
            }`}
          >
            {idx + 1}
          </div>
          <span className={`ml-2 font-medium ${
            idx <= currentIndex ? 'text-gray-900' : 'text-gray-600'
          }`}>
            {step}
          </span>
          {idx < steps.length - 1 && (
            <div className={`mx-4 flex-1 h-1 ${
              idx < currentIndex ? 'bg-blue-600' : 'bg-gray-300'
            }`} />
          )}
        </div>
      ))}
    </div>
  );
};

/**
 * Template Selection
 */
const TemplateSelection = ({ templates, selectedTemplate, onSelect }) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      {templates.map((template, idx) => (
        <div
          key={idx}
          onClick={() => onSelect(template)}
          className={`p-6 rounded-lg border-2 cursor-pointer transition ${
            selectedTemplate?.template_id === template.template_id
              ? 'border-blue-600 bg-blue-50'
              : 'border-gray-200 bg-white hover:border-blue-300'
          }`}
        >
          <h3 className="text-lg font-bold text-gray-900">{template.name}</h3>
          <p className="text-gray-600 text-sm mt-2">{template.description}</p>
          <div className="mt-4">
            <p className="text-xs font-semibold text-gray-700 mb-2">Includes:</p>
            <div className="flex flex-wrap gap-2">
              {template.sections.map((section, sIdx) => (
                <span
                  key={sIdx}
                  className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded"
                >
                  {section}
                </span>
              ))}
            </div>
          </div>
          <p className="text-xs text-gray-500 mt-4">
            Est. generation: {template.estimated_generation_time_seconds}s
          </p>
        </div>
      ))}

      {/* Blank Template */}
      <div
        onClick={() => onSelect({ template_id: 'blank', name: 'Blank Report' })}
        className={`p-6 rounded-lg border-2 cursor-pointer transition flex items-center justify-center ${
          selectedTemplate?.template_id === 'blank'
            ? 'border-blue-600 bg-blue-50'
            : 'border-gray-200 bg-white hover:border-blue-300'
        }`}
      >
        <div className="text-center">
          <div className="text-4xl mb-2">+</div>
          <h3 className="text-lg font-bold text-gray-900">Create from Scratch</h3>
          <p className="text-gray-600 text-sm mt-2">Custom report with your metrics</p>
        </div>
      </div>
    </div>
  );
};

/**
 * Report Configuration
 */
const ReportConfiguration = ({ config, setConfig, onNext, onBack }) => {
  const allMetrics = [
    'Active Users',
    'Total Executions',
    'Success Rate',
    'Latency (P95)',
    'Error Rate',
    'Feature Adoption',
    'ROI %',
    'Payback Period',
    'Churn Risk',
    'Expansion Likelihood',
    'MRR',
    'ARR',
  ];

  const allSections = [
    'Key Metrics',
    'Trends',
    'Alerts',
    'Recommendations',
    'Usage Overview',
    'Performance Metrics',
    'ROI Analysis',
    'Predictions',
  ];

  return (
    <div className="bg-white rounded-lg shadow p-8">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Configure Report</h2>

      {/* Report Name and Description */}
      <div className="mb-6">
        <label className="block text-gray-700 font-semibold mb-2">Report Name</label>
        <input
          type="text"
          value={config.name}
          onChange={(e) => setConfig({ ...config, name: e.target.value })}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-600"
        />
      </div>

      <div className="mb-6">
        <label className="block text-gray-700 font-semibold mb-2">Description</label>
        <textarea
          value={config.description}
          onChange={(e) => setConfig({ ...config, description: e.target.value })}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-600"
          rows="3"
        />
      </div>

      {/* Sections */}
      <div className="mb-6">
        <label className="block text-gray-700 font-semibold mb-2">Report Sections</label>
        <div className="grid grid-cols-2 gap-3">
          {allSections.map((section) => (
            <label key={section} className="flex items-center">
              <input
                type="checkbox"
                checked={config.sections.includes(section)}
                onChange={(e) => {
                  if (e.target.checked) {
                    setConfig({
                      ...config,
                      sections: [...config.sections, section],
                    });
                  } else {
                    setConfig({
                      ...config,
                      sections: config.sections.filter((s) => s !== section),
                    });
                  }
                }}
                className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-600"
              />
              <span className="ml-2 text-gray-700">{section}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Metrics */}
      <div className="mb-6">
        <label className="block text-gray-700 font-semibold mb-2">Metrics to Include</label>
        <div className="grid grid-cols-2 gap-3">
          {allMetrics.map((metric) => (
            <label key={metric} className="flex items-center">
              <input
                type="checkbox"
                checked={config.metrics.includes(metric)}
                onChange={(e) => {
                  if (e.target.checked) {
                    setConfig({
                      ...config,
                      metrics: [...config.metrics, metric],
                    });
                  } else {
                    setConfig({
                      ...config,
                      metrics: config.metrics.filter((m) => m !== metric),
                    });
                  }
                }}
                className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-600"
              />
              <span className="ml-2 text-gray-700">{metric}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Export Format */}
      <div className="mb-8">
        <label className="block text-gray-700 font-semibold mb-2">Export Format</label>
        <select
          value={config.format}
          onChange={(e) => setConfig({ ...config, format: e.target.value })}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-600"
        >
          <option value="pdf">PDF</option>
          <option value="csv">CSV</option>
          <option value="excel">Excel</option>
          <option value="json">JSON</option>
        </select>
      </div>

      {/* Navigation */}
      <div className="flex gap-4">
        <button
          onClick={onBack}
          className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 font-medium"
        >
          Back
        </button>
        <button
          onClick={onNext}
          className="ml-auto px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
        >
          Next
        </button>
      </div>
    </div>
  );
};

/**
 * Report Scheduling
 */
const ReportScheduling = ({ schedule, setSchedule, onNext, onBack }) => {
  const [addEmail, setAddEmail] = useState('');

  return (
    <div className="bg-white rounded-lg shadow p-8">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Schedule Report</h2>

      {/* Frequency */}
      <div className="mb-6">
        <label className="block text-gray-700 font-semibold mb-2">Frequency</label>
        <select
          value={schedule.frequency}
          onChange={(e) => setSchedule({ ...schedule, frequency: e.target.value })}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-600"
        >
          <option value="once">Generate Once</option>
          <option value="daily">Daily</option>
          <option value="weekly">Weekly</option>
          <option value="monthly">Monthly</option>
          <option value="quarterly">Quarterly</option>
        </select>
      </div>

      {/* Delivery Method */}
      <div className="mb-6">
        <label className="block text-gray-700 font-semibold mb-2">Delivery Method</label>
        <select
          value={schedule.deliveryMethod}
          onChange={(e) => setSchedule({ ...schedule, deliveryMethod: e.target.value })}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-600"
        >
          <option value="email">Email</option>
          <option value="cloud">Cloud Storage</option>
          <option value="slack">Slack</option>
          <option value="api">API</option>
        </select>
      </div>

      {/* Recipients (for email) */}
      {schedule.deliveryMethod === 'email' && (
        <div className="mb-6">
          <label className="block text-gray-700 font-semibold mb-2">Recipients</label>
          <div className="flex gap-2 mb-3">
            <input
              type="email"
              value={addEmail}
              onChange={(e) => setAddEmail(e.target.value)}
              placeholder="Enter email address"
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-600"
            />
            <button
              onClick={() => {
                if (addEmail) {
                  setSchedule({
                    ...schedule,
                    recipients: [...schedule.recipients, addEmail],
                  });
                  setAddEmail('');
                }
              }}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 font-medium"
            >
              Add
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {schedule.recipients.map((email, idx) => (
              <div
                key={idx}
                className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm flex items-center gap-2"
              >
                {email}
                <button
                  onClick={() =>
                    setSchedule({
                      ...schedule,
                      recipients: schedule.recipients.filter((_, i) => i !== idx),
                    })
                  }
                  className="text-blue-600 hover:text-blue-800"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Navigation */}
      <div className="flex gap-4 mt-8">
        <button
          onClick={onBack}
          className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 font-medium"
        >
          Back
        </button>
        <button
          onClick={onNext}
          className="ml-auto px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
        >
          Review & Create
        </button>
      </div>
    </div>
  );
};

/**
 * Report Confirmation
 */
const ReportConfirmation = ({ config, schedule, onBack, onConfirm }) => {
  const [isCreating, setIsCreating] = useState(false);

  const handleConfirm = async () => {
    setIsCreating(true);
    await onConfirm();
    setIsCreating(false);
  };

  return (
    <div className="bg-white rounded-lg shadow p-8">
      <h2 className="text-2xl font-bold text-gray-900 mb-6">Review Report</h2>

      <div className="space-y-6">
        {/* Configuration Summary */}
        <div className="border-l-4 border-blue-600 pl-4">
          <h3 className="font-semibold text-gray-900 mb-2">Report Configuration</h3>
          <div className="text-gray-700 space-y-1 text-sm">
            <p><strong>Name:</strong> {config.name}</p>
            <p><strong>Format:</strong> {config.format.toUpperCase()}</p>
            <p><strong>Sections:</strong> {config.sections.length}</p>
            <p><strong>Metrics:</strong> {config.metrics.length}</p>
          </div>
        </div>

        {/* Schedule Summary */}
        <div className="border-l-4 border-green-600 pl-4">
          <h3 className="font-semibold text-gray-900 mb-2">Schedule</h3>
          <div className="text-gray-700 space-y-1 text-sm">
            <p><strong>Frequency:</strong> {schedule.frequency}</p>
            <p><strong>Delivery:</strong> {schedule.deliveryMethod}</p>
            {schedule.deliveryMethod === 'email' && (
              <p><strong>Recipients:</strong> {schedule.recipients.length}</p>
            )}
          </div>
        </div>
      </div>

      {/* Navigation */}
      <div className="flex gap-4 mt-8">
        <button
          onClick={onBack}
          className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 font-medium"
        >
          Back
        </button>
        <button
          onClick={handleConfirm}
          disabled={isCreating}
          className="ml-auto px-8 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isCreating ? 'Creating...' : 'Create Report'}
        </button>
      </div>
    </div>
  );
};

export default ReportBuilder;
