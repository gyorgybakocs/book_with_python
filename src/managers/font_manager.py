import os

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from src.logger import logger
from src.services.config_service import ConfigService


class FontManager:
    def __init__(self):
        # Get config instance
        self.config = ConfigService.get_instance()
        self.font_path = self.config.get_cfg("fonts", "font_path")
        self.default_font = self.config.get_cfg("fonts", "default_font")
        self.ipa_font = self.config.get_cfg("fonts", "ipa_font")

    def register_all_fonts(self):
        """
        Registers all required fonts for the document.
        Returns True only if all fonts were successfully registered.
        """
        # Start with IPA font types
        font_types = {'normal': 'Regular'}
        ipa_success = self._register_font_family(self.ipa_font, font_types)

        # Update font types for main font
        font_types.update({
            'bold': 'Bold',
            'italic': 'Italic',
            'boldItalic': 'BoldItalic'
        })
        main_font_success = self._register_font_family(self.default_font, font_types)

        return ipa_success and main_font_success

    def _register_font_family(self, font, font_types):
        """
        Registers a font and its variations.

        Args:
            font: The base font name (e.g., 'Arial')
            font_types: Dictionary of font variations (e.g., {'normal': 'Regular', 'bold': 'Bold'})
        Returns:
            bool: True if ALL fonts were registered successfully, False otherwise
        """
        font_variants = {}
        required_fonts = [f"{self.font_path}/{font}-{font_type}.ttf"
                          for font_type in font_types.values()]

        # Check if all required fonts exist
        missing_fonts = [f for f in required_fonts if not os.path.exists(f)]
        if missing_fonts:
            logger.error(f"Missing fonts: {', '.join(missing_fonts)}")
            return False

        # Register each font variant
        try:
            for font_type_key, font_type in font_types.items():
                font_file = f"{self.font_path}/{font}-{font_type}.ttf"
                font_name = f"{font}-{font_type}"
                pdfmetrics.registerFont(TTFont(font_name, font_file))
                font_variants[font_type_key] = font_name

            pdfmetrics.registerFontFamily(font, **font_variants)
            logger.info(f"Successfully registered font family: {font}")
            return True

        except Exception as e:
            logger.error(f"Error registering font family {font}: {str(e)}")
            return False

    def get_font_name(self, base_font, style="Regular"):
        """
        Gets the full font name for a given style.

        Args:
            base_font: The base font name (default_font or ipa_font)
            style: The font style (Regular, Bold, Italic, BoldItalic)
        Returns:
            str: The complete font name
        """
        return f"{base_font}-{style}"
