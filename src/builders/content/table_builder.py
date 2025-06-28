import re
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from src.logger import logger

class TableBuilder:
    """
    Debug version: prints the string content being passed to the Paragraph
    object to diagnose the color replacement issue.
    """
    def __init__(self, canvas, page_size, style_manager, config):
        self.canvas = canvas
        self.page_size = page_size
        self.style_manager = style_manager
        self.config = config
        self.padding_h = config.get("common.padding.horizontal")

    def _preprocess_html_colors(self, text: str) -> str:
        """
        Finds custom color names in HTML-like tags and replaces them with
        hex codes using simple string.replace().
        """
        color_map = self.style_manager.get_color_map()
        processed_text = str(text)

        for name, hex_code in color_map.items():
            # This logic replaces the color names inside the tags directly.
            # It's case-sensitive.

            # Variations for backColor with single and double quotes
            processed_text = processed_text.replace(f"<backColor='{name}'>", f"<backColor='{hex_code}'>")
            processed_text = processed_text.replace(f'<backColor="{name}">', f'<backColor="{hex_code}">')

            # Variations for font color with single and double quotes
            processed_text = processed_text.replace(f"<font color='{name}'>", f"<font color='{hex_code}'>")
            processed_text = processed_text.replace(f'<font color="{name}">', f'<font color="{hex_code}">')

        return processed_text

    def add_table(self, data: list, style: list = None, current_pos: float = 0,
                  caption: str = None, alignment: str = "center",
                  block_column_widths: list = None, **kwargs) -> float:
        """
        Creates a series of tables, processing cell content as rich text Paragraphs
        with cell-specific styling to preserve formatting.
        """
        try:
            available_width = self.page_size[0] - 2 * self.padding_h
            y_pos_after_last_table = current_pos

            for i in range(len(data)):
                table_data_raw = data[i]
                table_style_raw = style[i]
                width_specs_percent = block_column_widths[i]
                col_widths_in_points = [available_width * (float(p.strip('%')) / 100) if '%' in p else float(p) for p in width_specs_percent]

                # Create Paragraphs with cell-specific styles
                table_data_as_paragraphs = []
                for r, row_data in enumerate(table_data_raw):
                    paragraph_row = []
                    for c, cell_text in enumerate(row_data):
                        is_header = (i == 0)
                        is_colored_cell = any(
                            cmd[0] == 'BACKGROUND' and
                            cmd[1][0] <= c <= cmd[2][0] and
                            cmd[1][1] <= r <= cmd[2][1] and
                            str(cmd[3]).lower() not in ['ltgrey', 'grey']
                            for cmd in table_style_raw
                        )

                        style_args = {'fontSize': 9, 'leading': 11}
                        if is_header:
                            style_args['fontName'] = 'Helvetica-Bold'
                            style_args['alignment'] = TA_CENTER
                        elif is_colored_cell:
                            style_args['fontName'] = 'Helvetica-Bold'
                            style_args['alignment'] = TA_CENTER
                        else:
                            style_args['alignment'] = TA_LEFT

                        cell_para_style = self.style_manager.prepare_style('paragraph_default', **style_args)

                        processed_text = self._preprocess_html_colors(str(cell_text))

                        paragraph = Paragraph(processed_text, cell_para_style)
                        paragraph_row.append(paragraph)
                    table_data_as_paragraphs.append(paragraph_row)

                # Get cell-level styles from the JSON
                final_table_style_cmds = []
                for cmd_tuple in table_style_raw:
                    cmd, start, end, *rest = cmd_tuple
                    if cmd in ('GRID', 'SPAN', 'BACKGROUND', 'LINEBELOW', 'LINEABOVE', 'LINEBEFORE', 'LINEAFTER', 'VALIGN'):
                        if cmd == 'BACKGROUND':
                            final_table_style_cmds.append(tuple([cmd, start, end, self.style_manager._parse_color(rest[0])]))
                        else:
                            final_table_style_cmds.append(cmd_tuple)

                # Add VALIGN MIDDLE to colored cells
                for cmd_tuple in table_style_raw:
                    if i > 0 and cmd_tuple[0] == 'BACKGROUND' and str(cmd_tuple[3]).lower() not in ['ltgrey', 'grey']:
                        cmd, start, end, *rest = cmd_tuple
                        final_table_style_cmds.append(('VALIGN', start, end, 'MIDDLE'))

                if table_data_as_paragraphs and len(table_data_as_paragraphs[0]) != len(col_widths_in_points):
                    logger.error(f"Data inconsistency in table block {i}")
                    continue

                table_obj = Table(table_data_as_paragraphs, colWidths=col_widths_in_points)
                table_obj.setStyle(TableStyle(final_table_style_cmds))
                y_pos_after_last_table = self._place_table(table_obj, y_pos_after_last_table, alignment)

            if caption:
                y_pos_after_last_table = self._add_table_caption(caption, y_pos_after_last_table)

            return y_pos_after_last_table + 10
        except Exception as e:
            logger.error(f"Failed to add table with rich text: {e}", exc_info=True)
            return current_pos + 50

    def _place_table(self, table: Table, current_pos: float, alignment: str) -> float:
        """Places a single table object on the canvas and updates the Y position."""
        available_width = self.page_size[0] - 2 * self.padding_h
        table_width, table_height = table.wrapOn(self.canvas, available_width, 0)

        if alignment == "center":
            x_pos = self.padding_h + (available_width - table_width) / 2
        elif alignment == "right":
            x_pos = self.page_size[0] - self.padding_h - table_width
        else:
            x_pos = self.padding_h

        y_pos = self.page_size[1] - current_pos - table_height
        table.drawOn(self.canvas, x_pos, y_pos)

        return current_pos + table_height

    def _add_table_caption(self, caption: str, current_pos: float) -> float:
        """Adds a caption below the entire set of tables."""
        caption_style = self.style_manager.prepare_style('paragraph_default', fontSize=9, alignment=1)
        caption_p = Paragraph(f"<i>{caption}</i>", caption_style)

        available_width = self.page_size[0] - 2 * self.padding_h
        caption_width, caption_height = caption_p.wrap(available_width, self.page_size[1])

        y_pos = self.page_size[1] - current_pos - caption_height - 5
        x_pos = self.padding_h
        caption_p.drawOn(self.canvas, x_pos, y_pos)

        return current_pos + caption_height + 10
