from copy import deepcopy
from reportlab.lib.styles import ParagraphStyle
from src.logger import logger
from src.services.config_service import ConfigService

def modify_paragraph_style(style, **kwargs):
    """
    Creates a modified copy of an existing paragraph style with new attributes.
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
        """Initializes the StyleManager."""
        self.config = ConfigService.get_instance()
        self.styles = {}
        self.font = self.config.get("fonts.main")

    def register_styles(self):
        """
        Dynamically registers paragraph styles from the configuration file.
        """
        try:
            config_styles = self.config.get("styles", {})
            for style_name, style_props in config_styles.items():
                try:
                    font_weight = style_props.get("font_weight", "Regular")
                    style = ParagraphStyle(
                        name=style_name,
                        fontName=f'{self.font}-{font_weight}',
                        fontSize=style_props.get("font_size", 12),
                        leading=style_props.get("leading", 16)
                    )
                    if "alignment" in style_props:
                        style.alignment = style_props["alignment"]
                    self.styles[style_name] = style
                except Exception as e:
                    logger.error(f"Failed to create style '{style_name}': {e}")
                    return False
            logger.info("Successfully registered all styles")
            return True
        except Exception as e:
            logger.error(f"Style registration failed: {e}")
            return False

    def get_style(self, style_name: str) -> ParagraphStyle | None:
        """
        Returns a registered style by name.
        """
        return self.styles.get(style_name)

    def prepare_style(self, style_name: str, **kwargs) -> ParagraphStyle | None:
        """
        Gets a base style and applies modifications to it.
        """
        original_style = self.get_style(style_name)
        if not kwargs or not original_style:
            return original_style
        return modify_paragraph_style(original_style, **kwargs)
