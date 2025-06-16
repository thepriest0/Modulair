import multiprocessing

# Gunicorn configuration for production
bind = "0.0.0.0:10000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "gevent"
timeout = 120
keepalive = 5
max_requests = 1000
max_requests_jitter = 50
preload_app = True
worker_connections = 1000

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# SSL (if needed)
# keyfile = "path/to/keyfile"
# certfile = "path/to/certfile" 