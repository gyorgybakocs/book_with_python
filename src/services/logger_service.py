import logging
import os
from src.services.config_service import ConfigService

class LoggerService:
    """
    Singleton service for managing application logging through the root logger.
    It should be initialized once with settings from the ConfigService.
    """
    _instance = None

    def __init__(self):
        """
        The constructor is now empty. The service does nothing until explicitly
        configured via initialize_from_config.
        """
        pass

    @classmethod
    def get_instance(cls):
        """
        Returns the singleton instance of the LoggerService.
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def initialize_from_config(self, config: ConfigService):
        """
        Configures the root logger based on the provided configuration service.
        This is the main setup method for the logger.

        Args:
            config (ConfigService): The initialized configuration service instance.
        """
        log_format = config.get("logger.log_format", fallback="%(asctime)s %(levelname)s: %(message)s")
        log_level = config.get("logger.level", fallback="INFO")
        log_dir = config.get("paths.log_dir")
        process_log_file = config.get("logger.process_log")
        error_log_file = config.get("logger.error_log")

        root_logger = logging.getLogger()

        if hasattr(logging, log_level.upper()):
            root_logger.setLevel(getattr(logging, log_level.upper()))
        else:
            root_logger.setLevel(logging.INFO)

        root_logger.handlers.clear()

        formatter = logging.Formatter(log_format)

        if log_dir and process_log_file and error_log_file:
            os.makedirs(log_dir, exist_ok=True)

            info_path = os.path.join(log_dir, process_log_file)
            info_handler = logging.FileHandler(info_path, mode='w')
            info_handler.setLevel(logging.INFO)
            info_handler.setFormatter(formatter)
            info_handler.addFilter(lambda record: record.levelno == logging.INFO)
            root_logger.addHandler(info_handler)

            error_path = os.path.join(log_dir, error_log_file)
            error_handler = logging.FileHandler(error_path, mode='w')
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(formatter)
            root_logger.addHandler(error_handler)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, log_level.upper()) if hasattr(logging, log_level.upper()) else logging.INFO)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

        logging.info("Logging has been configured from the config file.")
