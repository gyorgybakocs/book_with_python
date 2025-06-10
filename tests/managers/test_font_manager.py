import pytest
from unittest.mock import MagicMock, patch
from src.services.config_service import ConfigService
from src.managers.font_manager import FontManager

@pytest.fixture(autouse=True)
def mock_config_service(mocker):
    """
    This fixture automatically mocks the ConfigService for every test in this file.
    """
    mock_instance = MagicMock()
    config_values = {
        "paths.font_path": "/mock/fonts",
        "fonts.main": "TestMainFont",
        "fonts.ipa": "TestIPAFont",
    }
    mock_instance.get.side_effect = lambda key, fallback=None: config_values.get(key, fallback)
    mocker.patch.object(ConfigService, "_instance", mock_instance)

def test_font_manager_initialization():
    """
    Tests if the FontManager correctly initializes its attributes
    from the mocked configuration.
    """
    font_manager = FontManager()
    assert font_manager.font_path == "/mock/fonts"
    assert font_manager.default_font == "TestMainFont"
    assert font_manager.ipa_font == "TestIPAFont"

@patch("os.path.exists", return_value=True)
@patch("src.managers.font_manager.TTFont")
@patch("reportlab.pdfbase.pdfmetrics.registerFont")
@patch("reportlab.pdfbase.pdfmetrics.registerFontFamily")
def test_register_all_fonts_success(mock_register_family, mock_register_font, mock_ttfont, mock_exists):
    """
    Tests the successful registration of all fonts when the font files exist.
    """
    font_manager = FontManager()
    result = font_manager.register_all_fonts()

    assert result is True
    assert mock_register_font.call_count == 5
    assert mock_register_family.call_count == 2

@patch("os.path.exists", return_value=False)
@patch("src.managers.font_manager.logger.error")
def test_register_all_fonts_failure_if_file_missing(mock_logger_error, mock_exists):
    """
    Tests that font registration fails and logs an error if a font file is missing.
    """
    font_manager = FontManager()
    result = font_manager.register_all_fonts()

    assert result is False
    mock_logger_error.assert_called_once()
    assert "Missing font file: /mock/fonts/TestIPAFont-Regular.ttf" in mock_logger_error.call_args[0][0]

@patch("os.path.exists")
@patch("src.managers.font_manager.TTFont")
@patch("src.managers.font_manager.logger.error")
def test_register_all_fonts_main_font_fails(mock_logger_error, mock_ttfont, mock_exists):
    """
    Tests the case where the IPA font succeeds but the main font registration fails.
    """
    mock_exists.side_effect = [True, False]

    font_manager = FontManager()
    result = font_manager.register_all_fonts()

    assert result is False
    mock_logger_error.assert_called_once()
    assert "TestMainFont-Regular.ttf" in mock_logger_error.call_args[0][0]

@patch("os.path.exists", return_value=True)
@patch("src.managers.font_manager.TTFont", side_effect=IOError("Simulated TTF file read error"))
@patch("src.managers.font_manager.logger.error")
def test_register_font_family_handles_general_exception(mock_logger_error, mock_ttfont, mock_exists):
    """
    Tests the general except block in _register_font_family.
    """
    font_manager = FontManager()
    result = font_manager.register_all_fonts()

    assert result is False
    mock_logger_error.assert_called_once()
    log_message = mock_logger_error.call_args[0][0]
    assert "Error registering font family 'TestIPAFont'" in log_message
    assert "Simulated TTF file read error" in log_message
