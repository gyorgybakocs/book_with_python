import abc
from reportlab.lib.pagesizes import letter, A4, legal
from src.logger import logger
from src.managers.data_manager import DataManager
from src.managers.font_manager import FontManager
from src.managers.style_manager import StyleManager
from src.services.config_service import ConfigService

class BaseBuilder(metaclass=abc.ABCMeta):
    def __init__(self, json_file: str, **kwargs):
        """
        Initializes the base builder. It sets up all necessary managers and 
        configurations required for the building process.

        Args:
            json_file (str): The path to the JSON file containing the book data.
            **kwargs: Additional keyword arguments for builder-specific settings 
                      (e.g., paper_book, language).
        """
        self.config = ConfigService.get_instance()
        self.valid = True

        self.font_manager = FontManager()
        if not self.font_manager.register_all_fonts():
            logger.error("FontManager registration failed. Builder is invalid.")
            self.valid = False
            return

        self.style_manager = StyleManager()
        if not self.style_manager.register_styles():
            logger.error("StyleManager registration failed. Builder is invalid.")
            self.valid = False
            return

        self.data_manager = DataManager()
        if not self.data_manager.load_book_data(json_file):
            logger.error(f"DataManager failed to load data from {json_file}. Builder is invalid.")
            self.valid = False
            return

        self.paper_book = kwargs.get("paper_book", False)
        self.black_and_white = kwargs.get("black_and_white", False)
        self.short = kwargs.get("short", False)
        self.epub_type = kwargs.get("epub_type", None)

        self.language = kwargs.get("language", self.config.get("defaults.language"))

        page_size_map = {
            'letter': letter,
            'a4': A4,
            'legal': legal
        }
        page_size_str = self.config.get("defaults.page_size", fallback="letter").lower()
        self.PAGESIZE = page_size_map.get(page_size_str, letter)

        logger.info(f"BaseBuilder initialized successfully for language: {self.language}")

    @abc.abstractmethod
    def run(self):
        """
        Abstract method that must be implemented by subclasses (e.g., PdfBuilder, EpubBuilder).
        This method contains the core logic for building the document.
        """
        pass
