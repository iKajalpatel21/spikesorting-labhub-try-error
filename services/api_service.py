"""
API Service for handling HTTP communication with the job management API.
This service abstracts all API calls and provides a clean interface for the worker.
"""

import json
import logging
import requests
import urllib3
from typing import Dict, Optional, Any

from config.constants import Environment, WorkerConfig, JobSpecification, ErrorMessages


class APIService:
    """Service for handling API communication"""
    
    def __init__(self, environment: str = Environment.PRODUCTION):
        """
        Initialize API service with specified environment
        
        Args:
            environment: Environment to use (local, production, localhost_https)
        """
        self.environment = environment
        self.api_url = Environment.get_api_url(environment)
        self.token = Environment.get_token(environment)
        self.headers = {"Authorization": f"Token {self.token}"}
        
        # Configure SSL warnings
        if not WorkerConfig.SSL_VERIFY:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        self.logger = logging.getLogger(__name__)
        
    def get_next_job(self) -> Optional[Dict[str, Any]]:
        """
        Fetch the next available job from the API
        
        Returns:
            Job data dictionary if available, None if no jobs pending
            
        Raises:
            requests.exceptions.RequestException: If API call fails
        """
        try:
            response = requests.get(
                self.api_url, 
                headers=self.headers, 
                verify=WorkerConfig.SSL_VERIFY
            )
            
            if response.status_code == 200:
                job_data = response.json()
                
                # Check if we got actual job data or empty response
                if job_data and "job_id" in job_data:
                    self.logger.info(f"Received job: {job_data['job_id']}")
                    return job_data
                else:
                    self.logger.info("No pending jobs found")
                    return None
            else:
                self.logger.error(f"API returned status code: {response.status_code}")
                response.raise_for_status()
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching job from API: {e}")
            raise
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to decode JSON from API response: {e}")
            raise
            
    def update_job_status(self, job_id: str, status: str) -> bool:
        """
        Update the status of a job
        
        Args:
            job_id: The ID of the job to update
            status: The new status to set
            
        Returns:
            True if update was successful, False otherwise
        """
        return self._update_status(job_id, status)
    
    def update_step_status(self, job_id: str, step_id: str, status: str) -> bool:
        """
        Update the status of a specific job step
        
        Args:
            job_id: The ID of the job
            step_id: The ID of the step to update
            status: The new status to set
            
        Returns:
            True if update was successful, False otherwise
        """
        return self._update_status(job_id, status, step_id)
    
    def _update_status(self, job_id: str, status: str, step_id: Optional[str] = None) -> bool:
        """
        Internal method to update job or step status
        
        Args:
            job_id: The ID of the job
            status: The new status to set
            step_id: The ID of the step (optional)
            
        Returns:
            True if update was successful, False otherwise
        """
        payload = {"job_id": str(job_id), "status": status}
        
        if step_id is not None:
            payload["step_id"] = str(step_id)
        
        try:
            # Determine SSL verification method
            verify_param = WorkerConfig.SSL_CERT_PATH if WorkerConfig.SSL_CERT_PATH != "cert.pem" else WorkerConfig.SSL_VERIFY
            
            response = requests.post(
                self.api_url,
                json=payload,
                headers=self.headers,
                verify=verify_param
            )
            response.raise_for_status()
            
            # Log success message
            if step_id is not None:
                self.logger.info(f"Updated job {job_id}, step {step_id} to '{status}'")
            else:
                self.logger.info(f"Updated job {job_id} to '{status}'")
                
            return True
            
        except requests.exceptions.RequestException as e:
            # Log error message
            if step_id is not None:
                self.logger.error(f"Failed to update job {job_id}, step {step_id} to '{status}': {e}")
            else:
                self.logger.error(f"Failed to update job {job_id} to '{status}': {e}")
            return False
    
    def get_api_info(self) -> Dict[str, str]:
        """Get current API configuration info"""
        return {
            "environment": self.environment,
            "api_url": self.api_url,
            "has_token": bool(self.token),
            "ssl_verify": str(WorkerConfig.SSL_VERIFY)
        }
