import pytest
from src.services.config_service import ConfigService
from src.exceptions.config_exceptions import ConfigurationError

VALID_CONFIG_PATH = "tests/mocked_data/valid_config.yml"
INVALID_CONFIG_PATH="tests/mocked_data/invalid_config.yml"
NON_EXISTENT_PATH ='tests/mocked_data/non_existing_config.yml'
@pytest.fixture(autouse=True)
def cleanup_singleton():
    """
    This fixture automatically runs before and after each test.
    It ensures that the ConfigService singleton instance is reset,
    so tests do not interfere with each other.
    """
    yield
    ConfigService._instance = None
    ConfigService._config = None

def test_initialize_and_get_value():
    """
    Tests successful initialization and retrieval of a nested value
    using a valid mock config file.
    """
    ConfigService.initialize(VALID_CONFIG_PATH)
    instance = ConfigService.get_instance()

    assert instance.get("paths.font_path") == "/test/fonts"
    assert instance.get("defaults.language") == "en"

def test_get_non_existent_key_returns_fallback():
    """
    Tests that the get method returns the fallback value for a key that does not exist.
    """
    ConfigService.initialize(VALID_CONFIG_PATH)
    instance = ConfigService.get_instance()

    assert instance.get("paths.non_existent_key") is None
    assert instance.get("defaults.another_key", fallback="default_value") == "default_value"

def test_initialize_with_non_existent_file_raises_error():
    """
    Tests that initializing with a path to a non-existent file raises a ConfigurationError.
    """
    with pytest.raises(ConfigurationError, match="Config file not found"):
        ConfigService.initialize(NON_EXISTENT_PATH)

def test_initialize_with_invalid_yaml_raises_error():
    """
    Tests that a malformed YAML file raises a ConfigurationError.
    """
    with pytest.raises(ConfigurationError, match="Error parsing YAML file"):
        ConfigService.initialize(INVALID_CONFIG_PATH)

def test_double_initialization_raises_error():
    """
    Tests that calling initialize() twice raises a RuntimeError.
    """
    ConfigService.initialize(VALID_CONFIG_PATH) # First call is OK
    with pytest.raises(RuntimeError, match="ConfigService already initialized"):
        ConfigService.initialize(VALID_CONFIG_PATH) # Second call should fail

def test_get_instance_before_initialize_raises_error():
    """
    Tests that calling get_instance() before initialize() raises a RuntimeError.
    """
    with pytest.raises(RuntimeError, match="ConfigService not initialized"):
        ConfigService.get_instance()
