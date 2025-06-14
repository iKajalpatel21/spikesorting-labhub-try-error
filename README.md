# This is a simple queue project

## Architecture
frontend <==> light-backend <==> heavy backend (aka worker)

### frontend
Allows you to put a new "job" in the queue. It has one or two parameters and a single button "submit".
The front end also has Rest API to fetch jobs and report job states. Correspondingly, there are two URLs for job fetching (for example, `https://127.0.0.1/jobs`) and for report state (for example, `https://127.0.0.1/jobs/#jobid`)

### light-backend
single-table DB. Table fields are `jobid`:LONG INT, `created`:TIME, `state`:CHOICE(pending, fetched, running, finished, failed), and one or two columns for parameters.

### heavy backend (aka worker)
Standalone Python code, which uses the `requests` package to fetch jobs and report states.

## Operations

1. Worker fetches jobs from the backend, requesting the `https://127.0.0.1/jobs` URL every 10 seconds. If no new jobs are in the queue, it gets json with empty dictionary `{}`. If there is a job, it gets JSON with job parameters `{"jobid": "b5b126669b43", "a":12, "b":27}`, where `a' and `b` just parameters provided by user ar the job submission. As the job is received, the worker sends the job state to the backend by sending `{"jobid": "b5b126669b43", "state": "running"}` to the URL `https://127.0.0.1/jobs/b5b126669b43` and sleeps `a' seconds. After that, it sends job state `{"jobid": "b5b126669b43", "state": "finished"}` to the same URL.
2. Frontend/light-backend accepts job orders from the users. On the submit button, they create a new record in the database with the status `pending`. When a worker requests a job from `https://127.0.0.1/jobs`, they check if there is any recording with the `pending` flag, and if there is, they form JSON and send it to the worker. The state of the record should be changed to `fetched`. When a worker reports a `running`,`finished`, or `field` state, the record should be updated to this state.

## Notes
First, try to implement this queue without any encryption or authentication. When it works, add encryption and then try to work out how to authenticate the worker.
