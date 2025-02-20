from src.logger import logger
from src.services.config_service import ConfigService
from src.utils.json_utils import get_json_to_data


class DataManager:
    def __init__(self):
        # Get config instance
        self.config = ConfigService.get_instance()
        self.data = {}
        self.default_language = self.config.get_cfg("defaults", "language")

    def load_book_data(self, json_file):
        """
        Loads and validates book data from JSON.

        Args:
            json_file: Path to the JSON file
        Returns:
            bool: True if data loading was successful
        """
        try:
            self.data = get_json_to_data(json_file)
            if not self.data:
                logger.error("JSON loading failed!")
                return False

            # Validate required data structure
            if not self._validate_book_data():
                return False

            logger.info("Book data loaded successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to load book data: {e}")
            return False

    def _validate_book_data(self):
        """
        Validates the loaded book data structure.
        Returns:
            bool: True if data structure is valid
        """
        try:
            # Check if we have book data for at least the default language
            default_book_key = f'book_{self.default_language}'
            if default_book_key not in self.data:
                logger.error(f"Missing default language book data ({default_book_key})")
                return False

            # Validate basic book structure
            book_data = self.data[default_book_key]['title']
            required_fields = ['title', 'subtitle']

            for field in required_fields:
                if field not in book_data:
                    logger.error(f"Missing required field: {field}")
                    return False

            return True

        except Exception as e:
            logger.error(f"Data validation failed: {e}")
            return False

    # def get_data(self, language=None, node=None):
    #     """
    #     Gets book data for specified language.
    #
    #     Args:
    #         language: Language code, uses default if None
    #         node:
    #     Returns:
    #         dict: Book data for the specified language
    #     """
    #     lang = language or self.default_language
    #     book_key = f'book_{lang}'
    #
    #     if book_key not in self.data:
    #         logger.warning(f"No data for language {lang}, falling back to {self.default_language}")
    #         book_key = f'book_{self.default_language}'
    #
    #     if node is not None:
    #         return self.data.get(book_key, {}).get(node, {})
    #     else:
    #         return self.data.get(book_key, {})

    def get_data(self, language=None, node=None):
        """
        Gets book data for specified language.

        Args:
            language: Language code, uses default if None
            node: String with dot notation for nested access (e.g. 'node1.node2')
        Returns:
            dict: Book data for the specified language and node path
        """
        lang = language or self.default_language
        book_key = f'book_{lang}'

        if book_key not in self.data:
            logger.warning(f"No data for language {lang}, falling back to {self.default_language}")
            book_key = f'book_{self.default_language}'

        # Get base book data
        data = self.data.get(book_key, {})

        # If no node specified, return all book data
        if node is None:
            return data

        # Navigate through dot notation
        try:
            for key in node.split('.'):
                data = data[key]
            return data
        except (KeyError, AttributeError):
            logger.warning(f"Node path '{node}' not found in {book_key}")
            return {}
