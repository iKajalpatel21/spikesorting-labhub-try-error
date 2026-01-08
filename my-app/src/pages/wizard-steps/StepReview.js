import React, { useState } from 'react';
import { useWizard } from '../../context/WizardContext';
import '../../styles/WizardSteps.css';

export default function StepReview({ onComplete }) {
  const { wizardState, resetWizard } = useWizard();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const { recording, selectedPipeline, jobEnvironment, availablePipelines, availableEnvironments } = wizardState;

  const selectedPipelineData = availablePipelines.find(p => p.id === selectedPipeline);
  const selectedEnvData = availableEnvironments.find(e => e.id === jobEnvironment.preset);

  const handleSubmit = async () => {
    setIsSubmitting(true);
    setError('');

    try {
      // Prepare form data with files
      const formData = new FormData();
      formData.append('bin_file', recording.binFile);
      formData.append('probe_file', recording.probeFile);
      formData.append('sampling_rate', recording.samplingRate);
      formData.append('num_channels', recording.numChannels);
      formData.append('gain_to_microvolts', recording.gainToMicroVolts);
      formData.append('offset_to_microvolts', recording.offsetToMicroVolts);
      formData.append('bad_channels', JSON.stringify(recording.badChannels));
      formData.append('pipeline_id', selectedPipeline);
      formData.append('job_environment', jobEnvironment.preset);

      // TODO: Replace with actual API endpoint
      const response = await fetch('/api/jobs/create/', {
        method: 'POST',
        headers: {
          'Authorization': `Token ${localStorage.getItem('token')}`,
        },
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Failed to create job');
      }

      const data = await response.json();
      alert(`✅ Job created successfully! Job ID: ${data.id}`);
      
      // Reset wizard and go back to dashboard
      resetWizard();
      onComplete();
    } catch (err) {
      setError(err.message || 'Failed to submit job');
      console.error('Error:', err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="step-container">
      <h2>Step 4: Review & Submit</h2>
      <p className="step-description">Review all settings before submitting your job.</p>

      <div className="review-sections">
        {/* Recording Summary */}
        <div className="review-section">
          <h3>📁 Recording Configuration</h3>
          <div className="review-items">
            <div className="review-item">
              <span className="label">Binary File:</span>
              <span className="value">{recording.binFile?.name || 'Not selected'}</span>
            </div>
            <div className="review-item">
              <span className="label">Probe File:</span>
              <span className="value">{recording.probeFile?.name || 'Not selected'}</span>
            </div>
            <div className="review-item">
              <span className="label">Sampling Rate:</span>
              <span className="value">{recording.samplingRate} Hz</span>
            </div>
            <div className="review-item">
              <span className="label">Number of Channels:</span>
              <span className="value">{recording.numChannels}</span>
            </div>
            <div className="review-item">
              <span className="label">Gain to µV:</span>
              <span className="value">{recording.gainToMicroVolts}</span>
            </div>
            <div className="review-item">
              <span className="label">Offset to µV:</span>
              <span className="value">{recording.offsetToMicroVolts}</span>
            </div>
            {recording.badChannels.length > 0 && (
              <div className="review-item">
                <span className="label">Bad Channels:</span>
                <span className="value">{recording.badChannels.join(', ')}</span>
              </div>
            )}
          </div>
        </div>

        {/* Pipeline Summary */}
        <div className="review-section">
          <h3>🔧 Pipeline</h3>
          <div className="review-items">
            <div className="review-item">
              <span className="label">Pipeline Name:</span>
              <span className="value">{selectedPipelineData?.name || 'Not selected'}</span>
            </div>
            <div className="review-item">
              <span className="label">Description:</span>
              <span className="value">{selectedPipelineData?.description || '-'}</span>
            </div>
            <div className="review-item">
              <span className="label">Number of Steps:</span>
              <span className="value">{selectedPipelineData?.steps_count || 0}</span>
            </div>
          </div>
        </div>

        {/* Environment Summary */}
        <div className="review-section">
          <h3>⚙️ Job Environment</h3>
          <div className="review-items">
            <div className="review-item">
              <span className="label">Environment:</span>
              <span className="value">{selectedEnvData?.name || 'Not selected'}</span>
            </div>
            <div className="review-item">
              <span className="label">Description:</span>
              <span className="value">{selectedEnvData?.description || '-'}</span>
            </div>
          </div>
        </div>
      </div>

      {error && (
        <div className="error-message">
          ❌ {error}
        </div>
      )}

      <button
        className="submit-button"
        onClick={handleSubmit}
        disabled={isSubmitting}
      >
        {isSubmitting ? '⏳ Submitting...' : '✅ Submit Job'}
      </button>
    </div>
  );
}
