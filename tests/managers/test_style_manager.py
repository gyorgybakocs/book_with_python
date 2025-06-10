import pytest
from unittest.mock import MagicMock, patch
from reportlab.lib.styles import ParagraphStyle

from src.services.config_service import ConfigService
from src.managers.style_manager import StyleManager

@pytest.fixture
def mock_config_service(mocker):
    """
    This fixture creates a flexible mock for the ConfigService instance.
    It returns different values based on the key requested.
    """
    mock_instance = MagicMock()

    config_values = {
        "fonts.main": "TestStyleFont",
        "styles": {
            "test_style_default": {
                "font_weight": "Regular",
                "font_size": 12,
                "leading": 16
            },
            "test_style_bold": {
                "font_weight": "Bold",
                "font_size": 18,
                "leading": 22,
                "alignment": 1
            }
        }
    }

    def config_side_effect(key, fallback=None):
        return config_values.get(key, fallback)

    mock_instance.get.side_effect = config_side_effect

    mocker.patch.object(ConfigService, "_instance", mock_instance)
    return mock_instance

def test_style_manager_initialization(mock_config_service):
    style_manager = StyleManager()
    assert style_manager.font == "TestStyleFont"

def test_register_styles_success(mock_config_service):
    style_manager = StyleManager()
    result = style_manager.register_styles()
    assert result is True
    assert len(style_manager.styles) == 2
    bold_style = style_manager.get_style("test_style_bold")
    assert isinstance(bold_style, ParagraphStyle)
    assert bold_style.fontName == "TestStyleFont-Bold"

def test_prepare_style_modification(mock_config_service):
    style_manager = StyleManager()
    style_manager.register_styles()
    original_style = style_manager.get_style("test_style_default")
    modified_style = style_manager.prepare_style("test_style_default", leftIndent=20)
    assert modified_style is not original_style
    assert modified_style.leftIndent == 20
    assert original_style.leftIndent == 0

def test_prepare_style_returns_original_if_no_args(mock_config_service):
    style_manager = StyleManager()
    style_manager.register_styles()
    original_style = style_manager.get_style("test_style_default")
    returned_style = style_manager.prepare_style("test_style_default")
    assert returned_style is original_style

@patch("src.managers.style_manager.logger.warning")
def test_prepare_style_with_invalid_attribute(mock_logger_warning, mock_config_service):
    style_manager = StyleManager()
    style_manager.register_styles()
    style_manager.prepare_style("test_style_default", non_existent_attr="foo")
    mock_logger_warning.assert_called_once_with(
        "'non_existent_attr' is not a valid attribute for ParagraphStyle."
    )

@patch("src.managers.style_manager.logger.error")
def test_register_styles_handles_error_in_style_props(mock_logger_error, mock_config_service):
    """
    Tests the inner try-except block in register_styles.
    This simulates an error during the creation of a single ParagraphStyle.
    """
    def new_side_effect(key, fallback=None):
        if key == "styles":
            return {
                "valid_style": {"font_size": 12},
                "invalid_style": "this is not a dict"
            }
        return "TestStyleFont"

    mock_config_service.get.side_effect = new_side_effect

    style_manager = StyleManager()
    result = style_manager.register_styles()

    assert result is False
    mock_logger_error.assert_called_once()
    assert "Failed to create style 'invalid_style'" in mock_logger_error.call_args[0][0]

@patch("src.managers.style_manager.logger.error")
def test_register_styles_handles_main_exception(mock_logger_error, mock_config_service):
    """
    Tests the outer try-except block in register_styles.
    This simulates a failure in getting the styles dictionary itself.
    """
    def new_side_effect(key, fallback=None):
        if key == "styles":
            raise TypeError("Simulated config error")
        return "TestStyleFont"

    mock_config_service.get.side_effect = new_side_effect

    style_manager = StyleManager()
    result = style_manager.register_styles()

    assert result is False
    mock_logger_error.assert_called_once()
    assert "Style registration failed" in mock_logger_error.call_args[0][0]