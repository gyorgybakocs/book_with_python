import pytest
from pydantic import ValidationError
from src.schemas import BookData
from tests.mocked_data.mocked_data import valid_json_data


@pytest.fixture
def valid_book_data():
    return valid_json_data

def deep_del(data: dict, key_path: str):
    keys = key_path.split('.')
    d = data
    for key in keys[:-1]:
        d = d[key]
    del d[keys[-1]]

def test_book_data_with_valid_data(valid_book_data):
    book_data = BookData(**valid_book_data)
    assert book_data.book_hu.title.title == "Cím"
    assert book_data.book_en.chapters["ch1"].title == "Chapter 1"

@pytest.mark.parametrize("field_to_remove, expected_error", [
    ("book_hu.title.title", "Field required"),
    ("book_hu.copyright.author", "Field required"),
])
def test_book_data_with_missing_required_field(valid_book_data, field_to_remove, expected_error):
    invalid_data = valid_book_data
    deep_del(invalid_data, field_to_remove)
    with pytest.raises(ValidationError) as excinfo:
        BookData(**invalid_data)

    assert field_to_remove in str(excinfo.value)
    assert expected_error in str(excinfo.value)
