import abc
import json
import os
from reportlab.lib.pagesizes import letter, A4, legal
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import TableStyle
from reportlab.lib import colors

from src.config.config_service import ConfigService
from src.helpers.builder import register_fonts
from reportlab.platypus.paragraph import Paragraph
from src.utils.json_utils import get_json
from src.logger import logger


def get_json_to_data(json_file):
    """
    Loads the JSON data dynamically and handles errors.
    """
    if not os.path.exists(json_file):
        logger.error(f"JSON file not found: {json_file}")
        return {}

    try:
        json_data = get_json(json_file)

        if not isinstance(json_data, dict):
            logger.error(f"Invalid JSON format: {json_file}")
            return {}

        # Build the data dictionary dynamically
        data = {key: value for key, value in json_data.items() if isinstance(value, dict)}

        # Ensure styles are present if available
        if "styles" in json_data and isinstance(json_data["styles"], dict):
            data["styles"] = json_data["styles"]

        logger.info(f"Successfully loaded JSON: {json_file}")
        return data

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON syntax in {json_file}: {e}")
    except FileNotFoundError:
        logger.error(f"File not found: {json_file}")
    except Exception as e:
        logger.error(f"Unexpected error while loading JSON ({json_file}): {e}")

    return {}  # If there's an error, return an empty dictionary


class BaseBuilder(metaclass=abc.ABCMeta):
    def __init__(self, json_file, **kwargs):
        """
        :param json_file: Path to the JSON file.
        """
        # Get config instance
        self.config = ConfigService.get_instance()

        # Get paths from CFG
        self.resources_path = self.config.get_cfg("paths", "resources")
        self.font_path = self.config.get_cfg("fonts", "font_path")
        self.output_dir = self.config.get_cfg("paths", "output_dir")

        # Get font settings from CFG
        self.font = self.config.get_cfg("fonts", "default_font")
        self.ipa = self.config.get_cfg("fonts", "ipa_font")
        # Register fonts with path from CFG
        self.register_fonts(self.font_path)

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

        try:
            self.json_file = json_file
            self.data = get_json_to_data(json_file)
            if not self.data:
                logger.error("JSON loading failed!")
                self.valid = False

        except Exception as e:
            logger.error(f"Failed to load JSON: {e}")
            self.valid = False

        # Register fonts and check if ALL were successful
        if not self.register_fonts('/resources/fonts'):
            logger.error("Font registration failed!")
            self.valid = False

        # Register styles
        self.register_styles()

        #checking styles
        styles = self.get_registered_styles()
        for name, properties in styles.items():
            print(f"Style: {name}")
            for prop, value in properties.items():
                print(f"  {prop}: {value}")

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

    def register_fonts(self, path):
        """
        Registers all required fonts dynamically.
        """
        font_types = {'normal': 'Regular'}  # Start with IPA font types
        ipa_success = register_fonts(self.ipa, font_types, path)  # Register IPA fonts

        font_types.update({
            'bold': 'Bold',
            'italic': 'Italic',
            'boldItalic': 'BoldItalic'
        })
        main_font_success = register_fonts(self.font, font_types, path)  # Register main fonts

        return ipa_success and main_font_success  # 🔥 MUST be True for BOTH!

    def register_styles(self):
        """
        Dynamically registers paragraph styles from config.
        Creates a class attribute for each style defined in the config.
        """
        try:
            # Iterate through all styles in config
            for style_name, style_props in self.config.get_config("styles").items():
                try:
                    # Create ParagraphStyle instance
                    style = ParagraphStyle(
                        style_name,
                        fontName=f'{self.font}-{style_props.get("font_weight", "Regular")}',
                        fontSize=style_props.get("font_size", 12),
                        leading=style_props.get("leading", 16)
                    )

                    # Add alignment if specified
                    if "alignment" in style_props:
                        style.alignment = style_props["alignment"]

                    # Dynamically set class attribute for the style
                    setattr(self, style_name, style)

                except Exception as e:
                    logger.error(f"Failed to create style {style_name}: {e}")
                    self.valid = False

        except Exception as e:
            logger.error(f"Style registration failed: {e}")
            self.valid = False

    def get_registered_styles(self):
        """
        Lists all registered paragraph styles.

        Returns:
            dict: Dictionary of style names and their properties
        """
        registered_styles = {}

        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if isinstance(attr, ParagraphStyle):
                registered_styles[attr_name] = {
                    "font_name": attr.fontName,
                    "font_size": attr.fontSize,
                    "leading": attr.leading
                }
                if hasattr(attr, 'alignment'):
                    registered_styles[attr_name]["alignment"] = attr.alignment

        return registered_styles

    def make_paragraph(self, pos, text, style, extra_spacing=0, extra_width=0):
        paragraph = Paragraph(text, style)
        width, height = paragraph.wrapOn(self.canvas, self.PAGESIZE[0] - 2 * self.padding_h - extra_width, 20)
        pos += height + extra_spacing
        paragraph.drawOn(self.canvas, self.padding_h + extra_width, self.PAGESIZE[1] - pos)
        return pos
