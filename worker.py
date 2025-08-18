# import time
# import requests
# import json

# # worker.py

# API_BASE_URL = "https://127.0.0.1:8000/api/experiments/"
# GET_NEXT_URL = API_BASE_URL + "get-next/"
# POLL_INTERVAL = 10  # seconds


# # def fetch_pending_jobs():
# #     try:
# #         response = requests.get(API_BASE_URL)
# #         if response.status_code == 200:
# #             experiments = response.json()
# #             for exp in experiments:
# #                 if exp.get("status") == "pending":
# #                     return exp
# #         else:
# #             print(f"[!] Failed to fetch jobs: {response.status_code}")
# #     except Exception as e:
# #         print(f"[!] Error fetching jobs: {e}")
# #     return None


# def fetch_next_job():
#     try:
#         url = f"{API_BASE_URL}get-next/"
#         response = requests.get(url)
#         if response.status_code == 200:
#             job = response.json()
#             if job:  # Make sure it's not empty {}
#                 return job
#         elif response.status_code == 204:
#             print("[•] No pending jobs. Got empty response.")
#         else:
#             print(f"[!] Failed to fetch next job: {response.status_code}")
#     except Exception as e:
#         print(f"[!] Error fetching next job: {e}")
#     return None


# def update_job_status(job_id, status, result_path=None, log_path=None):
#     payload = {
#         "status": status,
#     }
#     if result_path:
#         payload["result_path"] = result_path
#     if log_path:
#         payload["log_path"] = log_path

#     try:
#         url = f"{API_BASE_URL}{job_id}/"
#         response = requests.patch(url, json=payload)
#         if response.status_code in (200, 202):
#             print(f"[✓] Job {job_id} updated to {status}")
#         else:
#             print(f"[!] Failed to update job {job_id}: {response.status_code}")
#     except Exception as e:
#         print(f"[!] Error updating job {job_id}: {e}")


# def process_job(job):
#     job_id = job["id"]

#     try:
#         parameters = job.get("parameters", {})
#         a = parameters.get("a", 1)
#         b = parameters.get("b", 1)
#     except Exception as e:
#         print(f"[!] Failed to parse parameters for job {job_id}: {e}")
#         return

#     print(f"[•] Processing job {job_id} with a={a}, b={b}")
#     update_job_status(job_id, "running")

#     time.sleep(a)

#     result_path = f"results/job_{job_id}_result.txt"
#     log_path = f"results/job_{job_id}_log.txt"

#     with open(result_path, "w") as f:
#         f.write(f"{a} + {b} = {a + b}")

#     with open(log_path, "w") as f:
#         f.write(f"Processed job {job_id}")

#     update_job_status(job_id, "finished", result_path=result_path, log_path=log_path)


# def main():
#     print("[✓] Worker started. Polling for jobs...")
#     while True:
#         job = fetch_next_job()
#         if job:
#             process_job(job)
#         else:
#             print("[•] No pending jobs. Sleeping...")
#             time.sleep(POLL_INTERVAL)


# if __name__ == "__main__":
#     main()


# Code with SSL verification enabled

"""
TLS‑enabled Toy‑worker
----------------------
• polls GET  /api/experiments/get-next/   every 5 s
• immediately PATCHes the job to running
• sleeps a seconds (a is taken from the JSON parameters)
• writes a dummy result file in ./results/
• PATCHes the job to finished   (and stores result_path)

Works against the HTTPS dev‑server started with:

uvicorn labhub.asgi:application \
       --host 127.0.0.1 --port 8000 \
       --ssl-keyfile key.pem --ssl-certfile cert.pem
"""
import time
import requests
import pathlib
import urllib3

# --- CONFIG ---
API_BASE = "https://127.0.0.1:8000/api/experiments/"
GET_NEXT_URL = API_BASE + "get-next/"
POLL_INTERVAL = 5  # seconds
SERVER_CERT = "cert.pem"  # path to your SSL certificate
TOKEN = "3164e6a07c80cc496a11ec07839229e9c134a681"  # ← paste your real token from Django shell
HEADERS = {"Authorization": f"Token {TOKEN}"}

# Disable SSL warnings for self-signed certs (optional for local dev)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# --- FUNCTIONS ---
def fetch_next_job():
    try:
        response = requests.get(
            GET_NEXT_URL, headers=HEADERS, verify=SERVER_CERT
        )  # This should be verify = false (serch abput it)
        if response.status_code == 200 and response.json():
            return response.json()
        elif response.status_code == 204:
            print("[•] Queue is empty")
        else:
            print(f"[!] Error fetching job: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"[!] Exception fetching job: {e}")
    return None


def update_status(job_id, status, **extra):
    url = f"{API_BASE}{job_id}/"
    payload = {"status": status, **extra}
    try:
        response = requests.patch(
            url, json=payload, headers=HEADERS, verify=SERVER_CERT
        )
        print(f"[•] PATCH {status} → {response.status_code}")
    except Exception as e:
        print(f"[!] Exception updating job {job_id}: {e}")


def process_job(job):
    job_id = job["id"]
    params = job.get("parameters", {})
    a = params.get("a", 1)
    b = params.get("b", 1)

    print(f"[✓] Processing job {job_id}: a={a}, b={b}")
    update_status(job_id, "running")

    time.sleep(a)  # simulate work

    pathlib.Path("results").mkdir(exist_ok=True)
    result_path = f"results/job_{job_id}_result.txt"
    log_path = f"results/job_{job_id}_log.txt"

    with open(result_path, "w") as rf:
        rf.write(f"{a} + {b} = {a + b}\n")

    with open(log_path, "w") as lf:
        lf.write(f"Processed job {job_id} successfully.\n")

    update_status(job_id, "finished", result_path=result_path, log_path=log_path)


# --- MAIN LOOP ---
if __name__ == "__main__":
    print("[✓] Worker is online. Polling every", POLL_INTERVAL, "seconds")
    while True:
        job = fetch_next_job()
        if job:
            process_job(job)
        time.sleep(POLL_INTERVAL)

# Code with SSL verification enabled
# (This code is a complete worker that can be run to process jobs from the Django application.)
# It fetches jobs, processes them, and updates their status in the database.
# Make sure to run this worker in an environment where it can access the Django API.
# Ensure that the `results` directory exists or is created by the worker.
# The worker uses a self-signed certificate for HTTPS requests, so it disables SSL warnings.
# This worker is designed to run continuously, polling for new jobs every 5 seconds.
# It processes each job by simulating work based on the parameters provided in the job.
