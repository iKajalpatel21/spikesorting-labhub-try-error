import React, { useState, useEffect } from 'react';
import '../styles/ManageJobs.css';

export default function ManageJobs({ onBack }) {
    const [jobs, setJobs] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState('');
    const [selectedJob, setSelectedJob] = useState(null);

    useEffect(() => {
        fetchJobs();
    }, []);

    const fetchJobs = async () => {
        setIsLoading(true);
        setError('');
        try {
            // TODO: Replace with actual API endpoint
            const response = await fetch('/api/jobs/', {
                headers: {
                    'Authorization': `Token ${localStorage.getItem('token')}`,
                },
            });

            if (!response.ok) {
                throw new Error('Failed to fetch jobs');
            }

            const data = await response.json();
            setJobs(data);
        } catch (err) {
            setError(err.message || 'Failed to load jobs');
            // Use mock data for demo
            setJobs(getMockJobs());
        } finally {
            setIsLoading(false);
        }
    };

    const getMockJobs = () => [
        {
            id: 1,
            created_at: '2024-01-07T10:30:00Z',
            status: 'completed',
            recording_name: 'recording_001.bin',
            pipeline_name: 'Standard Pipeline',
            steps: [
                { id: 1, name: 'Preprocessing', status: 'completed' },
                { id: 2, name: 'Detection', status: 'completed' },
                { id: 3, name: 'Sorting', status: 'completed' },
            ],
        },
        {
            id: 2,
            created_at: '2024-01-07T11:15:00Z',
            status: 'running',
            recording_name: 'recording_002.bin',
            pipeline_name: 'Advanced Pipeline',
            steps: [
                { id: 1, name: 'Preprocessing', status: 'completed' },
                { id: 2, name: 'Detection', status: 'running' },
                { id: 3, name: 'Sorting', status: 'pending' },
            ],
        },
        {
            id: 3,
            created_at: '2024-01-07T12:00:00Z',
            status: 'pending',
            recording_name: 'recording_003.bin',
            pipeline_name: 'Standard Pipeline',
            steps: [
                { id: 1, name: 'Preprocessing', status: 'pending' },
                { id: 2, name: 'Detection', status: 'pending' },
                { id: 3, name: 'Sorting', status: 'pending' },
            ],
        },
    ];

    const getStatusColor = (status) => {
        switch (status) {
            case 'completed':
                return '#28a745';
            case 'running':
                return '#ffc107';
            case 'pending':
                return '#6c757d';
            case 'failed':
                return '#dc3545';
            default:
                return '#6c757d';
        }
    };

    const getStatusIcon = (status) => {
        switch (status) {
            case 'completed':
                return 'Finished';
            case 'running':
                return 'Running';
            case 'pending':
                return '⏹️';
            case 'failed':
                return 'Failed';
            default:
                return '❓';
        }
    };

    const formatDate = (dateString) => {
        const date = new Date(dateString);
        return date.toLocaleString();
    };

    if (isLoading) {
        return (
            <div className="manage-jobs-container">
                <div className="jobs-header">
                    <button className="back-btn" onClick={onBack}>Back</button>
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
                    <button className="back-btn" onClick={() => setSelectedJob(null)}>Back</button>
                    <h1>Job Details: #{selectedJob.id}</h1>
                </div>

                <div className="job-details">
                    <div className="detail-section">
                        <h3>Job Information</h3>
                        <div className="detail-row">
                            <span className="label">Job ID:</span>
                            <span className="value">#{selectedJob.id}</span>
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
                    </div>

                    <div className="detail-section">
                        <h3>Recording</h3>
                        <div className="detail-row">
                            <span className="label">Recording:</span>
                            <span className="value">{selectedJob.recording_name}</span>
                        </div>
                    </div>

                    <div className="detail-section">
                        <h3>Pipeline</h3>
                        <div className="detail-row">
                            <span className="label">Pipeline:</span>
                            <span className="value">{selectedJob.pipeline_name}</span>
                        </div>
                    </div>

                    <div className="detail-section">
                        <h3>🔄 Step Status</h3>
                        <div className="steps-list">
                            {selectedJob.steps.map((step, idx) => (
                                <div key={step.id} className="step-item">
                                    <div className="step-number">{idx + 1}</div>
                                    <div className="step-info">
                                        <div className="step-name">{step.name}</div>
                                        <div className="step-status" style={{ color: getStatusColor(step.status) }}>
                                            {getStatusIcon(step.status)} {step.status}
                                        </div>
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
                <button className="refresh-btn" onClick={fetchJobs}>🔄 Refresh</button>
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
                            key={job.id}
                            className="job-card"
                            onClick={() => setSelectedJob(job)}
                        >
                            <div className="job-header">
                                <h3>Job #{job.id}</h3>
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
                                    <span className="label">Recording:</span>
                                    <span className="value">{job.recording_name}</span>
                                </div>
                                <div className="info-item">
                                    <span className="label">Pipeline:</span>
                                    <span className="value">{job.pipeline_name}</span>
                                </div>
                            </div>

                            <div className="job-progress">
                                <div className="progress-label">
                                    Step Progress: {job.steps.filter(s => s.status === 'completed').length}/{job.steps.length}
                                </div>
                                <div className="progress-bar">
                                    {job.steps.map((step, idx) => (
                                        <div
                                            key={step.id}
                                            className="progress-segment"
                                            style={{ backgroundColor: getStatusColor(step.status) }}
                                            title={`${step.name}: ${step.status}`}
                                        />
                                    ))}
                                </div>
                            </div>

                            <button className="view-details-btn">View Details</button>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
