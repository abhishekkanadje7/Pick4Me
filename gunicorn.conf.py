import os

# Render assigns PORT dynamically (defaulting to 10000)
port = os.environ.get("PORT", "10000")
bind = f"0.0.0.0:{port}"

# Concurrency & Reliability
workers = int(os.environ.get("WEB_CONCURRENCY", 2))
threads = 4
worker_class = "gthread"
timeout = 120
keepalive = 5

accesslog = "-"
errorlog = "-"
loglevel = "info"
