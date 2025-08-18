#!/usr/bin/env python3
"""
Production-ready QModel worker with SSL/TLS support and environment configuration.
"""
import os
import time
import requests
from datetime import datetime
import json
import logging
import random
import ssl

try:
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
except ImportError:
    # Fallback for different urllib3 versions
    HTTPAdapter = None
    Retry = None
import certifi
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging with file output for production
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
log_file = os.getenv("LOG_FILE", "qmodel_worker.log")

logging.basicConfig(
    level=getattr(logging, log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - [%(process)d] %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler(log_file, mode="a")],
)

logger = logging.getLogger(__name__)


class QModelWorker:
    """Production-ready QModel worker with SSL/TLS support."""

    def __init__(self):
        # Environment-based configuration
        self.api_url = os.getenv(
            "API_URL", "http://localhost:8000/qmodel/getthenextjob/"
        )
        self.polling_interval = int(os.getenv("POLLING_INTERVAL_SECONDS", "5"))
        self.token = os.getenv("AUTH_TOKEN", "e1997396f5c992a1cc89ea5c8a518ab22bbab65f")
        self.ssl_verify = os.getenv("SSL_VERIFY", "True").lower() == "true"

        # Setup headers
        self.headers = {"Authorization": f"Token {self.token}"}

        # Setup session with retry strategy and SSL configuration
        self.session = self._setup_session()

        logger.info(
            f"QModel Worker initialized - API: {self.api_url}, SSL Verify: {self.ssl_verify}"
        )

    def _setup_session(self):
        """Setup requests session with retry strategy and SSL configuration."""
        session = requests.Session()

        # Retry strategy for network resilience (if available)
        if HTTPAdapter and Retry:
            try:
                retry_strategy = Retry(
                    total=3,
                    status_forcelist=[429, 500, 502, 503, 504],
                    allowed_methods=[
                        "HEAD",
                        "GET",
                        "PUT",
                        "DELETE",
                        "OPTIONS",
                        "TRACE",
                        "POST",
                    ],
                    backoff_factor=1,
                )
            except TypeError:
                # Fallback for older urllib3 versions
                retry_strategy = Retry(
                    total=3,
                    status_forcelist=[429, 500, 502, 503, 504],
                    backoff_factor=1,
                )

            adapter = HTTPAdapter(max_retries=retry_strategy)
            session.mount("http://", adapter)
            session.mount("https://", adapter)

        # SSL Configuration
        if self.api_url.startswith("https://"):
            if self.ssl_verify:
                session.verify = certifi.where()
            else:
                session.verify = False
                try:
                    import urllib3

                    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                except ImportError:
                    pass
                logger.warning(
                    "SSL verification disabled - not recommended for production!"
                )

        return session

    def update_the_status(self, job_id, status, step_id=None):
        """
        Makes an API call to update the status of a job or a specific job step.

        Args:
            job_id (str): The ID of the job
            status (str): The new status to set
            step_id (str, optional): The ID of the specific step to update
        """
        payload = {"job_id": str(job_id), "status": status}

        if step_id is not None:
            payload["step_id"] = str(step_id)

        try:
            response = self.session.post(
                self.api_url, json=payload, headers=self.headers, timeout=30
            )
            response.raise_for_status()

            if step_id is not None:
                logger.info(f"Updated job {job_id}, step {step_id} to '{status}'")
            else:
                logger.info(f"Updated job {job_id} to '{status}'")

        except requests.exceptions.SSLError as e:
            logger.error(f"SSL/TLS error: {e}")
        except requests.exceptions.Timeout as e:
            logger.error(f"Request timeout: {e}")
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error: {e}")
        except requests.exceptions.RequestException as e:
            if step_id is not None:
                logger.error(
                    f"Failed to update job {job_id}, step {step_id} to '{status}': {e}"
                )
            else:
                logger.error(f"Failed to update job {job_id} to '{status}': {e}")

    def run_worker(self):
        """Main worker loop that polls for jobs."""
        logger.info(
            f"QModel Worker started. Polling API every {self.polling_interval} seconds..."
        )

        while True:
            try:
                response = self.session.get(
                    self.api_url, headers=self.headers, timeout=30
                )

                if response.status_code == 200:
                    job_data = response.json()
                    logger.debug(f"Received response: {job_data}")

                    if job_data and "job_id" in job_data:
                        logger.info(f"Processing job: {job_data['job_id']}")
                        self.process_job(job_data)
                    else:
                        logger.debug("No pending jobs found. Waiting...")
                else:
                    logger.error(f"API returned status code: {response.status_code}")

            except requests.exceptions.SSLError as e:
                logger.error(f"SSL/TLS error in main loop: {e}")
            except requests.exceptions.RequestException as e:
                logger.error(f"Error connecting to the API: {e}")
            except json.JSONDecodeError:
                logger.error("Failed to decode JSON from API response")
            except Exception as e:
                logger.error(f"Unexpected error in worker loop: {e}")

            time.sleep(self.polling_interval)

    def process_job(self, job_data):
        """Process a single job by iterating through its steps."""
        job_id = job_data["job_id"]
        logger.info(f"Starting to process job: {job_id}")

        self.update_the_status(job_id, "running")

        try:
            num_completed_steps = 0
            for step in job_data["steps"]:
                step_id = step["step_id"]
                function_name = step["function"]

                logger.info(f"Processing step '{step['identifier']}' for job {job_id}")
                self.update_the_status(job_id, "running", step_id)

                # Simulate work (replace with actual processing logic)
                logger.info(f"Simulating work for function '{function_name}'...")
                time.sleep(random.uniform(1, 3))

                logger.info(f"Finished step '{step['identifier']}'")
                self.update_the_status(job_id, "completed", step_id)
                num_completed_steps += 1

            if num_completed_steps == len(job_data["steps"]):
                self.update_the_status(job_id, "finished")
                logger.info(f"Job {job_id} finished successfully")

        except Exception as e:
            self.update_the_status(job_id, "failed")
            logger.error(f"Job {job_id} failed with error: {e}")


def main():
    """Entry point for the production worker."""
    try:
        worker = QModelWorker()
        worker.run_worker()
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
    except Exception as e:
        logger.error(f"Worker failed to start: {e}")
        raise


if __name__ == "__main__":
    main()
