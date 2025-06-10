import pytest
from src.managers.data_manager import DataManager
from tests.mocked_data.mocked_data import valid_json_data

@pytest.fixture
def loaded_data_manager(mocker):
    """
    This fixture provides a fully initialized DataManager instance with mocked data.
    """
    mocker.patch(
        'src.services.config_service.ConfigService.get_instance'
    ).return_value.get_cfg.return_value = 'en'
    mocker.patch('src.managers.data_manager.get_json_to_data', return_value=valid_json_data)
    data_manager = DataManager()
    data_manager.load_book_data('any_dummy_path')
    return data_manager

def test_load_book_data_successfully(loaded_data_manager):
    """
    Tests that data loading is successful with valid mocked data.
    """
    assert loaded_data_manager.data is not None
    assert loaded_data_manager.get_data(language='hu', node='title.title') == "Cím"

def test_load_book_data_validation_error(mocker):
    """
    Tests that load_book_data returns False when validation fails.
    """
    mocker.patch('src.services.config_service.ConfigService.get_instance').return_value.get_cfg.return_value = 'en'
    invalid_data = {"book_en": {"title": {"title": "Missing subtitle"}}}
    mocker.patch('src.managers.data_manager.get_json_to_data', return_value=invalid_data)

    data_manager = DataManager()
    assert data_manager.load_book_data('dummy_path') is False

def test_get_data_with_specific_language(loaded_data_manager):
    hungarian_book = loaded_data_manager.get_data(language='hu')
    assert hungarian_book['title']['title'] == "Cím"

def test_get_data_with_default_language(loaded_data_manager):
    default_book = loaded_data_manager.get_data()
    assert default_book['title']['title'] == "Title"

def test_get_data_with_node(loaded_data_manager):
    subtitle = loaded_data_manager.get_data(language='hu', node='title.subtitle')
    assert subtitle == "Alcím"

def test_get_data_fallback_to_default_language(loaded_data_manager, caplog):
    data = loaded_data_manager.get_data(language='de', node='title.title')
    assert data == "Title"
    assert "No data for language de, falling back to en" in caplog.text

def test_get_data_with_non_existent_node(loaded_data_manager, caplog):
    data = loaded_data_manager.get_data(language='hu', node='title.non_existent_key')
    assert data == {}
    assert "Node path 'title.non_existent_key' not found in book_hu" in caplog.text

def test_load_book_data_empty_json_returns_false(mocker):
    """
    Tests that load_book_data returns False if get_json_to_data returns an empty dict.
    This covers lines 26-27.
    """
    mocker.patch('src.services.config_service.ConfigService.get_instance').return_value.get_cfg.return_value = 'en'
    mocker.patch('src.managers.data_manager.get_json_to_data', return_value={})

    data_manager = DataManager()
    assert data_manager.load_book_data('dummy_path') is False

def test_load_book_data_generic_exception_returns_false(mocker):
    """
    Tests that load_book_data returns False on a generic Exception.
    This covers lines 38-39.
    """
    mocker.patch('src.services.config_service.ConfigService.get_instance').return_value.get_cfg.return_value = 'en'
    mocker.patch('src.managers.data_manager.get_json_to_data', side_effect=Exception("A generic error occurred"))

    data_manager = DataManager()
    assert data_manager.load_book_data('dummy_path') is False
