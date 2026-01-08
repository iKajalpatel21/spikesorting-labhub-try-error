import React from 'react';
import { useWizard } from '../../context/WizardContext';
import '../../styles/WizardSteps.css';

export default function StepEnvironment() {
  const { wizardState, updateJobEnvironment } = useWizard();
  const { jobEnvironment, availableEnvironments } = wizardState;

  return (
    <div className="step-container">
      <h2>Step 3: Job Environment</h2>
      <p className="step-description">Select the execution environment for your job.</p>

      <div className="environments-grid">
        {availableEnvironments.map(env => (
          <div
            key={env.id}
            className={`environment-card ${jobEnvironment.preset === env.id ? 'selected' : ''}`}
            onClick={() => updateJobEnvironment(env.id)}
          >
            <div className="env-header">
              <h3>{env.name}</h3>
              {jobEnvironment.preset === env.id && <span className="selected-badge">✓ Selected</span>}
            </div>
            <p className="env-description">{env.description}</p>
          </div>
        ))}
      </div>

      <div className="form-section">
        <h3>📋 Environment Details</h3>
        <div className="env-details">
          <div className="detail-item">
            <strong>Selected:</strong> {availableEnvironments.find(e => e.id === jobEnvironment.preset)?.name}
          </div>
        </div>
      </div>

      <div className="info-box">
        <strong>💡 Info:</strong>
        <ul>
          <li><strong>Local CPU:</strong> Process on your local machine using CPU (slower)</li>
          <li><strong>Local GPU:</strong> Process on your local machine using GPU (faster, requires GPU)</li>
          <li><strong>Test Environment:</strong> Run in test mode for validation</li>
        </ul>
      </div>
    </div>
  );
}
