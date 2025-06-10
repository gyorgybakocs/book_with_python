import yaml
import os
from src.exceptions.config_exceptions import ConfigurationError

class ConfigService:
    """
    Singleton service that manages a unified YAML configuration.
    Provides centralized, read-only access to all application settings.
    This class should be initialized once at the start of the application.
    """
    _instance = None
    _config = None

    @classmethod
    def get_instance(cls):
        """
        Provides access to the singleton instance.

        Raises:
            RuntimeError: If the service has not been initialized by calling initialize() first.

        Returns:
            ConfigService: The singleton instance of the service.
        """
        if cls._instance is None:
            raise RuntimeError("ConfigService not initialized. Call initialize() first.")
        return cls._instance

    @classmethod
    def initialize(cls, config_file: str):
        """
        Initializes the singleton instance by loading the configuration from a YAML file.
        This method must be called before get_instance() is used for the first time.

        Args:
            config_file (str): The path to the YAML configuration file.

        Raises:
            RuntimeError: If the service has already been initialized.

        Returns:
            ConfigService: The newly created and initialized singleton instance.
        """
        if cls._instance is not None:
            raise RuntimeError("ConfigService already initialized.")
        cls._instance = cls()
        cls._instance._load_config(config_file)
        return cls._instance

    def _load_config(self, config_file: str):
        """
        Private method to load and parse the YAML configuration file.

        Args:
            config_file (str): The path to the YAML configuration file.

        Raises:
            ConfigurationError: If the file is not found or if there's an error parsing the YAML.
        """
        if not os.path.exists(config_file):
            raise ConfigurationError(f"Config file not found: {config_file}")
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Error parsing YAML file: {e}")

    def get(self, key: str, fallback=None):
        """
        Retrieves a value from the loaded configuration using dot notation.

        Example:
            config.get('paths.font_path')

        Args:
            key (str): A string representing the path to the value, with levels separated by dots.
            fallback: The default value to return if the key is not found. Defaults to None.

        Returns:
            The requested value from the configuration, or the fallback value if not found.
        """
        keys = key.split('.')
        value = self._config
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return fallback

