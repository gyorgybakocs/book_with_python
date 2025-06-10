import os
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from src.logger import logger
from src.services.config_service import ConfigService

class FontManager:
    def __init__(self):
        """Initializes the FontManager."""
        self.config = ConfigService.get_instance()
        self.font_path = self.config.get("paths.font_path")
        self.default_font = self.config.get("fonts.main")
        self.ipa_font = self.config.get("fonts.ipa")

    def register_all_fonts(self):
        """
        Registers all required fonts for the document by looking them up in the font_path.
        Returns True only if all fonts were successfully registered.
        """
        ipa_font_types = {'normal': 'Regular'}
        if not self._register_font_family(self.ipa_font, ipa_font_types):
            return False # FIX: Early exit on failure

        main_font_types = {
            'normal': 'Regular',
            'bold': 'Bold',
            'italic': 'Italic',
            'boldItalic': 'BoldItalic'
        }
        if not self._register_font_family(self.default_font, main_font_types):
            return False # FIX: Early exit on failure

        return True

    def _register_font_family(self, font_name: str, font_types: dict) -> bool:
        """
        Private helper to register a font family and its variations (e.g., bold, italic).
        """
        font_variants = {}
        for font_type in font_types.values():
            font_file_path = os.path.join(self.font_path, f"{font_name}-{font_type}.ttf")
            if not os.path.exists(font_file_path):
                logger.error(f"Missing font file: {font_file_path}")
                return False

        try:
            for style_key, style_name in font_types.items():
                font_file = os.path.join(self.font_path, f"{font_name}-{style_name}.ttf")
                registered_font_name = f"{font_name}-{style_name}"
                pdfmetrics.registerFont(TTFont(registered_font_name, font_file))
                font_variants[style_key] = registered_font_name

            pdfmetrics.registerFontFamily(font_name, **font_variants)
            logger.info(f"Successfully registered font family: {font_name}")
            return True
        except Exception as e:
            logger.error(f"Error registering font family '{font_name}': {e}")
            return False
