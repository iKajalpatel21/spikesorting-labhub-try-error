import React, { useState } from 'react';
import '../styles/AddNewPipeline.css';

export default function AddNewPipeline({ onBack }) {
    const [formData, setFormData] = useState({
        description: '',
        steps: [{ id: 'step-1', name: '', function_name: '', config: '{}', dependencies: '' }],
    });
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    const handleDescriptionChange = (e) => {
        setFormData({ ...formData, description: e.target.value });
    };

    const handleStepChange = (index, field, value) => {
        const newSteps = [...formData.steps];
        newSteps[index] = { ...newSteps[index], [field]: value };
        setFormData({ ...formData, steps: newSteps });
    };

    const addStep = () => {
        const newStepId = `step-${Math.max(...formData.steps.map(s => parseInt(s.id.split('-')[1]) || 0)) + 1}`;
        const newStep = {
            id: newStepId,
            name: '',
            function_name: '',
            config: '{}',
            dependencies: '',
        };
        setFormData({ ...formData, steps: [...formData.steps, newStep] });
    };

    const removeStep = (index) => {
        if (formData.steps.length > 1) {
            setFormData({
                ...formData,
                steps: formData.steps.filter((_, i) => i !== index),
            });
        }
    };

    const validateForm = () => {
        if (!formData.description.trim()) {
            setError('Pipeline description is required');
            return false;
        }

        if (formData.steps.length === 0) {
            setError('At least one step is required');
            return false;
        }

        for (let step of formData.steps) {
            if (!step.name.trim()) {
                setError('All steps must have a name');
                return false;
            }
            if (!step.function_name.trim()) {
                setError('All steps must have a function name');
                return false;
            }
            try {
                JSON.parse(step.config);
            } catch (e) {
                setError(`Invalid JSON in step "${step.name}" config`);
                return false;
            }
        }

        return true;
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setSuccess('');

        if (!validateForm()) {
            return;
        }

        setIsSubmitting(true);

        try {
            // TODO: Replace with actual API endpoint
            const response = await fetch('/api/pipelines/create/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Token ${localStorage.getItem('token')}`,
                },
                body: JSON.stringify({
                    description: formData.description,
                    steps: formData.steps.map(step => ({
                        identifier: step.id,
                        name: step.name,
                        function_name: step.function_name,
                        config: JSON.parse(step.config),
                        dependencies: step.dependencies
                            ? step.dependencies.split(',').map(d => d.trim())
                            : [],
                    })),
                }),
            });

            if (!response.ok) {
                throw new Error('Failed to create pipeline');
            }

            const data = await response.json();
            setSuccess(`Pipeline created successfully! Pipeline ID: ${data.id}`);

            // Reset form after success
            setTimeout(() => {
                setFormData({
                    description: '',
                    steps: [{ id: 'step-1', name: '', function_name: '', config: '{}', dependencies: '' }],
                });
            }, 1500);
        } catch (err) {
            setError(err.message || 'Failed to create pipeline');
            console.error('Error:', err);
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="pipeline-form-container">
            <div className="pipeline-form-header">
                <button className="back-btn" onClick={onBack}>Back</button>
                <h1>Create New Pipeline</h1>
            </div>

            <form onSubmit={handleSubmit} className="pipeline-form">
                {/* Description */}
                <div className="form-section">
                    <h3>📝 Pipeline Description</h3>
                    <div className="form-group">
                        <label>Description</label>
                        <textarea
                            value={formData.description}
                            onChange={handleDescriptionChange}
                            placeholder="Describe what this pipeline does..."
                            rows="3"
                            className="form-textarea"
                        />
                    </div>
                </div>

                {/* Steps */}
                <div className="form-section">
                    <h3>Pipeline Steps</h3>
                    <p className="section-description">Define the processing steps for this pipeline.</p>

                    <div className="steps-container">
                        {formData.steps.map((step, index) => (
                            <div key={step.id} className="step-card">
                                <div className="step-header">
                                    <h4>Step {index + 1}: {step.name || 'Unnamed'}</h4>
                                    {formData.steps.length > 1 && (
                                        <button
                                            type="button"
                                            className="remove-step-btn"
                                            onClick={() => removeStep(index)}
                                            title="Remove this step"
                                        >
                                            ✕
                                        </button>
                                    )}
                                </div>

                                <div className="step-grid">
                                    <div className="form-group">
                                        <label>Step Name *</label>
                                        <input
                                            type="text"
                                            value={step.name}
                                            onChange={(e) => handleStepChange(index, 'name', e.target.value)}
                                            placeholder="e.g., Preprocessing"
                                            className="form-input"
                                        />
                                    </div>

                                    <div className="form-group">
                                        <label>Function Name *</label>
                                        <input
                                            type="text"
                                            value={step.function_name}
                                            onChange={(e) => handleStepChange(index, 'function_name', e.target.value)}
                                            placeholder="e.g., preprocess_signal"
                                            className="form-input"
                                        />
                                    </div>
                                </div>

                                <div className="form-group">
                                    <label>Step Configuration (JSON)</label>
                                    <textarea
                                        value={step.config}
                                        onChange={(e) => handleStepChange(index, 'config', e.target.value)}
                                        placeholder='{"param1": "value1", "param2": 42}'
                                        rows="4"
                                        className="form-textarea config-textarea"
                                    />
                                    <small className="help-text">Enter valid JSON for the step parameters</small>
                                </div>

                                <div className="form-group">
                                    <label>Dependencies (comma-separated step IDs)</label>
                                    <input
                                        type="text"
                                        value={step.dependencies}
                                        onChange={(e) => handleStepChange(index, 'dependencies', e.target.value)}
                                        placeholder="e.g., step-1, step-2"
                                        className="form-input"
                                    />
                                    <small className="help-text">Leave empty if this step has no dependencies</small>
                                </div>
                            </div>
                        ))}
                    </div>

                    <button
                        type="button"
                        className="add-step-btn"
                        onClick={addStep}
                    >
                        + Add Another Step
                    </button>
                </div>

                {/* Messages */}
                {error && <div className="error-message">{error}</div>}
                {success && <div className="success-message">{success}</div>}

                {/* Submit Button */}
                <div className="form-actions">
                    <button
                        type="submit"
                        className="submit-btn"
                        disabled={isSubmitting}
                    >
                        {isSubmitting ? 'Creating Pipeline...' : 'Create Pipeline'}
                    </button>
                </div>
            </form>
        </div>
    );
}
