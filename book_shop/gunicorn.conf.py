"""Gunicorn configuration (``gunicorn book_shop.asgi:application -c gunicorn.conf.py``).

Gunicorn is the process manager; each worker runs the ASGI app on Uvicorn, so
the async cart views really run async. Everything can be overridden with
environment variables.
"""

import os

bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"

worker_class = "uvicorn_worker.UvicornWorker"
# WEB_CONCURRENCY is the de-facto standard name (Heroku, Render, ...).
workers = int(os.getenv("WEB_CONCURRENCY", "3"))

# Restart workers periodically (with jitter so they don't all go at once) to
# contain slow memory leaks.
max_requests = int(os.getenv("GUNICORN_MAX_REQUESTS", "1000"))
max_requests_jitter = int(os.getenv("GUNICORN_MAX_REQUESTS_JITTER", "100"))

timeout = int(os.getenv("GUNICORN_TIMEOUT", "30"))
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", "30"))
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", "5"))

# In-memory heartbeat files: avoids false worker timeouts on Docker's disk FS.
worker_tmp_dir = "/dev/shm"

accesslog = "-"
errorlog = "-"
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")
