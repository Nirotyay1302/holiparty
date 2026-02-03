# Gunicorn config - optimized for Render free tier (512MB RAM)
import os

workers = 1
threads = 2
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 5
max_requests = 500
max_requests_jitter = 50
preload = True
