# import os
# import time
# import requests
# from datetime import datetime
# import json
# import logging
# import random

# # Configure logging
# logging.basicConfig(
#     level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
# )

# # -----------------------------------------------------------------------------
# # 1. Worker Configuration
# # -----------------------------------------------------------------------------
# # Single API endpoint for both fetching a job and updating its status
# API_URL = "http://localhost:8000/job-queue/getthenextjob/"
# POLLING_INTERVAL_SECONDS = 5

# # Security token from the user for API authentication
# TOKEN = "e1997396f5c992a1cc89ea5c8a518ab22bbab65f"
# HEADERS = {"Authorization": f"Token {TOKEN}"}

# print(
#     f"Worker started. Polling API at {API_URL} every {POLLING_INTERVAL_SECONDS} seconds..."
# )


# # -----------------------------------------------------------------------------
# # 2. Status Update Functions
# # -----------------------------------------------------------------------------
# def update_job_status(job_id, status):
#     """Makes an API call to update the status of a job via a POST request."""
#     payload = {"job_id": str(job_id), "status": status}
#     try:
#         # Use the same API_URL for POST requests
#         response = requests.post(API_URL, json=payload, headers=HEADERS)
#         response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
#         logging.info(f"API call successful: Updated job {job_id} to '{status}'.")
#     except requests.exceptions.RequestException as e:
#         logging.error(f"Failed to update job {job_id} status to '{status}': {e}")


# def update_job_step_status(job_id, step_id, status):
#     """Makes an API call to update the status of a specific job step via a POST request."""
#     payload = {"job_id": str(job_id), "step_id": str(step_id), "status": status}
#     try:
#         # Use the same API_URL for POST requests
#         response = requests.post(API_URL, json=payload, headers=HEADERS)
#         response.raise_for_status()
#         logging.info(
#             f"API call successful: Updated job {job_id}, step {step_id} to '{status}'."
#         )
#     except requests.exceptions.RequestException as e:
#         logging.error(
#             f"Failed to update job {job_id}, step {step_id} status to '{status}': {e}"
#         )


# # -----------------------------------------------------------------------------
# # 3. Main Worker Loop
# # -----------------------------------------------------------------------------
# def run_worker():
#     """Main function for the worker. It polls an API endpoint for new jobs."""
#     while True:
#         try:
#             # Send a GET request to the API to fetch a pending job
#             response = requests.get(API_URL, headers=HEADERS)

#             if response.status_code == 200:
#                 job_data = response.json().get("job")
#                 if job_data:
#                     process_job(job_data)
#                 else:
#                     logging.info("No pending jobs found. Waiting...")

#             elif response.status_code == 404:
#                 logging.info("No pending jobs found. Waiting...")
#             else:
#                 logging.error(
#                     f"API returned an unexpected status code: {response.status_code}"
#                 )

#         except requests.exceptions.RequestException as e:
#             logging.error(f"Error connecting to the API: {e}")
#         except json.JSONDecodeError:
#             logging.error("Failed to decode JSON from API response.")
#         except Exception as e:
#             logging.error(f"An unexpected error occurred in the worker loop: {e}")

#         time.sleep(POLLING_INTERVAL_SECONDS)


# def process_job(job_data):
#     """Processes a single job by iterating through its steps."""
#     job_id = job_data["job_id"]
#     logging.info(f"Starting to process new job: {job_id}")

#     update_job_status(job_id, "running")

#     try:
#         num_completed_steps = 0
#         for step in job_data["steps"]:
#             step_id = step["step_id"]
#             function_name = step["function"]

#             logging.info(
#                 f"[{datetime.now()}] Processing step '{step['identifier']}' for Job {job_id}"
#             )
#             update_job_step_status(job_id, step_id, "running")

#             # --- Your processing logic would go here ---
#             logging.info(
#                 f"[{datetime.now()}] Simulating work for function '{function_name}'..."
#             )
#             time.sleep(random.uniform(1, 3))  # Simulate a task
#             # --- End of processing logic ---

#             logging.info(f"[{datetime.now()}] Finished step '{step['identifier']}'.")
#             update_job_step_status(job_id, step_id, "completed")
#             num_completed_steps += 1

#         if num_completed_steps == len(job_data["steps"]):
#             update_job_status(job_id, "finished")
#             logging.info(f"Job {job_id} finished successfully.")

#     except Exception as e:
#         update_job_status(job_id, "failed")
#         logging.error(f"Job {job_id} failed with an error: {e}")


# if __name__ == "__main__":
#     run_worker()


import os
import time
import requests
from datetime import datetime
import json
import logging
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# -----------------------------------------------------------------------------
# 1. Worker Configuration
# -----------------------------------------------------------------------------
# Single API endpoint for both fetching a job and updating its status
API_URL = "http://localhost:8000/job-queue/getthenextjob/"
POLLING_INTERVAL_SECONDS = 5

# Security token from the user for API authentication
TOKEN = "7043591ad29f88607f2b109bfba5044eac892785"
HEADERS = {"Authorization": f"Token {TOKEN}"}

print(
    f"Worker started. Polling API at {API_URL} every {POLLING_INTERVAL_SECONDS} seconds..."
)


# -----------------------------------------------------------------------------
# 2. Status Update Function
# -----------------------------------------------------------------------------
def update_the_status(job_id, status, step_id=None):
    """
    Makes an API call to update the status of a job or a specific job step via a POST request.

    Args:
        job_id (str): The ID of the job
        status (str): The new status to set
        step_id (str, optional): The ID of the specific step to update. If None, updates the main job status.
    """
    payload = {"job_id": str(job_id), "status": status}

    # If step_id is provided, include it in the payload to update a specific step
    if step_id is not None:
        payload["step_id"] = str(step_id)

    try:
        # Use the same API_URL for POST requests
        response = requests.post(API_URL, json=payload, headers=HEADERS)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

        # Log the appropriate success message based on whether we're updating a job or step
        if step_id is not None:
            logging.info(
                f"API call successful: Updated job {job_id}, step {step_id} to '{status}'."
            )
        else:
            logging.info(f"API call successful: Updated job {job_id} to '{status}'.")

    except requests.exceptions.RequestException as e:
        # Log the appropriate error message based on whether we're updating a job or step
        if step_id is not None:
            logging.error(
                f"Failed to update job {job_id}, step {step_id} status to '{status}': {e}"
            )
        else:
            logging.error(f"Failed to update job {job_id} status to '{status}': {e}")


# -----------------------------------------------------------------------------
# 3. Main Worker Loop
# -----------------------------------------------------------------------------
def run_worker():
    """Main function for the worker. It polls an API endpoint for new jobs."""
    while True:
        try:
            # Send a GET request to the API to fetch a pending job
            response = requests.get(API_URL, headers=HEADERS)

            # Check if the response was successful
            if response.status_code == 200:
                job_data = response.json()
                logging.info(f"Received response: {job_data}")
                # Check if we got actual job data (has job_id) or empty response
                if job_data and "job_id" in job_data:
                    logging.info(f"Processing job: {job_data['job_id']}")
                    process_job(job_data)
                else:
                    logging.info("No pending jobs found. Waiting...")
            else:
                logging.error(f"API returned status code: {response.status_code}")

        except requests.exceptions.RequestException as e:
            logging.error(f"Error connecting to the API: {e}")
        except json.JSONDecodeError:
            logging.error("Failed to decode JSON from API response.")
        except Exception as e:
            logging.error(f"An unexpected error occurred in the worker loop: {e}")

        time.sleep(POLLING_INTERVAL_SECONDS)


def process_job(job_data):
    """
    Processes a single job by iterating through its steps.

    Actual API response format:
    {
        "version": "0.4.1",
        "si": "0.101.0",
        "job_id": "...",
        "job_evn": {...},
        "job_steps": [
            {"function": "...", "identifier": "...", "depends": [...]},
            ...
        ],
        "identifier_hash": {...config...}  # Config blocks by identifier
    }
    """
    job_id = job_data.get("job_id")
    job_steps = job_data.get("job_steps", [])

    if not job_id or not job_steps:
        logging.error("Invalid job data - missing job_id or job_steps")
        return

    logging.info(f"Starting to process new job: {job_id}")
    logging.info(f"Version: {job_data.get('version')}, SI: {job_data.get('si')}")
    logging.info(f"Total steps to process: {len(job_steps)}")

    update_the_status(job_id, "running")

    try:
        completed_steps = set()
        num_completed_steps = 0

        for step in job_steps:
            step_identifier = step.get("identifier")
            function_name = step.get("function")
            depends_on = step.get("depends", [])

            if not step_identifier:
                logging.warning(f"Step missing identifier: {step}")
                continue

            # Check dependencies before processing
            logging.info(f"\n{'='*80}")
            logging.info(
                f"Processing step: {function_name} ({step_identifier[:16]}...)"
            )
            logging.info(
                f"Dependencies: {[d[:16] + '...' if len(d) > 16 else d for d in depends_on]}"
            )

            # Wait for all dependencies to complete
            if depends_on:
                missing_deps = [d for d in depends_on if d not in completed_steps]
                if missing_deps:
                    logging.warning(
                        f"Waiting for dependencies: {[d[:16] + '...' for d in missing_deps]}"
                    )
                    # In a real scenario, you'd wait or skip this step
                    # For simulation, we'll just log it

            # Load configuration for this step
            step_config = job_data.get(step_identifier, {})
            logging.info(f"Step config: {str(step_config)[:100]}...")

            # Update step status to running
            update_the_status(job_id, "running", step_identifier)

            # --- Your processing logic would go here ---
            logging.info(f"Executing {function_name}...")
            time.sleep(random.uniform(1, 3))  # Simulate work
            # --- End of processing logic ---

            # Mark step as completed
            update_the_status(job_id, "completed", step_identifier)
            completed_steps.add(step_identifier)
            num_completed_steps += 1
            logging.info(f"✓ Completed step: {function_name}")

        # All steps completed
        if num_completed_steps == len(job_steps):
            update_the_status(job_id, "finished")
            logging.info(f"\n{'='*80}")
            logging.info(f"✓ Job {job_id} finished successfully!")
            logging.info(f"{'='*80}\n")
        else:
            logging.warning(
                f"Only {num_completed_steps}/{len(job_steps)} steps completed"
            )

    except Exception as e:
        update_the_status(job_id, "failed")
        logging.error(f"Job {job_id} failed with an error: {e}", exc_info=True)


if __name__ == "__main__":
    run_worker()
