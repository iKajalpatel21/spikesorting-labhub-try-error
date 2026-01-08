import React, { useRef } from 'react';
import { useWizard } from '../../context/WizardContext';
import '../../styles/WizardSteps.css';

export default function StepRecording() {
  const { wizardState, updateRecording } = useWizard();
  const binInputRef = useRef();
  const probeInputRef = useRef();
  const recording = wizardState.recording;

  const handleBinFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      updateRecording({ binFile: file });
    }
  };

  const handleProbeFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      updateRecording({ probeFile: file });
    }
  };

  const handleParameterChange = (field, value) => {
    const numValue = parseFloat(value);
    updateRecording({ [field]: isNaN(numValue) ? value : numValue });
  };

  const handleBadChannelToggle = (channel) => {
    const updated = recording.badChannels.includes(channel)
      ? recording.badChannels.filter(c => c !== channel)
      : [...recording.badChannels, channel];
    updateRecording({ badChannels: updated });
  };

  return (
    <div className="step-container">
      <h2>Step 1: Create New Recording</h2>
      <p className="step-description">Upload your recording files and configure the recording parameters.</p>

      <div className="form-section">
        <h3>📁 Upload Files</h3>

        <div className="form-group">
          <label>Binary File (.bin)</label>
          <input
            ref={binInputRef}
            type="file"
            accept=".bin"
            onChange={handleBinFileSelect}
            className="file-input"
          />
          {recording.binFile && (
            <div className="file-info">✅ {recording.binFile.name}</div>
          )}
        </div>

        <div className="form-group">
          <label>Probe File (.prb, .json)</label>
          <input
            ref={probeInputRef}
            type="file"
            accept=".prb,.json"
            onChange={handleProbeFileSelect}
            className="file-input"
          />
          {recording.probeFile && (
            <div className="file-info">✅ {recording.probeFile.name}</div>
          )}
        </div>
      </div>

      <div className="form-section">
        <h3>⚙️ Recording Parameters</h3>

        <div className="form-row">
          <div className="form-group">
            <label>Sampling Rate (Hz)</label>
            <input
              type="number"
              value={recording.samplingRate}
              onChange={(e) => handleParameterChange('samplingRate', e.target.value)}
              className="form-input"
            />
          </div>

          <div className="form-group">
            <label>Number of Channels</label>
            <input
              type="number"
              value={recording.numChannels}
              onChange={(e) => handleParameterChange('numChannels', e.target.value)}
              className="form-input"
            />
          </div>
        </div>

        <div className="form-row">
          <div className="form-group">
            <label>Gain to µV</label>
            <input
              type="number"
              step="0.001"
              value={recording.gainToMicroVolts}
              onChange={(e) => handleParameterChange('gainToMicroVolts', e.target.value)}
              className="form-input"
            />
          </div>

          <div className="form-group">
            <label>Offset to µV</label>
            <input
              type="number"
              step="0.001"
              value={recording.offsetToMicroVolts}
              onChange={(e) => handleParameterChange('offsetToMicroVolts', e.target.value)}
              className="form-input"
            />
          </div>
        </div>
      </div>

      <div className="form-section">
        <h3>❌ Bad Channels</h3>
        <p className="section-description">Select channels to exclude from analysis</p>
        
        <div className="bad-channels-grid">
          {Array.from({ length: recording.numChannels }).map((_, idx) => (
            <button
              key={idx}
              className={`channel-btn ${recording.badChannels.includes(idx) ? 'selected' : ''}`}
              onClick={() => handleBadChannelToggle(idx)}
              title={`Channel ${idx}`}
            >
              {idx}
            </button>
          ))}
        </div>
        {recording.badChannels.length > 0 && (
          <div className="bad-channels-list">
            <strong>Bad channels:</strong> {recording.badChannels.join(', ')}
          </div>
        )}
      </div>

      <div className="validation-note">
        <strong>✓ Validation:</strong> All required files and parameters are filled
      </div>
    </div>
  );
}
