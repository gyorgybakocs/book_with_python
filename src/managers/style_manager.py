from copy import deepcopy
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
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
        self.table_styles = {}
        self.font = self.config.get("fonts.main")

    def register_styles(self):
        """
        Dynamically registers paragraph styles and table styles from the configuration file.
        """
        success = True

        # Register paragraph styles
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
                    success = False
        except Exception as e:
            logger.error(f"Paragraph style registration failed: {e}")
            success = False

        # Register table styles
        try:
            self._register_table_styles()
        except Exception as e:
            logger.error(f"Table style registration failed: {e}")
            success = False

        if success:
            logger.info("Successfully registered all styles")
        return success

    def _register_table_styles(self):
        """Register predefined table styles."""

        # Default table style
        self.table_styles['default'] = [
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ]

        # Modern table style
        self.table_styles['modern'] = [
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('LINEBELOW', (0, 0), (-1, 0), 2, colors.HexColor('#4472C4')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F2F2F2')]),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]

        # Elegant table style
        self.table_styles['elegant'] = [
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2F4F4F')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor('#2F4F4F')),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]

        # Colorful table style
        self.table_styles['colorful'] = [
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#70AD47')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [
                colors.HexColor('#E2EFDA'),
                colors.HexColor('#C6E0B4')
            ]),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ]

        # Minimal table style
        self.table_styles['minimal'] = [
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
            ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
        ]

        # Bordered table style
        self.table_styles['bordered'] = [
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]

    def get_style(self, style_name: str) -> ParagraphStyle | None:
        """
        Returns a registered paragraph style by name.
        """
        return self.styles.get(style_name)

    def get_table_style(self, style_name: str) -> list:
        """
        Returns a registered table style by name.
        """
        return self.table_styles.get(style_name, self.table_styles['default'])

    def prepare_style(self, style_name: str, **kwargs) -> ParagraphStyle | None:
        """
        Gets a base style and applies modifications to it.
        """
        original_style = self.get_style(style_name)
        if not kwargs or not original_style:
            return original_style
        return modify_paragraph_style(original_style, **kwargs)
