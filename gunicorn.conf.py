#!/usr/bin/env python3
"""
Gunicorn configuration for production deployment of QModel.
"""
import multiprocessing
import os

# Server socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests to prevent memory leaks
max_requests = 1000
max_requests_jitter = 50

# Logging
loglevel = "info"
accesslog = "logs/gunicorn_access.log"
errorlog = "logs/gunicorn_error.log"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "qmodel-labhub"

# Daemonize the Gunicorn process (set to False for systemd)
daemon = False

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Preload application for better performance
preload_app = True

# Enable auto-reload in development (disable in production)
reload = False


def when_ready(server):
    """Called just after the server is started."""
    server.log.info("QModel server is ready. Spawning workers")


def worker_int(worker):
    """Called just after a worker has been created."""
    worker.log.info("Worker received INT or QUIT signal")


def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.info("Worker spawned (pid: %s)", worker.pid)


def post_worker_init(worker):
    """Called just after a worker has initialized the application."""
    worker.log.info("Worker initialized (pid: %s)", worker.pid)


def worker_abort(worker):
    """Called when a worker process exits abnormally."""
    worker.log.info("Worker aborted (pid: %s)", worker.pid)
