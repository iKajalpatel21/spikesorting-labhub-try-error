import React, { useState, useEffect } from 'react';
import '../styles/ManageJobs.css';

export default function ManageJobs({ onBack }) {
    const [jobs, setJobs] = useState([]);
    const [statistics, setStatistics] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState('');
    const [selectedJob, setSelectedJob] = useState(null);
    const [statusFilter, setStatusFilter] = useState('');

    // Push a history entry when opening job details so browser back works
    const openJobDetail = (job) => {
        window.history.pushState({ jobDetail: true }, '');
        setSelectedJob(job);
    };

    const closeJobDetail = () => {
        setSelectedJob(null);
    };

    useEffect(() => {
        const handlePopState = () => {
            if (selectedJob) setSelectedJob(null);
        };
        window.addEventListener('popstate', handlePopState);
        return () => window.removeEventListener('popstate', handlePopState);
    }, [selectedJob]);

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
                headers: { 'Authorization': `Token ${localStorage.getItem('token')}` },
            });

            if (!response.ok) throw new Error('Failed to fetch jobs');

            const data = await response.json();
            setJobs(data.jobs || []);
        } catch (err) {
            setError(err.message || 'Failed to load jobs');
        } finally {
            setIsLoading(false);
        }
    };

    const fetchStatistics = async () => {
        try {
            const response = await fetch('/submit-jobs/statistics/', {
                headers: { 'Authorization': `Token ${localStorage.getItem('token')}` },
            });
            if (!response.ok) return;
            const data = await response.json();
            setStatistics(data);
        } catch (err) {
            console.error('Error fetching statistics:', err);
        }
    };

    const STATUS_COLORS = {
        finished:  '#28a745',
        completed: '#28a745',
        running:   '#2b7de9',
        pending:   '#e0a800',
        fetched:   '#0dcaf0',
        failed:    '#dc3545',
        canceled:  '#6c757d',
    };

    const STATUS_ICONS = {
        finished:  '✓',
        completed: '✓',
        running:   '⟳',
        pending:   '⋯',
        fetched:   '↓',
        failed:    '✗',
        canceled:  '⊘',
    };

    const getStatusColor = (status) => STATUS_COLORS[status] || '#6c757d';
    const getStatusIcon  = (status) => STATUS_ICONS[status]  || '?';

    const getProgressPercentage = (job) => {
        if (!job.step_count || job.step_count === 0) return 0;
        return Math.round((job.completed_steps / job.step_count) * 100);
    };

    const formatDate = (dateString) => new Date(dateString).toLocaleString();

    const formatRecordingConfig = (step) => {
        if (!step.config_block) return '';
        const cfg = step.config_block;
        if (cfg.binfile) return `${cfg.binfile.split('/').pop()} (${cfg.sampling_rate}Hz)`;
        return JSON.stringify(cfg).substring(0, 50) + '...';
    };

    const authHeaders = () => ({
        'Content-Type': 'application/json',
        'Authorization': `Token ${localStorage.getItem('token')}`,
    });

    const cancelJob = async (e, jobId) => {
        e.stopPropagation();
        if (!window.confirm('Cancel this job?')) return;
        try {
            const res = await fetch('/job-queue/cancel-job/', {
                method: 'POST',
                headers: authHeaders(),
                body: JSON.stringify({ job_id: jobId }),
            });
            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.error || 'Failed to cancel job');
            }
            if (selectedJob?.job_id === jobId) setSelectedJob({ ...selectedJob, status: 'canceled' });
            fetchJobs();
            fetchStatistics();
        } catch (err) {
            alert(err.message);
        }
    };

    const resumeJob = async (e, jobId) => {
        e.stopPropagation();
        if (!window.confirm('Resume this job?')) return;
        try {
            const res = await fetch('/job-queue/resume-job/', {
                method: 'POST',
                headers: authHeaders(),
                body: JSON.stringify({ job_id: jobId }),
            });
            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.error || 'Failed to resume job');
            }
            if (selectedJob?.job_id === jobId) setSelectedJob({ ...selectedJob, status: 'pending' });
            fetchJobs();
            fetchStatistics();
        } catch (err) {
            alert(err.message);
        }
    };

    const updateJobStatus = async (jobId, newStatus) => {
        try {
            const res = await fetch('/job-queue/update-status/', {
                method: 'POST',
                headers: authHeaders(),
                body: JSON.stringify({ job_id: jobId, status: newStatus }),
            });
            if (!res.ok) throw new Error('Failed to update job status');
            setSelectedJob({ ...selectedJob, status: newStatus });
            fetchJobs();
            fetchStatistics();
        } catch (err) {
            alert('Failed to update job status: ' + err.message);
        }
    };

    const updateStepStatus = async (jobId, stepId, newStatus) => {
        try {
            const res = await fetch('/job-queue/update-status/', {
                method: 'POST',
                headers: authHeaders(),
                body: JSON.stringify({ job_id: jobId, step_id: stepId, status: newStatus }),
            });
            if (!res.ok) throw new Error('Failed to update step status');
            setSelectedJob({
                ...selectedJob,
                job_steps: selectedJob.job_steps.map(s =>
                    s.identifier === stepId ? { ...s, status: newStatus } : s
                ),
            });
            fetchJobs();
            fetchStatistics();
        } catch (err) {
            alert('Failed to update step status: ' + err.message);
        }
    };

    // ── Loading state ──────────────────────────────────────────────────────────
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

    // ── Detail view ────────────────────────────────────────────────────────────
    if (selectedJob) {
        const isPending  = selectedJob.status === 'pending';
        const isCanceled = selectedJob.status === 'canceled';

        return (
            <div className="manage-jobs-container">
                <div className="jobs-header">
                    <button className="back-btn" onClick={closeJobDetail}>← Back</button>
                    <h1>Job Details</h1>
                </div>

                <div className="job-details">
                    <div className="detail-section">
                        <h3>Job Information</h3>
                        <div className="detail-row">
                            <span className="label">Job ID:</span>
                            <span className="value mono">{selectedJob.job_id}</span>
                        </div>
                        <div className="detail-row">
                            <span className="label">Status:</span>
                            <span className="status-inline" style={{ color: getStatusColor(selectedJob.status) }}>
                                <span className="status-dot" style={{ backgroundColor: getStatusColor(selectedJob.status) }} />
                                {selectedJob.status.toUpperCase()}
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

                        {/* Cancel / Resume */}
                        <div className="action-buttons-row">
                            <button
                                className="action-btn cancel-btn"
                                onClick={(e) => cancelJob(e, selectedJob.job_id)}
                                disabled={!isPending}
                                title={isPending ? 'Cancel this job' : 'Can only cancel pending jobs'}
                            >
                                ✕ Cancel Job
                            </button>
                            <button
                                className="action-btn resume-btn"
                                onClick={(e) => resumeJob(e, selectedJob.job_id)}
                                disabled={!isCanceled}
                                title={isCanceled ? 'Resume this job' : 'Can only resume canceled jobs'}
                            >
                                ↺ Resume Job
                            </button>
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
                                            <div className="step-deps">Depends on: {step.depends_on.join(', ')}</div>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    // ── List view ──────────────────────────────────────────────────────────────
    const FILTER_TABS = [
        { label: 'All Jobs',  value: '' },
        { label: 'Pending',   value: 'pending' },
        { label: 'Running',   value: 'running' },
        { label: 'Completed', value: 'completed' },
        { label: 'Failed',    value: 'failed' },
        { label: 'Canceled',  value: 'canceled' },
    ];

    return (
        <div className="manage-jobs-container">
            <div className="jobs-header">
                <button className="back-btn" onClick={onBack}>← Back</button>
                <h1>Manage Jobs</h1>
                <button className="refresh-btn" onClick={() => { fetchJobs(); fetchStatistics(); }}>Refresh</button>
            </div>

            {/* Statistics */}
            {statistics && (
                <div className="statistics-bar">
                    <div className="stat-item">
                        <div className="stat-value">{statistics.total_jobs}</div>
                        <div className="stat-label">Total</div>
                    </div>
                    <div className="stat-item">
                        <div className="stat-value" style={{ color: STATUS_COLORS.completed }}>{statistics.status_breakdown.completed}</div>
                        <div className="stat-label">Completed</div>
                    </div>
                    <div className="stat-item">
                        <div className="stat-value" style={{ color: STATUS_COLORS.running }}>{statistics.status_breakdown.running}</div>
                        <div className="stat-label">Running</div>
                    </div>
                    <div className="stat-item">
                        <div className="stat-value" style={{ color: STATUS_COLORS.pending }}>{statistics.status_breakdown.pending}</div>
                        <div className="stat-label">Pending</div>
                    </div>
                    <div className="stat-item">
                        <div className="stat-value" style={{ color: STATUS_COLORS.failed }}>{statistics.status_breakdown.failed}</div>
                        <div className="stat-label">Failed</div>
                    </div>
                    <div className="stat-item">
                        <div className="stat-value" style={{ color: STATUS_COLORS.canceled }}>{statistics.status_breakdown.canceled}</div>
                        <div className="stat-label">Canceled</div>
                    </div>
                </div>
            )}

            {/* Filter tabs */}
            <div className="filter-bar">
                {FILTER_TABS.map(tab => (
                    <button
                        key={tab.value}
                        className={`filter-btn ${statusFilter === tab.value ? 'active' : ''}`}
                        onClick={() => setStatusFilter(tab.value)}
                    >
                        {tab.label}
                    </button>
                ))}
            </div>

            {error && <div className="error-message">{error}</div>}

            {jobs.length === 0 ? (
                <div className="empty-state">
                    <p>No jobs found. Create a sorting job to get started!</p>
                </div>
            ) : (
                <div className="jobs-grid">
                    {jobs.map(job => {
                        const isPending  = job.status === 'pending';
                        const isCanceled = job.status === 'canceled';
                        return (
                            <div key={job.job_id} className="job-card" onClick={() => openJobDetail(job)}>
                                <div className="job-header">
                                    <span className="job-id-text">{job.job_id.substring(0, 8)}…</span>
                                    <span
                                        className="status-badge"
                                        style={{ backgroundColor: getStatusColor(job.status) }}
                                    >
                                        <span className="badge-dot" />
                                        {job.status}
                                    </span>
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
                                    <div className="progress-label">Steps: {job.completed_steps}/{job.step_count}</div>
                                    <div className="progress-bar">
                                        <div
                                            className="progress-fill"
                                            style={{
                                                width: `${getProgressPercentage(job)}%`,
                                                backgroundColor: getStatusColor(job.status),
                                            }}
                                        />
                                    </div>
                                    <div className="progress-text">{getProgressPercentage(job)}%</div>
                                </div>

                                <div className="card-actions" onClick={e => e.stopPropagation()}>
                                    <button
                                        className="card-action-btn cancel-btn"
                                        onClick={(e) => cancelJob(e, job.job_id)}
                                        disabled={!isPending}
                                        title={isPending ? 'Cancel job' : 'Can only cancel pending jobs'}
                                    >
                                        ✕ Cancel
                                    </button>
                                    <button
                                        className="card-action-btn resume-btn"
                                        onClick={(e) => resumeJob(e, job.job_id)}
                                        disabled={!isCanceled}
                                        title={isCanceled ? 'Resume job' : 'Can only resume canceled jobs'}
                                    >
                                        ↺ Resume
                                    </button>
                                    <button className="view-details-btn" onClick={() => openJobDetail(job)}>
                                        Details →
                                    </button>
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}
