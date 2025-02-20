from copy import deepcopy

from reportlab.lib.styles import ParagraphStyle

from src.logger import logger
from src.services.config_service import ConfigService


def modify_paragraph_style(style, **kwargs):
    """
    Creates a modified copy of an existing paragraph style with new attributes.

    Args:
        style: The original ParagraphStyle object to copy.
        kwargs: The attributes to override (e.g., fontSize=16, alignment=1).
    Returns:
        A new ParagraphStyle object with the modified attributes.
    """
    new_style = deepcopy(style)

    for key, value in kwargs.items():
        if hasattr(new_style, key):
            setattr(new_style, key, value)
        else:
            logger.warning(f"'{key}' is not a valid attribute for ParagraphStyle.")

    return new_style


class StyleManager:
    def __init__(self):
        # Get config instance
        self.config = ConfigService.get_instance()
        self.styles = {}

        # Get font names from config
        self.font = self.config.get_cfg("fonts", "default_font")
        self.ipa = self.config.get_cfg("fonts", "ipa_font")

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

                    # Store the style in our styles dictionary
                    self.styles[style_name] = style

                except Exception as e:
                    logger.error(f"Failed to create style {style_name}: {e}")
                    return False

            logger.info("Successfully registered all styles")
            return True

        except Exception as e:
            logger.error(f"Style registration failed: {e}")
            return False

    def get_style(self, style_name):
        """
        Returns a registered style by name.

        Args:
            style_name: Name of the style to retrieve
        Returns:
            ParagraphStyle or None if not found
        """
        return self.styles.get(style_name)

    def get_registered_styles(self):
        """
        Lists all registered paragraph styles.

        Returns:
            dict: Dictionary of style names and their properties
        """
        registered_styles = {}

        for name, style in self.styles.items():
            registered_styles[name] = {
                "font_name": style.fontName,
                "font_size": style.fontSize,
                "leading": style.leading
            }
            if hasattr(style, 'alignment'):
                registered_styles[name]["alignment"] = style.alignment

        return registered_styles
