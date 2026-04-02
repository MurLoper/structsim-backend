import multiprocessing
import os


bind = f"0.0.0.0:{os.getenv('APP_PORT', '6060')}"
worker_class = "gthread"
workers = max(2, int(os.getenv('GUNICORN_WORKERS', str(multiprocessing.cpu_count()))))
threads = max(4, int(os.getenv('GUNICORN_THREADS', '8')))
timeout = int(os.getenv('GUNICORN_TIMEOUT', '180'))
graceful_timeout = int(os.getenv('GUNICORN_GRACEFUL_TIMEOUT', '30'))
keepalive = int(os.getenv('GUNICORN_KEEPALIVE', '5'))
max_requests = int(os.getenv('GUNICORN_MAX_REQUESTS', '1000'))
max_requests_jitter = int(os.getenv('GUNICORN_MAX_REQUESTS_JITTER', '100'))
accesslog = "-"
errorlog = "-"
capture_output = True
loglevel = os.getenv('GUNICORN_LOG_LEVEL', 'info')
