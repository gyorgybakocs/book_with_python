from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib import colors
from src.logger import logger

class TableBuilder:
    """Handles tables with simple data matrix + style commands."""

    def __init__(self, canvas, page_size, style_manager, config):
        self.canvas = canvas
        self.page_size = page_size
        self.style_manager = style_manager
        self.config = config
        self.padding_h = config.get("common.padding.horizontal")

    def add_table(self, data: list, style: list = None, current_pos: float = 0,
                  caption: str = None, alignment: str = "center") -> float:
        """Add table from data matrix and style commands."""
        try:
            if not data:
                return current_pos

            # Convert data to Paragraph objects
            table_data = self._convert_data_to_paragraphs(data)

            # Create table
            table = Table(table_data, repeatRows=1)

            # Apply styles
            style_commands = self._convert_style_commands(style or [])
            if style_commands:
                table.setStyle(TableStyle(style_commands))

            # Place table
            new_pos = self._place_table(table, current_pos, alignment)

            # Add caption
            if caption:
                new_pos = self._add_table_caption(caption, new_pos)

            return new_pos + 15

        except Exception as e:
            logger.error(f"Failed to add table: {e}")
            return current_pos + 50

    def _convert_data_to_paragraphs(self, data: list) -> list:
        """Convert string data matrix to Paragraph objects."""
        converted_data = []

        for row_idx, row in enumerate(data):
            converted_row = []
            for cell in row:
                if row_idx == 0:  # Header row
                    style = self.style_manager.prepare_style('paragraph_default',
                                                             fontSize=10, alignment=1)
                    if cell.strip():
                        converted_row.append(Paragraph(f"<b>{cell}</b>", style))
                    else:
                        converted_row.append(Paragraph("", style))
                else:  # Data rows
                    style = self.style_manager.prepare_style('paragraph_default', fontSize=9)
                    converted_row.append(Paragraph(str(cell), style))
            converted_data.append(converted_row)

        return converted_data

    def _convert_style_commands(self, style: list) -> list:
        """Convert JSON style commands to ReportLab format."""
        commands = []

        for style_cmd in style:
            if len(style_cmd) < 3:
                continue

            cmd_type = style_cmd[0]
            start_pos = tuple(style_cmd[1])
            end_pos = tuple(style_cmd[2])

            if cmd_type == "SPAN":
                commands.append(('SPAN', start_pos, end_pos))

            elif cmd_type == "BACKGROUND":
                if len(style_cmd) >= 4:
                    color_spec = style_cmd[3]
                    color = self._parse_color(color_spec)
                    commands.append(('BACKGROUND', start_pos, end_pos, color))

        return commands

    def _parse_color(self, color_spec: str):
        """Parse color specification to ReportLab color."""
        if color_spec.startswith('#'):
            return colors.HexColor(color_spec)

        color_map = {
            'lightblue': colors.lightblue,
            'lightgreen': colors.lightgreen,
            'lightyellow': colors.lightyellow,
            'lightgrey': colors.lightgrey,
            'red': colors.red,
            'blue': colors.blue,
            'green': colors.green,
            'yellow': colors.yellow,
            'white': colors.white,
            'black': colors.black,
        }

        return color_map.get(color_spec.lower(), colors.white)

    def _place_table(self, table: Table, current_pos: float, alignment: str) -> float:
        """Place table on page."""
        available_width = self.page_size[0] - 2 * self.padding_h

        try:
            table_width, table_height = table.wrapOn(self.canvas, available_width, 1000)
        except Exception as e:
            logger.error(f"Failed to calculate table dimensions: {e}")
            return current_pos + 100

        if alignment == "center":
            x_pos = self.padding_h + (available_width - table_width) / 2
        elif alignment == "right":
            x_pos = self.page_size[0] - self.padding_h - table_width
        else:  # left
            x_pos = self.padding_h

        y_pos = self.page_size[1] - current_pos - table_height
        table.drawOn(self.canvas, x_pos, y_pos)

        return current_pos + table_height + 5

    def _add_table_caption(self, caption: str, current_pos: float) -> float:
        """Add table caption."""
        caption_style = self.style_manager.prepare_style('paragraph_default',
                                                         fontSize=9, alignment=1)
        caption_p = Paragraph(f"<i>{caption}</i>", caption_style)
        width = self.page_size[0] - 2 * self.padding_h
        _, caption_height = caption_p.wrap(width, 30)

        y_pos = self.page_size[1] - current_pos - caption_height
        caption_p.drawOn(self.canvas, self.padding_h, y_pos)

        return current_pos + caption_height + 5
