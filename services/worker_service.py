"""
Worker Service for orchestrating the main worker loop and job polling.
This service manages the overall worker lifecycle and coordinates between API and job processing.
"""

import logging
import time
from typing import Optional

from config.constants import Environment, WorkerConfig
from services.api_service import APIService
from services.job_processor import JobProcessor


class WorkerService:
    """Main worker service that orchestrates job polling and processing"""
    
    def __init__(self, environment: str = Environment.PRODUCTION):
        """
        Initialize worker service
        
        Args:
            environment: Environment to run in (local, production, localhost_https)
        """
        self.environment = environment
        self.api_service = APIService(environment)
        self.job_processor = JobProcessor(self.api_service)
        self.logger = logging.getLogger(__name__)
        self.running = False
        
    def start(self):
        """Start the worker main loop"""
        self.running = True
        
        # Log startup information
        api_info = self.api_service.get_api_info()
        self.logger.info(f"Worker starting in {api_info['environment']} environment")
        self.logger.info(f"Polling API at {api_info['api_url']}")
        self.logger.info(f"SSL Verify: {api_info['ssl_verify']}")
        self.logger.info(f"Polling interval: {WorkerConfig.POLLING_INTERVAL_SECONDS} seconds")
        
        try:
            self._main_loop()
        except KeyboardInterrupt:
            self.logger.info("Worker stopped by user")
        except Exception as e:
            self.logger.error(f"Worker stopped due to error: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the worker"""
        self.running = False
        self.logger.info("Worker stopped")
    
    def _main_loop(self):
        """Main worker polling loop"""
        while self.running:
            try:
                # Attempt to get the next job
                job_data = self.api_service.get_next_job()
                
                if job_data:
                    # Validate job data before processing
                    if self.job_processor.validate_job_data(job_data):
                        self.logger.info(f"Processing job: {job_data['job_id']}")
                        success = self.job_processor.process_job(job_data)
                        
                        if success:
                            self.logger.info(f"Job {job_data['job_id']} completed successfully")
                        else:
                            self.logger.error(f"Job {job_data['job_id']} failed")
                    else:
                        self.logger.error(f"Invalid job data received: {job_data.get('job_id', 'unknown')}")
                else:
                    self.logger.debug("No pending jobs found, waiting...")
                
            except Exception as e:
                self.logger.error(f"Error in worker main loop: {e}")
                # Continue running even if there's an error
            
            # Wait before polling again
            time.sleep(WorkerConfig.POLLING_INTERVAL_SECONDS)
    
    def process_single_job(self) -> bool:
        """
        Process a single job (useful for testing)
        
        Returns:
            True if a job was processed, False if no jobs available
        """
        try:
            job_data = self.api_service.get_next_job()
            
            if job_data:
                if self.job_processor.validate_job_data(job_data):
                    return self.job_processor.process_job(job_data)
                else:
                    self.logger.error(f"Invalid job data: {job_data.get('job_id', 'unknown')}")
                    return False
            else:
                self.logger.info("No jobs available")
                return False
                
        except Exception as e:
            self.logger.error(f"Error processing single job: {e}")
            return False
    
    def get_status(self) -> dict:
        """Get current worker status"""
        api_info = self.api_service.get_api_info()
        return {
            "running": self.running,
            "environment": self.environment,
            "api_url": api_info["api_url"],
            "polling_interval": WorkerConfig.POLLING_INTERVAL_SECONDS,
            "ssl_verify": api_info["ssl_verify"]
        }
