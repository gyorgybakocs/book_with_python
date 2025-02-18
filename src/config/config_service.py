import configparser
import json
import os

from src.exceptions.onfig_exceptions import ConfigurationError
from src.logger import python_logger
from src.service_factory import get_json


class ConfigService:
    """
    Singleton service that manages both JSON and CFG configurations.
    Provides centralized access to application settings.
    """
    _instance = None
    _json_config = None
    _cfg_config = None

    @classmethod
    def get_instance(cls):
        """
        Returns singleton instance of ConfigService.
        Must call initialize() before first use.

        Returns:
            ConfigService: Singleton instance

        Raises:
            RuntimeError: If called before initialize()
        """
        if cls._instance is None:
            raise RuntimeError("ConfigService not initialized. Call initialize() first")
        return cls._instance

    @classmethod
    def initialize(cls, json_file, cfg_file="src/config/config.cfg"):
        """
        Initialize the configuration service with both JSON and CFG files.
        Must be called before first get_instance().

        Args:
            json_file (str): Path to JSON configuration file
            cfg_file (str): Path to CFG configuration file, defaults to src/config/config.cfg

        Returns:
            ConfigService: Initialized singleton instance

        Raises:
            RuntimeError: If service is already initialized
            ConfigurationError: If JSON config is invalid or missing required sections
        """
        if cls._instance is not None:
            raise RuntimeError("ConfigService already initialized")

        cls._instance = cls()
        cls._instance._load_configs(json_file, cfg_file)
        return cls._instance

    def _load_configs(self, json_file, cfg_file):
        """
        Load both configuration file types.
        Loads CFG first, then JSON configuration.

        Args:
            json_file (str): Path to JSON configuration file
            cfg_file (str): Path to CFG configuration file
        """
        self._load_cfg_config(cfg_file)  # First load CFG
        self._load_json_config(json_file)  # Then load JSON

    def _load_json_config(self, json_file):
        """
        Load and validate JSON configuration.

        Args:
            json_file (str): Path to JSON configuration file

        Raises:
            ConfigurationError: If file not found, invalid JSON, or missing required sections
        """
        if not os.path.exists(json_file):
            raise ConfigurationError(f"JSON config file not found: {json_file}")

        try:
            config_data = get_json(json_file)
            if not isinstance(config_data, dict):
                raise ConfigurationError("Configuration must be a JSON object")

            if "styles" not in config_data:
                raise ConfigurationError("Missing required 'styles' section")
            if "common" not in config_data:
                raise ConfigurationError("Missing required 'common' section")

            self._json_config = config_data

        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON syntax: {str(e)}")
        except Exception as e:
            raise ConfigurationError(f"Error loading JSON configuration: {str(e)}")

    def _load_cfg_config(self, cfg_file):
        """
        Load CFG configuration file.
        Logs error but does not raise exception if file not found.

        Args:
            cfg_file (str): Path to CFG configuration file
        """
        if not os.path.exists(cfg_file):
            python_logger.error(f"CFG file not found: {cfg_file}")
            return

        config = configparser.ConfigParser()
        config.read(cfg_file)
        self._cfg_config = config

    def get_config(self, key=None):
        """
        Get value from JSON configuration.
        Supports dot notation for nested access (e.g. 'common.padding.vertical')

        Args:
            key: String key with optional dot notation, or None for full config

        Returns:
            Config value if found, None if not found
        """
        if key is None:
            return self._json_config

        # Handle dot notation
        current = self._json_config
        for part in key.split('.'):
            if isinstance(current, dict):
                current = current.get(part)
                if current is None:
                    return None
            else:
                return None

        return current

    def get_cfg(self, section, key, fallback=None):
        """
        Get value from CFG configuration.

        Args:
            section (str): Configuration section name
            key (str): Key within section
            fallback: Default value if section/key not found

        Returns:
            Value from config or fallback if not found
        """
        if self._cfg_config is None:
            return fallback

        try:
            return self._cfg_config.get(section, key, fallback=fallback)
        except Exception as e:
            python_logger.error(f"Error reading config {section}.{key}: {e}")
            return fallback