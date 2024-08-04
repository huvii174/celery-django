import os
import logging
from concurrent_log_handler import ConcurrentTimedRotatingFileHandler

logger = logging.getLogger('batch-celery-logger')
logger.setLevel(logging.DEBUG)

loki_url = os.getenv('LOKI_URL', 'http://localhost:3100/loki/api/v1/push')
log_file = os.getenv('LOG_FILE', "/var/log/batch-celery.log")
max_bytes = os.getenv('LOG_MAX_BYTES', 10485760)
backup_count = os.getenv('LOG_BACKUP_COUNT', 7)

# Concurrent log handler
logfile = os.path.abspath(log_file)
rotateHandler = ConcurrentTimedRotatingFileHandler(filename=logfile, when="MIDNIGHT", interval=1, mode="a",
                                                   maxBytes=int(max_bytes), backupCount=int(backup_count),
                                                   use_gzip=True)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
rotateHandler.setFormatter(formatter)
logger.addHandler(rotateHandler)


# Function to get the logger
def get_logger():
    return logger