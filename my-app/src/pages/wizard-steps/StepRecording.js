import React, { useRef, useState } from 'react';
import { useWizard } from '../../context/WizardContext';
import '../../styles/WizardSteps.css';

export default function StepRecording() {
    const { wizardState, updateRecording } = useWizard();
    const binInputRef = useRef();
    const probeInputRef = useRef();
    const recording = wizardState.recording;
    const [removeChannels, setRemoveChannels] = useState([]);

    const validateJsonFile = (file) => {
        const fileName = file.name.toLowerCase();
        return fileName.endsWith('.json');
    };

    const handleBinFileSelect = (e) => {
        const file = e.target.files[0];
        if (file) {
            if (!validateJsonFile(file)) {
                alert('Please select a JSON file (.json extension required)');
                e.target.value = '';
                return;
            }
            updateRecording({ binFile: file });
        }
    };

    const handleProbeFileSelect = (e) => {
        const file = e.target.files[0];
        if (file) {
            if (!validateJsonFile(file)) {
                alert('Please select a JSON file (.json extension required)');
                e.target.value = '';
                return;
            }
            updateRecording({ probeFile: file });
        }
    };

    const handleParameterChange = (field, value) => {
        if (field === 'numChannels') {
            const intValue = parseInt(value, 10);
            updateRecording({ [field]: isNaN(intValue) ? value : intValue });
        } else {
            const numValue = parseFloat(value);
            updateRecording({ [field]: isNaN(numValue) ? value : numValue });
        }
    };

    const handleRemoveChannelToggle = (channel) => {
        const updated = removeChannels.includes(channel)
            ? removeChannels.filter(c => c !== channel)
            : [...removeChannels, channel];
        setRemoveChannels(updated);
    };

    const handleBadChannelToggle = (channel) => {
        const updated = recording.badChannels.includes(channel)
            ? recording.badChannels.filter(c => c !== channel)
            : [...recording.badChannels, channel];
        updateRecording({ badChannels: updated });
    };

    return (
        <div className="step-container recording-step">
            <h2>Step 1: Create New Recording</h2>

            <div className="recording-form">
                {/* Binfile */}
                <div className="form-group recording-form-group">
                    <label>Binfile:</label>
                    <input
                        ref={binInputRef}
                        type="file"
                        accept="application/json,.json"
                        onChange={handleBinFileSelect}
                        className="file-input recording-file-input"
                    />
                    {recording.binFile && (
                        <div className="file-info">{recording.binFile.name}</div>
                    )}
                </div>

                {/* Sampling Rate */}
                <div className="form-group recording-form-group">
                    <label>Sampling Rate:</label>
                    <input
                        type="number"
                        value={recording.samplingRate}
                        onChange={(e) => handleParameterChange('samplingRate', e.target.value)}
                        className="form-input recording-form-input"
                    />
                </div>

                {/* Number of Channels */}
                <div className="form-group recording-form-group">
                    <label>Number of Channels:</label>
                    <input
                        type="number"
                        value={recording.numChannels}
                        onChange={(e) => handleParameterChange('numChannels', e.target.value)}
                        className="form-input recording-form-input"
                    />
                </div>

                {/* Gain to µV */}
                <div className="form-group recording-form-group">
                    <label>Gain to µV:</label>
                    <input
                        type="number"
                        step="0.001"
                        value={recording.gainToMicroVolts}
                        onChange={(e) => handleParameterChange('gainToMicroVolts', e.target.value)}
                        className="form-input recording-form-input"
                    />
                </div>

                {/* Offset to µV */}
                <div className="form-group recording-form-group">
                    <label>Offset to µV:</label>
                    <input
                        type="number"
                        step="0.001"
                        value={recording.offsetToMicroVolts}
                        onChange={(e) => handleParameterChange('offsetToMicroVolts', e.target.value)}
                        className="form-input recording-form-input"
                    />
                </div>

                {/* Probe */}
                <div className="form-group recording-form-group">
                    <label>Probe:</label>
                    <input
                        ref={probeInputRef}
                        type="file"
                        accept="application/json,.json"
                        onChange={handleProbeFileSelect}
                        className="file-input recording-file-input"
                    />
                    {recording.probeFile && (
                        <div className="file-info">{recording.probeFile.name}</div>
                    )}
                </div>

                {/* Remove Channels */}
                <div className="channels-section">
                    <label className="channels-label">Remove Channels</label>
                    <div className="channels-grid">
                        {Array.from({ length: Math.max(0, recording.numChannels) }).map((_, idx) => (
                            <label key={`remove-${idx}`} className="checkbox-label">
                                <input
                                    type="checkbox"
                                    checked={removeChannels.includes(idx)}
                                    onChange={() => handleRemoveChannelToggle(idx)}
                                    className="checkbox-input"
                                />
                                <span className="checkbox-text">{idx}</span>
                            </label>
                        ))}
                    </div>
                    {removeChannels.length > 0 && (
                        <div className="selected-text">
                            Selected: {removeChannels.join(', ')}
                        </div>
                    )}
                </div>

                {/* Bad Channels */}
                <div className="channels-section">
                    <label className="channels-label">Bad Channels</label>
                    <div className="channels-grid">
                        {Array.from({ length: Math.max(0, recording.numChannels) }).map((_, idx) => (
                            <label key={`bad-${idx}`} className="checkbox-label">
                                <input
                                    type="checkbox"
                                    checked={recording.badChannels.includes(idx)}
                                    onChange={() => handleBadChannelToggle(idx)}
                                    className="checkbox-input"
                                />
                                <span className="checkbox-text">{idx}</span>
                            </label>
                        ))}
                    </div>
                    {recording.badChannels.length > 0 && (
                        <div className="selected-text">
                            Selected: {recording.badChannels.join(', ')}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
