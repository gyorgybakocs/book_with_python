import logging
import os

# Log file paths (same as used in the Bash script)
LOG_DIR = "log"
PROCESS_LOG = os.path.join(LOG_DIR, "process.log")
ERROR_LOG = os.path.join(LOG_DIR, "process-error.log")

# Ensure the log directory exists
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Remove any existing root handlers to prevent duplicate logging
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

# Create a dedicated logger for Python
python_logger = logging.getLogger("PythonLogger")
python_logger.setLevel(logging.DEBUG)  # Log everything (DEBUG, INFO, WARNING, ERROR, CRITICAL)

# 🔥 Ensure logs do NOT propagate to the root logger
python_logger.propagate = False

# Log format
formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")

# INFO and DEBUG logs go to process.log
info_handler = logging.FileHandler(PROCESS_LOG)
info_handler.setLevel(logging.INFO)
info_handler.setFormatter(formatter)
info_handler.addFilter(lambda record: record.levelno == logging.INFO)

# WARNING, ERROR, and CRITICAL logs go to process-error.log
error_handler = logging.FileHandler(ERROR_LOG)
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(formatter)

# Clear existing handlers (prevents accidental root logger usage)
python_logger.handlers.clear()

# Add handlers to the logger
python_logger.addHandler(info_handler)
python_logger.addHandler(error_handler)
