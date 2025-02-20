import logging
import os


class LoggerService:
    """
    Service for managing application logging through root logger.
    Starts with basic configuration, then updates with settings from config.
    """
    _instance = None

    def __init__(self):
        """Initialize service with basic root logger configuration"""
        self._setup_initial_logger()

    @classmethod
    def get_instance(cls):
        """Returns singleton instance, creating it with basic logger if needed"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _setup_initial_logger(self):
        """Sets up basic root logger for startup phase"""
        print("Setting up initial root logger...")

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)

        # Clear any existing handlers
        root_logger.handlers.clear()

        # Add console handler for startup phase
        formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        root_logger.addHandler(handler)

    def initialize_from_config(self, config):
        """Updates root logger configuration with settings from config"""
        # Get logger settings from config
        logger_name = config.get_cfg("logger", "name")
        process_log = config.get_cfg("logger", "process_log")
        error_log = config.get_cfg("logger", "error_log")
        log_format = config.get_cfg("logger", "log_format")
        log_dir = config.get_cfg("paths", "log_dir")

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)

        # Clear existing handlers from initial setup
        root_logger.handlers.clear()

        # Create formatter
        formatter = logging.Formatter(log_format or "[%(asctime)s] %(levelname)s: %(message)s")

        # Setup handlers
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        # Setup info handler
        info_path = os.path.join(log_dir, process_log)
        info_handler = logging.FileHandler(info_path)
        info_handler.setLevel(logging.INFO)
        info_handler.setFormatter(formatter)
        info_handler.addFilter(lambda record: record.levelno == logging.INFO)
        root_logger.addHandler(info_handler)

        # Setup error handler
        error_path = os.path.join(log_dir, error_log)
        error_handler = logging.FileHandler(error_path)
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        root_logger.addHandler(error_handler)

        # Add console handler for immediate feedback
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
