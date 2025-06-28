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

        # Centralized color map for consistency
        self.color_map = {
            'lightblue': '#ADD8E6',
            'lightgreen': '#90EE90',
            'lightyellow': '#FFFFE0',
            'pink': '#FFC0CB',
            'ltgrey': '#EEEEEE',
            'grey': '#808080',
            'red': '#FF0000',
            'blue': '#0000FF',
            'green': '#008000',
            'yellow': '#FFFF00',
            'white': '#FFFFFF',
            'black': '#000000'
        }

    def register_styles(self):
        """
        Dynamically registers paragraph styles and table styles from the configuration file.
        """
        success = True
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

    def get_color_map(self) -> dict:
        """Returns the central color map."""
        return self.color_map

    def _parse_color(self, color_spec: str):
        """Converts color names or hex codes into ReportLab color objects using the central map."""
        if isinstance(color_spec, str):
            if color_spec.startswith('#'):
                return colors.HexColor(color_spec)

            hex_code = self.color_map.get(color_spec.lower())
            if hex_code:
                return colors.HexColor(hex_code)

            try:
                return colors.toColor(color_spec)
            except ValueError:
                return colors.white
        return color_spec

    def build_tense_table_style(self, block_index: int, raw_json_styles: list) -> list:
        """
        Builds the complete style command list for a specific block of the tense table.
        """
        style_cmds = [('GRID', (0, 0), (-1, -1), 0.5, colors.grey)]
        if block_index == 0:
            style_cmds.append(('ALIGN', (0, 0), (-1, -1), 'CENTER'))
            style_cmds.append(('VALIGN', (0, 0), (-1, -1), 'MIDDLE'))
            style_cmds.append(('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'))

        additional_styles = []
        for cmd_tuple in raw_json_styles:
            cmd, start, end, *rest = cmd_tuple

            if cmd == 'BACKGROUND' and rest:
                color_spec = rest[0]
                new_cmd = [cmd, start, end, self._parse_color(color_spec)]
                style_cmds.append(tuple(new_cmd))

                if block_index > 0 and str(color_spec).lower() not in ['ltgrey', 'grey']:
                    additional_styles.append(('FONTNAME', start, end, 'Helvetica-Bold'))
                    additional_styles.append(('ALIGN', start, end, 'CENTER'))
                    additional_styles.append(('VALIGN', start, end, 'MIDDLE'))
            else:
                style_cmds.append(cmd_tuple)

        style_cmds.extend(additional_styles)
        return style_cmds

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
