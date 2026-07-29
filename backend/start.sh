#!/bin/bash
# Starts both the web server and the Celery worker in one container,
# so they share the same local filesystem (needed since this app
# currently uses local disk for uploaded files, not cloud storage).

celery -A workers.celery_app worker --loglevel=info --concurrency=2 &
uvicorn main:app --host 0.0.0.0 --port 8000