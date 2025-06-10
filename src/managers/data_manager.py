from src.logger import logger
from src.services.config_service import ConfigService
from src.utils.json_utils import get_json_to_data
from pydantic import ValidationError
from src.schemas import BookData


class DataManager:
    def __init__(self):
        # Get config instance
        self.config = ConfigService.get_instance()
        self.data = {}
        self.default_language = self.config.get("defaults", "language")

    def load_book_data(self, json_file):
        """
        Loads and validates book data from JSON using Pydantic.

        Args:
            json_file: Path to the JSON file
        Returns:
            bool: True if data loading and validation was successful
        """
        try:
            raw_data = get_json_to_data(json_file)
            if not raw_data:
                logger.error("JSON loading failed!")
                return False

            self.data = BookData(**raw_data)
            logger.info("Book data loaded and validated successfully")
            return True

        except ValidationError as e:
            logger.error(f"Data validation failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to load book data: {e}")
            return False

    def get_data(self, language=None, node=None):
        lang = language or self.default_language
        book_key = f'book_{lang}'

        if book_key not in self.data.dict():
            logger.warning(f"No data for language {lang}, falling back to {self.default_language}")
            book_key = f'book_{self.default_language}'

        data = self.data.dict().get(book_key, {})

        if node is None:
            return data

        try:
            for key in node.split('.'):
                data = data[key]
            return data
        except (KeyError, AttributeError):
            logger.warning(f"Node path '{node}' not found in {book_key}")
            return {}
