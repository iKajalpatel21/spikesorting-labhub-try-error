import React from 'react';
import { useWizard } from '../../context/WizardContext';
import '../../styles/WizardSteps.css';

export default function StepPipeline() {
  const { wizardState, updateSelectedPipeline } = useWizard();
  const { availablePipelines, selectedPipeline } = wizardState;

  return (
    <div className="step-container">
      <h2>Step 2: Apply Pipeline</h2>
      <p className="step-description">Select a processing pipeline for your recording.</p>

      {availablePipelines.length === 0 ? (
        <div className="empty-state">
          <p>No pipelines available. Create one in "Add New Pipeline" section.</p>
        </div>
      ) : (
        <div className="pipelines-list">
          {availablePipelines.map(pipeline => (
            <div
              key={pipeline.id}
              className={`pipeline-card ${selectedPipeline === pipeline.id ? 'selected' : ''}`}
              onClick={() => updateSelectedPipeline(pipeline.id)}
            >
              <div className="pipeline-header">
                <h3>{pipeline.name}</h3>
                {selectedPipeline === pipeline.id && <span className="selected-badge">✓ Selected</span>}
              </div>
              <p className="pipeline-description">{pipeline.description}</p>
              <div className="pipeline-meta">
                <span className="steps-count">📋 {pipeline.steps_count} steps</span>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="info-box">
        <strong>💡 Info:</strong> The selected pipeline will process your recording with predefined steps and configurations.
      </div>
    </div>
  );
}
