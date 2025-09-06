"""
Job Management Service for Django views.
Handles job creation, validation, and data processing logic.
"""

import json
import hashlib
from typing import Dict, Any, List, Optional, Tuple
from django.db import transaction
from django.core.exceptions import ValidationError

from ..models import Job, JobStep, StepConfig
from config.constants import JobSpecification, ErrorMessages


class JobManagementService:
    """Service for managing job creation and processing"""
    
    @staticmethod
    def compute_fingerprint(config_block: Dict[str, Any]) -> str:
        """
        Generate SHA-256 hash for configuration block
        
        Args:
            config_block: Configuration data to hash
            
        Returns:
            SHA-256 hash string
        """
        json_str = json.dumps(config_block, sort_keys=True)
        return hashlib.sha256(json_str.encode("utf-8")).hexdigest()
    
    @staticmethod
    def validate_job_json(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate job JSON structure
        
        Args:
            data: Job JSON data to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check for required fields
        if not data.get("job_steps"):
            return False, ErrorMessages.MISSING_JOB_STEPS
        
        job_steps = data["job_steps"]
        if not isinstance(job_steps, list) or len(job_steps) == 0:
            return False, "job_steps must be a non-empty list"
        
        # Validate each step
        for i, step in enumerate(job_steps):
            if not step.get("identifier"):
                return False, f"Step {i} missing 'identifier' field"
            if not step.get("function"):
                return False, f"Step {i} missing 'function' field"
                
            # Validate that step configuration exists in data
            identifier = step["identifier"]
            if identifier not in data:
                return False, f"Missing configuration block for step '{identifier}'"
        
        return True, None
    
    @classmethod
    def create_job_from_json(cls, json_data: Dict[str, Any]) -> Job:
        """
        Create a new job from JSON data
        
        Args:
            json_data: Validated job JSON data
            
        Returns:
            Created Job instance
            
        Raises:
            ValidationError: If validation fails
            Exception: If database operation fails
        """
        # Validate the JSON data
        is_valid, error_message = cls.validate_job_json(json_data)
        if not is_valid:
            raise ValidationError(error_message)
        
        # Extract job data
        job_env_config = json_data.get("job_evn", {})
        job_steps_list = json_data.get("job_steps", [])
        version = json_data.get("version")
        si = json_data.get("si")
        
        with transaction.atomic():
            # Process step configurations
            step_configs = {}
            
            for step in job_steps_list:
                identifier = step.get("identifier")
                config_block = json_data.get(identifier, {})
                fingerprint = cls.compute_fingerprint(config_block)
                step_configs[identifier] = fingerprint
                
                # Create or get existing step config
                StepConfig.objects.get_or_create(
                    config_block_hash=fingerprint,
                    defaults={"config_block": config_block},
                )
            
            # Create the job
            job = Job.objects.create(
                job_env_config=job_env_config,
                status=JobSpecification.STATUS_PENDING
            )
            
            # Create job steps
            for step in job_steps_list:
                identifier = step.get("identifier")
                function = step.get("function")
                depends_on = step.get("depends", [])
                config_hash = step_configs[identifier]
                
                JobStep.objects.create(
                    identifier=identifier,
                    job=job,
                    function=function,
                    depends_on=depends_on,
                    config_block_hash_id=config_hash,
                    status=JobSpecification.STATUS_PENDING,
                )
            
            return job
    
    @staticmethod
    def get_next_pending_job() -> Optional[Job]:
        """
        Get the next pending job and mark it as fetched
        
        Returns:
            Job instance if available, None otherwise
        """
        with transaction.atomic():
            job = (
                Job.objects.select_for_update()
                .filter(status=JobSpecification.STATUS_PENDING)
                .order_by("created_at")
                .first()
            )
            
            if job:
                job.status = JobSpecification.STATUS_FETCHED
                job.save()
            
            return job
    
    @staticmethod
    def build_job_response(job: Job) -> Dict[str, Any]:
        """
        Build API response for a job
        
        Args:
            job: Job instance to build response for
            
        Returns:
            Job data dictionary matching API specification
        """
        job_steps = job.jobstep_set.all()
        
        # Build base response
        job_data = {
            "version": JobSpecification.VERSION,
            "si": JobSpecification.SI_VERSION,
            "job_id": str(job.job_id),
            "job_evn": job.job_env_config,
            "job_steps": [
                {
                    "function": step.function,
                    "identifier": step.identifier,
                    "depends": step.depends_on,
                }
                for step in job_steps
            ],
        }
        
        # Add individual step configuration blocks as top-level keys
        for step in job_steps:
            job_data[step.identifier] = step.config_block_hash.config_block
        
        return job_data
    
    @staticmethod
    def update_job_status(job_id: str, status: str) -> Job:
        """
        Update job status
        
        Args:
            job_id: ID of job to update
            status: New status
            
        Returns:
            Updated job instance
            
        Raises:
            Job.DoesNotExist: If job not found
        """
        job = Job.objects.get(job_id=job_id)
        job.status = status
        job.save()
        return job
    
    @staticmethod
    def update_step_status(job_id: str, step_id: str, status: str) -> JobStep:
        """
        Update job step status
        
        Args:
            job_id: ID of parent job
            step_id: ID of step to update
            status: New status
            
        Returns:
            Updated job step instance
            
        Raises:
            JobStep.DoesNotExist: If step not found
        """
        step = JobStep.objects.get(identifier=step_id, job__job_id=job_id)
        step.status = status
        step.save()
        return step
