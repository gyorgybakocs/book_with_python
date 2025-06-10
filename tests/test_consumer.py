import pytest
from unittest.mock import patch, MagicMock
from src import consumer

@pytest.fixture(autouse=True)
def mock_services(mocker):
    """
    Mocks all external services that consumer.py depends on.
    This fixture runs automatically for every test in this file.
    """
    mocker.patch('src.consumer.ConfigService.initialize')
    mocker.patch('src.consumer.ConfigService.get_instance')
    mocker.patch('src.consumer.LoggerService.get_instance')

    mock_pdf_builder = mocker.patch('src.consumer.PdfBuilder')
    mock_epub_builder = mocker.patch('src.consumer.EpubBuilder')

    mock_pdf_instance = MagicMock()
    mock_pdf_instance.valid = True
    mock_pdf_builder.return_value = mock_pdf_instance

    mock_epub_instance = MagicMock()
    mock_epub_instance.valid = True
    mock_epub_builder.return_value = mock_epub_instance

@pytest.mark.parametrize(
    "pb_arg, bw_arg, s_arg, expected_paper_book, expected_bw, expected_short",
    [
        ("1", "0", "0", True, False, False),
        ("1", "1", "0", True, True, False),
        ("1", "1", "1", False, False, True),
        ("0", "0", "0", False, False, False),
    ]
)
def test_pdf_builder_called_with_various_args(mocker, pb_arg, bw_arg, s_arg, expected_paper_book, expected_bw, expected_short):
    """
    Tests if the main function correctly parses various PDF-related arguments
    and calls the PdfBuilder with the expected boolean parameters.
    """
    test_args = [
        'consumer.py', '--format', 'pdf', '--data', 'data.json', '--config', 'config.yml',
        '--pb', pb_arg, '--bw', bw_arg, '--s', s_arg, '--l', 'hu'
    ]
    mocker.patch('sys.argv', test_args)
    consumer.main()
    consumer.PdfBuilder.assert_called_with(
        json_file='data.json',
        paper_book=expected_paper_book,
        black_and_white=expected_bw,
        short=expected_short,
        language='hu'
    )
    consumer.PdfBuilder.return_value.run.assert_called_once()

@pytest.mark.parametrize("missing_arg", ["--pb", "--bw", "--s", "--l"])
def test_missing_pdf_args_raises_error(mocker, missing_arg):
    """
    Tests if the script exits with an error if any of the required PDF arguments are missing.
    """
    base_args = [
        'consumer.py', '--format', 'pdf', '--data', 'data.json',
        '--config', 'config.yml', '--pb', '1', '--bw', '0', '--s', '0', '--l', 'hu'
    ]
    index_to_remove = base_args.index(missing_arg)
    test_args = base_args[:index_to_remove] + base_args[index_to_remove+2:]

    mocker.patch('sys.argv', test_args)
    with pytest.raises(SystemExit):
        consumer.main()

@pytest.mark.parametrize("epub_type", ["kindle", "epub", "web"])
def test_epub_builder_called_with_correct_args(mocker, epub_type):
    """
    Tests if the main function correctly calls the EpubBuilder for various epub types.
    """
    test_args = [
        'consumer.py', '--format', 'epub', '--data', 'data.json',
        '--config', 'config.yml', '--et', epub_type
    ]
    mocker.patch('sys.argv', test_args)
    consumer.main()
    consumer.EpubBuilder.assert_called_with(
        json_file='data.json', epub_type=epub_type
    )
    consumer.EpubBuilder.return_value.run.assert_called_once()

def test_missing_epub_args_raises_error(mocker):
    """
    Tests if the script exits with an error if the required EPUB argument is missing.
    """
    test_args = [
        'consumer.py', '--format', 'epub', '--data', 'data.json',
        '--config', 'config.yml'
    ] # Missing --et
    mocker.patch('sys.argv', test_args)
    with pytest.raises(SystemExit):
        consumer.main()

def test_startup_exception_is_caught(mocker):
    """
    Tests that a generic exception during service initialization is caught
    and the program exits gracefully.
    """
    test_args = [
        'consumer.py', '--format', 'pdf', '--data', 'data.json',
        '--config', 'config.yml', '--pb', '1', '--bw', '0', '--s', '0', '--l', 'hu'
    ]
    mocker.patch('sys.argv', test_args)
    mocker.patch('src.consumer.ConfigService.initialize', side_effect=Exception("Failed to load"))
    consumer.main()
    consumer.PdfBuilder.assert_not_called()
