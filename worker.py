import time
import requests
import json

# worker.py

API_BASE_URL = "http://127.0.0.1:8000/api/experiments/"
POLL_INTERVAL = 5  # seconds


def fetch_pending_jobs():
    try:
        response = requests.get(API_BASE_URL)
        if response.status_code == 200:
            experiments = response.json()
            for exp in experiments:
                if exp.get("status") == "pending":
                    return exp
        else:
            print(f"[!] Failed to fetch jobs: {response.status_code}")
    except Exception as e:
        print(f"[!] Error fetching jobs: {e}")
    return None


def update_job_status(job_id, status, result_path=None, log_path=None):
    payload = {
        "status": status,
    }
    if result_path:
        payload["result_path"] = result_path
    if log_path:
        payload["log_path"] = log_path

    try:
        url = f"{API_BASE_URL}{job_id}/"
        response = requests.patch(url, json=payload)
        if response.status_code in (200, 202):
            print(f"[✓] Job {job_id} updated to {status}")
        else:
            print(f"[!] Failed to update job {job_id}: {response.status_code}")
    except Exception as e:
        print(f"[!] Error updating job {job_id}: {e}")


def process_job(job):
    job_id = job["id"]

    try:
        parameters = json.loads(job.get("parameters", "{}"))
        a = parameters.get("a", 1)
        b = parameters.get("b", 1)
    except Exception as e:
        print(f"[!] Failed to parse parameters for job {job_id}: {e}")
        return

    print(f"[•] Processing job {job_id} with a={a}, b={b}")
    update_job_status(job_id, "running")

    time.sleep(a)

    result_path = f"results/job_{job_id}_result.txt"
    log_path = f"results/job_{job_id}_log.txt"

    with open(result_path, "w") as f:
        f.write(f"{a} + {b} = {a + b}")

    with open(log_path, "w") as f:
        f.write(f"Processed job {job_id}")

    update_job_status(job_id, "finished", result_path=result_path, log_path=log_path)


def main():
    print("[✓] Worker started. Polling for jobs...")
    while True:
        job = fetch_pending_jobs()
        if job:
            process_job(job)
        else:
            print("[•] No pending jobs. Sleeping...")
            time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
