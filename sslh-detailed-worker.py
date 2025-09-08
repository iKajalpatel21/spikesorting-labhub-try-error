#!/usr/bin/env python3
"""
Enhanced SSLH Dummy Worker with Detailed Step Reporting
Based on the original worker pattern with comprehensive logging and status updates.
"""

import os
import time
import requests
import urllib3
from datetime import datetime
import json
import logging
import random
import argparse

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging with detailed format
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(lineno)-6d- %(levelname)s - %(message)s"
)


# -----------------------------------------------------------------------------
# 1. Configuration Management
# -----------------------------------------------------------------------------
def load_config(config_file=None):
    """Load configuration from file or use defaults"""
    default_config = {
        "SERVER": "http://127.0.0.1:8000/qmodel",
        "TOKEN": "your_token_here",
        "API_TOKEN": "your_token_here",
        "POLLING_INTERVAL": 5,
        "SSL_VERIFY": False,
        "VERIFY_SSL": False,
    }

    if config_file and os.path.exists(config_file):
        try:
            with open(config_file, "r") as f:
                file_config = json.load(f)
                default_config.update(file_config)

                # Handle both TOKEN and API_TOKEN formats
                if "API_TOKEN" in file_config and "TOKEN" not in file_config:
                    default_config["TOKEN"] = file_config["API_TOKEN"]
                elif "TOKEN" in file_config and "API_TOKEN" not in file_config:
                    default_config["API_TOKEN"] = file_config["TOKEN"]

                logging.info(f"Loaded configuration from {config_file}")
        except Exception as e:
            logging.error(f"Failed to load config file {config_file}: {e}")
    else:
        logging.info("Using default configuration")

    return default_config


# -----------------------------------------------------------------------------
# 2. Enhanced Status Update Function
# -----------------------------------------------------------------------------
def update_the_status(job_id, status, step_id=None, config=None):
    """
    Makes an API call to update the status of a job or a specific job step.

    Args:
        job_id (str): The ID of the job
        status (str): The new status to set
        step_id (str, optional): The ID of the specific step to update
        config (dict): Configuration dictionary
    """
    if not config:
        logging.error("No configuration provided for status update")
        return

    # Use the official API endpoint for status updates
    status_url = f"{config['SERVER']}/status/{job_id}/"
    headers = {
        "Authorization": f"Token {config['TOKEN']}",
        "Content-Type": "application/json",
    }

    # Handle both SSL_VERIFY and VERIFY_SSL config formats
    ssl_verify = config.get("SSL_VERIFY", config.get("VERIFY_SSL", False))

    payload = {"status": status}

    # If step_id is provided, include it in the payload
    if step_id is not None:
        payload["step_id"] = str(step_id)
        payload["step_status"] = status

    try:
        logging.info(
            f"Updating status - Job: {job_id}, Status: '{status}'"
            + (f", Step: {step_id}" if step_id else "")
        )

        response = requests.post(
            status_url, json=payload, headers=headers, verify=ssl_verify
        )

        if response.status_code in [200, 201]:
            if step_id is not None:
                logging.info(
                    f"API call successful: Updated job {job_id}, step {step_id} to '{status}'"
                )
            else:
                logging.info(
                    f"API call successful: Updated job {job_id} to '{status}'"
                )
        else:
            logging.warning(
                f"API returned status code: {response.status_code} for job {job_id}"
            )

    except requests.exceptions.RequestException as e:
        if step_id is not None:
            logging.error(
                f"Failed to update job {job_id}, step {step_id} status to '{status}': {e}"
            )
        else:
            logging.error(f"Failed to update job {job_id} status to '{status}': {e}")


# -----------------------------------------------------------------------------
# 3. Enhanced Job Processing with Detailed Steps
# -----------------------------------------------------------------------------
def process_job(job_data, config):
    """Processes a single job with detailed step-by-step reporting."""
    job_id = job_data.get("job_id") or job_data.get("id")
    logging.info(f"Starting to process new job: {job_id}")
    logging.info(f"Job details: {json.dumps(job_data, indent=2)}")

    # Update job status to running
    update_the_status(job_id, "running", config=config)

    try:
        # Simulate detailed processing steps based on job data
        steps = simulate_processing_steps(job_data)

        logging.info(f"Generated {len(steps)} processing steps for job {job_id}")

        num_completed_steps = 0

        for i, step in enumerate(steps, 1):
            step_id = f"step_{i}"
            step_name = step["name"]
            duration = step["duration"]

            logging.info(
                f"[{i}/{len(steps)}] Processing step '{step_name}' for Job {job_id}"
            )
            update_the_status(job_id, "running", step_id, config)

            # Simulate the actual work with progress updates
            simulate_step_work(step_name, duration, job_id, step_id)

            logging.info(
                f"[{i}/{len(steps)}] Finished step '{step_name}' for Job {job_id}"
            )
            update_the_status(job_id, "completed", step_id, config)
            num_completed_steps += 1

            # Brief pause between steps
            time.sleep(0.5)

        # Check if all steps completed successfully
        if num_completed_steps == len(steps):
            update_the_status(job_id, "completed", config=config)
            logging.info(
                f"Job {job_id} finished successfully! Completed {num_completed_steps}/{len(steps)} steps"
            )
        else:
            logging.warning(
                f"Job {job_id} completed with issues: {num_completed_steps}/{len(steps)} steps"
            )

    except Exception as e:
        update_the_status(job_id, "failed", config=config)
        logging.error(f"Job {job_id} failed with an error: {e}")


def simulate_processing_steps(job_data):
    """Generate realistic processing steps based on job data."""
    steps = [
        {"name": "data_validation", "duration": random.uniform(1, 2)},
        {"name": "preprocessing", "duration": random.uniform(2, 4)},
    ]

    # Add algorithm-specific steps
    algorithm = job_data.get("algorithm", "default")
    if algorithm == "kilosort3":
        steps.extend(
            [
                {"name": "kilosort3_preprocessing", "duration": random.uniform(3, 5)},
                {"name": "spike_detection", "duration": random.uniform(5, 8)},
                {"name": "template_matching", "duration": random.uniform(4, 6)},
                {"name": "cluster_analysis", "duration": random.uniform(2, 4)},
            ]
        )
    elif algorithm == "mountainsort":
        steps.extend(
            [
                {"name": "filtering", "duration": random.uniform(2, 4)},
                {"name": "whitening", "duration": random.uniform(1, 3)},
                {"name": "sorting", "duration": random.uniform(6, 10)},
            ]
        )
    else:
        steps.extend(
            [
                {"name": "generic_processing", "duration": random.uniform(3, 6)},
                {"name": "analysis", "duration": random.uniform(2, 4)},
            ]
        )

    steps.append({"name": "result_packaging", "duration": random.uniform(1, 2)})

    return steps


def simulate_step_work(step_name, duration, job_id, step_id):
    """Simulate work for a processing step with detailed progress."""
    logging.info(f" Executing '{step_name}' (estimated {duration:.1f}s)...")

    # Break down the work into smaller chunks for progress reporting
    chunks = max(3, int(duration))
    chunk_duration = duration / chunks

    for chunk in range(chunks):
        progress = ((chunk + 1) / chunks) * 100
        logging.info(f"'{step_name}' progress: {progress:.0f}% (Job {job_id})")
        time.sleep(chunk_duration)

    logging.info(f"'{step_name}' execution completed for Job {job_id}")


# -----------------------------------------------------------------------------
# 4. Enhanced Main Worker Loop
# -----------------------------------------------------------------------------
def run_worker(config):
    """Main function for the worker with enhanced error handling and reporting."""
    next_job_url = f"{config['SERVER']}/next-job/"
    headers = {"Authorization": f"Token {config['TOKEN']}"}

    # Handle both SSL_VERIFY and VERIFY_SSL config formats
    ssl_verify = config.get("SSL_VERIFY", config.get("VERIFY_SSL", False))

    logging.info(f"Worker started successfully!")
    logging.info(f"Polling API at {next_job_url}")
    logging.info(f" Polling interval: {config['POLLING_INTERVAL']} seconds")
    logging.info(f"SSL verification: {ssl_verify}")

    consecutive_errors = 0
    max_consecutive_errors = 5

    while True:
        try:
            logging.info(f"Checking for new jobs...")

            # Send a GET request to fetch a pending job
            response = requests.get(
                next_job_url, headers=headers, verify=ssl_verify, timeout=30
            )

            if response.status_code == 200:
                consecutive_errors = 0  # Reset error counter
                try:
                    job_data = response.json()
                    logging.info(f"Received response from server")

                    # Check if we got actual job data
                    if job_data and ("job_id" in job_data or "id" in job_data):
                        job_id = job_data.get("job_id") or job_data.get("id")
                        logging.info(f"New job found: {job_id}")
                        process_job(job_data, config)
                    else:
                        logging.info("No pending jobs found. Waiting...")

                except json.JSONDecodeError as e:
                    logging.error(f"📄 Failed to decode JSON from API response: {e}")

            elif response.status_code == 204:
                consecutive_errors = 0
                logging.info("No jobs available (204 response)")
            else:
                consecutive_errors += 1
                logging.error(
                    f"API returned status code: {response.status_code} (Error #{consecutive_errors})"
                )

                if consecutive_errors >= max_consecutive_errors:
                    logging.critical(
                        f"Too many consecutive errors ({consecutive_errors}). Stopping worker."
                    )
                    break

        except requests.exceptions.RequestException as e:
            consecutive_errors += 1
            logging.error(
                f"Error connecting to the API: {e} (Error #{consecutive_errors})"
            )

            if consecutive_errors >= max_consecutive_errors:
                logging.critical(
                    f"Too many consecutive connection errors. Stopping worker."
                )
                break

        except Exception as e:
            consecutive_errors += 1
            logging.error(
                f"An unexpected error occurred in the worker loop: {e} (Error #{consecutive_errors})"
            )

        # Sleep before next poll
        logging.info(f"Sleeping for {config['POLLING_INTERVAL']} seconds...")
        time.sleep(config["POLLING_INTERVAL"])


# -----------------------------------------------------------------------------
# 5. Main Entry Point
# -----------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(
        description="SSLH Detailed Worker with Step Reporting"
    )
    parser.add_argument("-c", "--config", help="Configuration file path")
    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)

    logging.info("=" * 60)
    logging.info("SSLH DETAILED WORKER STARTING")
    logging.info("=" * 60)

    try:
        run_worker(config)
    except KeyboardInterrupt:
        logging.info("Worker stopped by user (Ctrl+C)")
    except Exception as e:
        logging.critical(f"Worker crashed with fatal error: {e}")
    finally:
        logging.info("=" * 60)
        logging.info("SSLH DETAILED WORKER STOPPED")
        logging.info("=" * 60)


if __name__ == "__main__":
    main()
