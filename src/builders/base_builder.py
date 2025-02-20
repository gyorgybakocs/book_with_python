import abc
import json
import os

from reportlab.lib.pagesizes import letter, A4, legal

from src.logger import logger
from src.managers.data_manager import DataManager
from src.managers.font_manager import FontManager
from src.managers.style_manager import StyleManager
from src.services.config_service import ConfigService
from src.utils.json_utils import get_json, get_json_to_data


class BaseBuilder(metaclass=abc.ABCMeta):
    def __init__(self, json_file, **kwargs):
        """
        :param json_file: Path to the JSON file.
        """
        # Get config instance
        self.config = ConfigService.get_instance()
        # Register fonts
        self.font_manager = FontManager()
        if not self.font_manager.register_all_fonts():
            logger.error("Font registration failed!")
            self.valid = False
        # Register styles
        self.style_manager = StyleManager()
        self.style_manager.register_styles()
        # checking styles
        # styles = self.style_manager.get_registered_styles()
        # for name, properties in styles.items():
        #     print(f"Style: {name}")
        #     for prop, value in properties.items():
        #         print(f"  {prop}: {value}")
        self.data_manager = DataManager()
        # Load and validate data
        if not self.data_manager.load_book_data(json_file):
            logger.error("Data loading failed!")
            self.valid = False

        # Get paths from CFG
        self.resources_path = self.config.get_cfg("paths", "resources")
        self.font_path = self.config.get_cfg("fonts", "font_path")
        self.output_dir = self.config.get_cfg("paths", "output_dir")

        # Get font settings from CFG
        self.font = self.config.get_cfg("fonts", "default_font")
        self.ipa = self.config.get_cfg("fonts", "ipa_font")

        # Get default values from CFG
        self.starting_pos = float(self.config.get_cfg("defaults", "starting_pos"))
        self.default_language = self.config.get_cfg("defaults", "language")

        # Get style-related values from JSON config
        self.padding_v = self.config.get_config("common.padding.vertical")
        self.padding_h = self.config.get_config("common.padding.horizontal")

        # Initialize other attributes
        self.paragraph_default = None
        self.title_sub = None
        self.title_main = None
        self.canvas = None
        self.page_num = 0
        self.valid = True

        # Map page size string to ReportLab constant
        page_size_map = {
            'letter': letter,
            'a4': A4,
            'legal': legal
        }
        # Get page size from CFG, default to letter if not found or invalid
        cfg_page_size = self.config.get_cfg("defaults", "page_size", "letter").lower()

        self.PAGESIZE = page_size_map.get(cfg_page_size, letter)

        self.valid = True  # Default: initialization is successful

        # PDF-specific properties (using CFG default language if not specified)
        self.paper_book = kwargs.get("paper_book", False)
        self.black_and_white = kwargs.get("black_and_white", False)
        self.short = kwargs.get("short", False)
        self.language = kwargs.get("language", self.default_language)

        # EPUB-specific properties
        self.epub_type = kwargs.get("epub_type", None)

        logger.info(f"Successfully Initialized the builder!")

    @abc.abstractmethod
    def run(self):
        """Abstract method that must be implemented by subclasses."""
        pass
