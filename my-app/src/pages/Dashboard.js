import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import CreateSortingJobWizard from './CreateSortingJobWizard';
import AddNewPipeline from './AddNewPipeline';
import ManageJobs from './ManageJobs';
import '../styles/Dashboard.css';

export default function Dashboard() {
  const [activeSection, setActiveSection] = useState('home');
  const navigate = useNavigate();

  if (activeSection === 'createJob') {
    return <CreateSortingJobWizard onBack={() => setActiveSection('home')} />;
  }

  if (activeSection === 'addPipeline') {
    return <AddNewPipeline onBack={() => setActiveSection('home')} />;
  }

  if (activeSection === 'manageJobs') {
    return <ManageJobs onBack={() => setActiveSection('home')} />;
  }

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <h1>Spike Sorting Pipeline Manager</h1>
        <p>Manage your spike sorting workflows</p>
      </div>

      <div className="dashboard-actions">
        <div 
          className="action-card create-job"
          onClick={() => setActiveSection('createJob')}
        >
          <div className="card-icon">⚙️</div>
          <h3>Create Sorting Job</h3>
          <p>Start a new spike sorting workflow with your recording data</p>
          <button className="action-button">Start Wizard →</button>
        </div>

        <div 
          className="action-card add-pipeline"
          onClick={() => setActiveSection('addPipeline')}
        >
          <div className="card-icon">🔧</div>
          <h3>Add New Pipeline</h3>
          <p>Create a reusable pipeline template with processing steps</p>
          <button className="action-button">Create Pipeline →</button>
        </div>

        <div 
          className="action-card manage-jobs"
          onClick={() => setActiveSection('manageJobs')}
        >
          <div className="card-icon">📊</div>
          <h3>Manage Jobs</h3>
          <p>Monitor and inspect your job history and status</p>
          <button className="action-button">View Jobs →</button>
        </div>
      </div>
    </div>
  );
}
