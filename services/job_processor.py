"""
Job Processing Service for handling the execution of job steps.
This service contains the business logic for processing individual jobs and their steps.
"""

import logging
import random
import time
from typing import Dict, Any, List

from config.constants import JobSpecification
from services.api_service import APIService


class JobProcessor:
    """Service for processing jobs and their steps"""
    
    def __init__(self, api_service: APIService):
        """
        Initialize job processor with API service
        
        Args:
            api_service: Instance of APIService for API communication
        """
        self.api_service = api_service
        self.logger = logging.getLogger(__name__)
    
    def process_job(self, job_data: Dict[str, Any]) -> bool:
        """
        Process a complete job by executing all its steps
        
        Args:
            job_data: Job data dictionary from API
            
        Returns:
            True if job completed successfully, False if failed
        """
        job_id = job_data["job_id"]
        self.logger.info(f"Starting to process job: {job_id}")
        
        # Update job status to running
        self.api_service.update_job_status(job_id, JobSpecification.STATUS_RUNNING)
        
        try:
            job_steps = job_data.get("job_steps", [])
            num_completed_steps = 0
            
            for step in job_steps:
                if self._process_step(job_id, step):
                    num_completed_steps += 1
                else:
                    # If any step fails, mark job as failed
                    self.api_service.update_job_status(job_id, JobSpecification.STATUS_FAILED)
                    self.logger.error(f"Job {job_id} failed due to step failure")
                    return False
            
            # Check if all steps completed successfully
            if num_completed_steps == len(job_steps):
                self.api_service.update_job_status(job_id, JobSpecification.STATUS_FINISHED)
                self.logger.info(f"Job {job_id} finished successfully")
                return True
            else:
                self.api_service.update_job_status(job_id, JobSpecification.STATUS_FAILED)
                self.logger.error(f"Job {job_id} failed: {num_completed_steps}/{len(job_steps)} steps completed")
                return False
                
        except Exception as e:
            self.api_service.update_job_status(job_id, JobSpecification.STATUS_FAILED)
            self.logger.error(f"Job {job_id} failed with error: {e}")
            return False
    
    def _process_step(self, job_id: str, step: Dict[str, Any]) -> bool:
        """
        Process a single job step
        
        Args:
            job_id: ID of the parent job
            step: Step data dictionary
            
        Returns:
            True if step completed successfully, False if failed
        """
        step_id = step["identifier"]
        function_name = step["function"]
        
        self.logger.info(f"Processing step '{step_id}' (function: {function_name}) for job {job_id}")
        
        # Update step status to running
        if not self.api_service.update_step_status(job_id, step_id, JobSpecification.STATUS_RUNNING):
            self.logger.error(f"Failed to update step {step_id} status to running")
            return False
        
        try:
            # Execute the step function
            success = self._execute_step_function(function_name, step, job_id)
            
            if success:
                # Update step status to completed
                self.api_service.update_step_status(job_id, step_id, JobSpecification.STATUS_COMPLETED)
                self.logger.info(f"Finished step '{step_id}'")
                return True
            else:
                # Update step status to failed
                self.api_service.update_step_status(job_id, step_id, JobSpecification.STATUS_FAILED)
                self.logger.error(f"Step '{step_id}' failed during execution")
                return False
                
        except Exception as e:
            # Update step status to failed
            self.api_service.update_step_status(job_id, step_id, JobSpecification.STATUS_FAILED)
            self.logger.error(f"Step '{step_id}' failed with error: {e}")
            return False
    
    def _execute_step_function(self, function_name: str, step: Dict[str, Any], job_id: str) -> bool:
        """
        Execute the actual step function logic
        
        Args:
            function_name: Name of the function to execute
            step: Step configuration data
            job_id: ID of the parent job
            
        Returns:
            True if execution successful, False otherwise
        """
        try:
            # For now, simulate work with different logic based on function type
            self.logger.info(f"Executing function '{function_name}'...")
            
            # Simulate processing time based on function type
            processing_time = self._get_processing_time(function_name)
            time.sleep(processing_time)
            
            # Add your actual processing logic here based on function_name
            # For example:
            # if function_name == "recording":
            #     return self._process_recording(step)
            # elif function_name == "preprocessing":
            #     return self._process_preprocessing(step)
            # etc.
            
            # For now, simulate success (you can add failure simulation for testing)
            return True
            
        except Exception as e:
            self.logger.error(f"Error executing function '{function_name}': {e}")
            return False
    
    def _get_processing_time(self, function_name: str) -> float:
        """
        Get simulated processing time based on function type
        
        Args:
            function_name: Name of the function
            
        Returns:
            Processing time in seconds
        """
        # Different functions take different amounts of time (simulation)
        time_ranges = {
            "recording": (0.5, 1.0),
            "preprocessing": (1.0, 2.0),
            "sorting": (2.0, 4.0),
            "analyzer": (1.5, 3.0),
            "phy_export": (0.5, 1.5),
            "upload": (1.0, 2.5),
        }
        
        time_range = time_ranges.get(function_name, (1.0, 3.0))  # Default range
        return random.uniform(time_range[0], time_range[1])
    
    def validate_job_data(self, job_data: Dict[str, Any]) -> bool:
        """
        Validate job data structure
        
        Args:
            job_data: Job data dictionary to validate
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = ["job_id", "job_steps"]
        
        for field in required_fields:
            if field not in job_data:
                self.logger.error(f"Missing required field in job data: {field}")
                return False
        
        job_steps = job_data["job_steps"]
        if not isinstance(job_steps, list) or len(job_steps) == 0:
            self.logger.error("Job steps must be a non-empty list")
            return False
        
        # Validate each step
        for i, step in enumerate(job_steps):
            step_required_fields = ["identifier", "function"]
            for field in step_required_fields:
                if field not in step:
                    self.logger.error(f"Missing required field in step {i}: {field}")
                    return False
        
        return True
