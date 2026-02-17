import React, { useState, useEffect } from 'react';
import '../styles/ManageJobs.css';

export default function ManageJobs({ onBack }) {
    const [jobs, setJobs] = useState([]);
    const [statistics, setStatistics] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState('');
    const [selectedJob, setSelectedJob] = useState(null);
    const [statusFilter, setStatusFilter] = useState('');

    useEffect(() => {
        fetchJobs();
        fetchStatistics();
    }, [statusFilter]);

    const fetchJobs = async () => {
        setIsLoading(true);
        setError('');
        try {
            const url = statusFilter
                ? `/submit-jobs/list/?status=${statusFilter}`
                : `/submit-jobs/list/`;

            const response = await fetch(url, {
                headers: {
                    'Authorization': `Token ${localStorage.getItem('token')}`,
                },
            });

            if (!response.ok) {
                throw new Error('Failed to fetch jobs');
            }

            const data = await response.json();
            setJobs(data.jobs || []);
        } catch (err) {
            setError(err.message || 'Failed to load jobs');
            console.error('Error fetching jobs:', err);
        } finally {
            setIsLoading(false);
        }
    };

    const fetchStatistics = async () => {
        try {
            const response = await fetch('/submit-jobs/statistics/', {
                headers: {
                    'Authorization': `Token ${localStorage.getItem('token')}`,
                },
            });

            if (!response.ok) {
                throw new Error('Failed to fetch statistics');
            }

            const data = await response.json();
            setStatistics(data);
        } catch (err) {
            console.error('Error fetching statistics:', err);
        }
    };

    const getStatusColor = (status) => {
        switch (status) {
            case 'finished':
                return '#28a745';
            case 'running':
                return '#ffc107';
            case 'pending':
                return '#6c757d';
            case 'fetched':
                return '#0dcaf0';
            case 'failed':
                return '#dc3545';
            default:
                return '#6c757d';
        }
    };

    const getStatusIcon = (status) => {
        switch (status) {
            case 'finished':
                return '✓';
            case 'running':
                return '⟳';
            case 'pending':
                return '⋯';
            case 'fetched':
                return '↓';
            case 'failed':
                return '✗';
            default:
                return '?';
        }
    };

    const getProgressPercentage = (job) => {
        if (!job.step_count || job.step_count === 0) return 0;
        return Math.round((job.completed_steps / job.step_count) * 100);
    };

    const formatDate = (dateString) => {
        const date = new Date(dateString);
        return date.toLocaleString();
    };

    const formatRecordingConfig = (step) => {
        if (!step.config_block) return '';
        const cfg = step.config_block;
        if (cfg.binfile) {
            return `${cfg.binfile.split('/').pop()} (${cfg.sampling_rate}Hz)`;
        }
        return JSON.stringify(cfg).substring(0, 50) + '...';
    };

    const updateJobStatus = async (jobId, newStatus) => {
        try {
            const response = await fetch('/job-queue/getthenextjob/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Token ${localStorage.getItem('token')}`,
                },
                body: JSON.stringify({
                    job_id: jobId,
                    status: newStatus,
                }),
            });

            if (!response.ok) {
                throw new Error('Failed to update job status');
            }

            // Refresh the selected job to show updated status
            const updatedJob = { ...selectedJob, status: newStatus };
            setSelectedJob(updatedJob);

            // Refresh jobs list
            fetchJobs();
            fetchStatistics();
        } catch (err) {
            console.error('Error updating job status:', err);
            alert('Failed to update job status: ' + err.message);
        }
    };

    const updateStepStatus = async (jobId, stepId, newStatus) => {
        try {
            const response = await fetch('/job-queue/getthenextjob/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Token ${localStorage.getItem('token')}`,
                },
                body: JSON.stringify({
                    job_id: jobId,
                    step_id: stepId,
                    status: newStatus,
                }),
            });

            if (!response.ok) {
                throw new Error('Failed to update step status');
            }

            // Update the step in selectedJob
            const updatedJob = {
                ...selectedJob,
                job_steps: selectedJob.job_steps.map(s =>
                    s.identifier === stepId ? { ...s, status: newStatus } : s
                ),
            };
            setSelectedJob(updatedJob);

            // Refresh jobs list
            fetchJobs();
            fetchStatistics();
        } catch (err) {
            console.error('Error updating step status:', err);
            alert('Failed to update step status: ' + err.message);
        }
    };

    if (isLoading) {
        return (
            <div className="manage-jobs-container">
                <div className="jobs-header">
                    <button className="back-btn" onClick={onBack}>← Back</button>
                    <h1>Manage Jobs</h1>
                </div>
                <div className="loading">Loading jobs...</div>
            </div>
        );
    }

    if (selectedJob) {
        return (
            <div className="manage-jobs-container">
                <div className="jobs-header">
                    <button className="back-btn" onClick={() => setSelectedJob(null)}>← Back</button>
                    <h1>Job Details: {selectedJob.job_id}</h1>
                </div>

                <div className="job-details">
                    <div className="detail-section">
                        <h3>Job Information</h3>
                        <div className="detail-row">
                            <span className="label">Job ID:</span>
                            <span className="value">{selectedJob.job_id}</span>
                        </div>
                        <div className="detail-row">
                            <span className="label">Status:</span>
                            <span className="value status" style={{ color: getStatusColor(selectedJob.status) }}>
                                {getStatusIcon(selectedJob.status)} {selectedJob.status.toUpperCase()}
                            </span>
                        </div>
                        <div className="detail-row">
                            <span className="label">Created:</span>
                            <span className="value">{formatDate(selectedJob.created_at)}</span>
                        </div>
                        <div className="detail-row">
                            <span className="label">Progress:</span>
                            <span className="value">{selectedJob.completed_steps}/{selectedJob.step_count} steps completed</span>
                        </div>

                        {/* Status Update Buttons */}
                        <div className="status-update-section">
                            <h4>Update Job Status:</h4>
                            <div className="status-buttons">
                                <button
                                    className="status-btn pending"
                                    onClick={() => updateJobStatus(selectedJob.job_id, 'pending')}
                                    disabled={selectedJob.status === 'pending'}
                                >
                                    ⋯ Pending
                                </button>
                                <button
                                    className="status-btn fetched"
                                    onClick={() => updateJobStatus(selectedJob.job_id, 'fetched')}
                                    disabled={selectedJob.status === 'fetched'}
                                >
                                    ↓ Fetched
                                </button>
                                <button
                                    className="status-btn running"
                                    onClick={() => updateJobStatus(selectedJob.job_id, 'running')}
                                    disabled={selectedJob.status === 'running'}
                                >
                                    ⟳ Running
                                </button>
                                <button
                                    className="status-btn finished"
                                    onClick={() => updateJobStatus(selectedJob.job_id, 'finished')}
                                    disabled={selectedJob.status === 'finished'}
                                >
                                    ✓ Finished
                                </button>
                                <button
                                    className="status-btn failed"
                                    onClick={() => updateJobStatus(selectedJob.job_id, 'failed')}
                                    disabled={selectedJob.status === 'failed'}
                                >
                                    ✗ Failed
                                </button>
                            </div>
                        </div>
                    </div>

                    <div className="detail-section">
                        <h3>Environment</h3>
                        <div className="detail-row">
                            <span className="label">Environment:</span>
                            <span className="value">{selectedJob.job_env.environment}</span>
                        </div>
                        <div className="detail-row">
                            <span className="label">Base Directory:</span>
                            <span className="value">{selectedJob.job_env.base_directory}</span>
                        </div>
                        <div className="detail-row">
                            <span className="label">Log Level:</span>
                            <span className="value">{selectedJob.job_env.log_level}</span>
                        </div>
                    </div>

                    <div className="detail-section">
                        <h3>Job Steps</h3>
                        <div className="steps-list">
                            {selectedJob.job_steps.map((step, idx) => (
                                <div key={idx} className="step-item">
                                    <div className="step-number">{idx + 1}</div>
                                    <div className="step-info">
                                        <div className="step-name">{step.function}</div>
                                        <div className="step-config">{formatRecordingConfig(step)}</div>
                                        <div className="step-status" style={{ color: getStatusColor(step.status) }}>
                                            {getStatusIcon(step.status)} {step.status}
                                        </div>
                                        {step.depends_on && step.depends_on.length > 0 && (
                                            <div className="step-deps">
                                                Depends on: {step.depends_on.join(', ')}
                                            </div>
                                        )}
                                    </div>
                                    {/* Step Status Update Buttons */}
                                    <div className="step-status-buttons">
                                        <button
                                            className="small-status-btn pending"
                                            onClick={() => updateStepStatus(selectedJob.job_id, step.identifier, 'pending')}
                                            disabled={step.status === 'pending'}
                                            title="Mark as pending"
                                        >
                                            ⋯
                                        </button>
                                        <button
                                            className="small-status-btn running"
                                            onClick={() => updateStepStatus(selectedJob.job_id, step.identifier, 'running')}
                                            disabled={step.status === 'running'}
                                            title="Mark as running"
                                        >
                                            ⟳
                                        </button>
                                        <button
                                            className="small-status-btn completed"
                                            onClick={() => updateStepStatus(selectedJob.job_id, step.identifier, 'completed')}
                                            disabled={step.status === 'completed'}
                                            title="Mark as completed"
                                        >
                                            ✓
                                        </button>
                                        <button
                                            className="small-status-btn failed"
                                            onClick={() => updateStepStatus(selectedJob.job_id, step.identifier, 'failed')}
                                            disabled={step.status === 'failed'}
                                            title="Mark as failed"
                                        >
                                            ✗
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="manage-jobs-container">
            <div className="jobs-header">
                <button className="back-btn" onClick={onBack}>← Back</button>
                <h1>Manage Jobs</h1>
                <button className="refresh-btn" onClick={() => { fetchJobs(); fetchStatistics(); }}>🔄 Refresh</button>
            </div>

            {/* Statistics */}
            {statistics && (
                <div className="statistics-bar">
                    <div className="stat-item">
                        <div className="stat-value">{statistics.total_jobs}</div>
                        <div className="stat-label">Total Jobs</div>
                    </div>
                    <div className="stat-item">
                        <div className="stat-value" style={{ color: '#28a745' }}>{statistics.status_breakdown.finished}</div>
                        <div className="stat-label">Finished</div>
                    </div>
                    <div className="stat-item">
                        <div className="stat-value" style={{ color: '#ffc107' }}>{statistics.status_breakdown.running}</div>
                        <div className="stat-label">Running</div>
                    </div>
                    <div className="stat-item">
                        <div className="stat-value" style={{ color: '#6c757d' }}>{statistics.status_breakdown.pending}</div>
                        <div className="stat-label">Pending</div>
                    </div>
                    <div className="stat-item">
                        <div className="stat-value" style={{ color: '#dc3545' }}>{statistics.status_breakdown.failed}</div>
                        <div className="stat-label">Failed</div>
                    </div>
                </div>
            )}

            {/* Status Filter */}
            <div className="filter-bar">
                <button
                    className={`filter-btn ${statusFilter === '' ? 'active' : ''}`}
                    onClick={() => setStatusFilter('')}
                >
                    All Jobs
                </button>
                <button
                    className={`filter-btn ${statusFilter === 'pending' ? 'active' : ''}`}
                    onClick={() => setStatusFilter('pending')}
                >
                    Pending
                </button>
                <button
                    className={`filter-btn ${statusFilter === 'running' ? 'active' : ''}`}
                    onClick={() => setStatusFilter('running')}
                >
                    Running
                </button>
                <button
                    className={`filter-btn ${statusFilter === 'finished' ? 'active' : ''}`}
                    onClick={() => setStatusFilter('finished')}
                >
                    Finished
                </button>
                <button
                    className={`filter-btn ${statusFilter === 'failed' ? 'active' : ''}`}
                    onClick={() => setStatusFilter('failed')}
                >
                    Failed
                </button>
            </div>

            {error && <div className="error-message">⚠️ {error}</div>}

            {jobs.length === 0 ? (
                <div className="empty-state">
                    <p>No jobs found. Create a sorting job to get started!</p>
                </div>
            ) : (
                <div className="jobs-grid">
                    {jobs.map(job => (
                        <div
                            key={job.job_id}
                            className="job-card"
                            onClick={() => setSelectedJob(job)}
                        >
                            <div className="job-header">
                                <h3>{job.job_id.substring(0, 8)}...</h3>
                                <div
                                    className="status-badge"
                                    style={{ backgroundColor: getStatusColor(job.status) }}
                                >
                                    {getStatusIcon(job.status)} {job.status}
                                </div>
                            </div>

                            <div className="job-info">
                                <div className="info-item">
                                    <span className="label">Created:</span>
                                    <span className="value">{formatDate(job.created_at)}</span>
                                </div>
                                <div className="info-item">
                                    <span className="label">Environment:</span>
                                    <span className="value">{job.job_env.environment}</span>
                                </div>
                            </div>

                            <div className="job-progress">
                                <div className="progress-label">
                                    Steps: {job.completed_steps}/{job.step_count}
                                </div>
                                <div className="progress-bar">
                                    <div
                                        className="progress-fill"
                                        style={{ width: `${getProgressPercentage(job)}%` }}
                                    />
                                </div>
                                <div className="progress-text">{getProgressPercentage(job)}%</div>
                            </div>

                            <button className="view-details-btn">View Details →</button>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
