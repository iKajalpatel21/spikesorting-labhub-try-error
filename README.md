# The general notes on what we want to achive and what you need to know for the project

## We are developint Spikesorting LabHub

SpikeSortingLabHub (SSLH) is an infrastructure for creating and executing spike sorting jobs.
It consists of three parts:

- Data storage -  for experimental data
- SSLH server provides:
  - user web interface to create, submit, and monitor the status of sorting jobs
  - job queue
  - Rest API for SSLH workers to fetch jobs and report progress
- one or more SSLH workers
   - Linux box(s) runs a python demon which:
   -  checks the job queue every n-second, 
   -  performs sorting jobs if present in the queue, and
   -  reports job progress to the server

This project targets a single laboratory infrastructure, therefore all operations are assumed local and does not expect cloud-based operations (at least now :). Neural recordings are stored on a NAS system which is shared by users in the lab and by SSLH-workers. 


## Technology
- SSLH is based on [`spikeinterface`](https://github.com/SpikeInterface/spikeinterface) packages and utilizes `singularity` containers to run spikesorters.
- `spikeinterface` functions are wrapped by `runthepipe` (should be rename) package which provides CLI interface and allows to encapsulate  any sequence of spikesorting steps into a JSON dictionary.
- SSLH targets [TrueNAS SCALE](https://www.truenas.com/truenas-scale/) as the NAS solution. Ability `TrueNAS SCALE` runs `Docker containers` allows combine storage solution and SSLH server in a single computer.
- SSLH server is based up on [`django`](https://www.djangoproject.com/)
- SSLH server uses [`django-rest-framework`](https://www.django-rest-framework.org/) to provide Rest API to workers
- SSLH worker accesses server rest API using [`requests`](https://requests.readthedocs.io/en/latest/)
- SSLH server uses a local SQLite database for job queue, metadata and logs.

Prerequisite: All server - user and server - worker communications must be TLS/SSL encrypted.


## Goals to develop first mailestone

1. if you are not familiar with gjango make a hello-world project, but ignore this step otherwize
2. if you are not familiar with gjango-rest-framework do the same
3. decide what web server to use is the next step - do research on that and let's discuss.
4. now the question is how to encrypt communications with this server. this can be tricky. We should discuss this later.
5. we will need to design a SQL schema for the queue very well - I would like to be heavily involved in this
6. finally you will need to design a simple front-end to upload json and put them into the queue.
7. pack all of this in the container so we can run on the test computer so we can debug worker-server communication.

