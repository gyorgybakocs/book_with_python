from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib import colors
from src.logger import logger

class TableBuilder:
    """
    Final version based on the corrected JSON structure.
    It iterates through the list of tables provided in the JSON
    and creates them one by one.
    """

    def __init__(self, canvas, page_size, style_manager, config):
        self.canvas = canvas
        self.page_size = page_size
        self.style_manager = style_manager
        self.config = config
        self.padding_h = config.get("common.padding.horizontal")

    def add_table(self, data: list, style: list = None, current_pos: float = 0,
                  caption: str = None, alignment: str = "center",
                  block_column_widths: list = None, **kwargs) -> float:
        """
        Creates a series of small, independent tables from the provided lists.
        The JSON is expected to provide a list for each table block.
        """
        try:
            available_width = self.page_size[0] - 2 * self.padding_h
            y_pos_after_last_table = current_pos

            # The JSON is a list of tables, so we just loop through it.
            for i in range(len(data)):
                table_data = data[i]
                table_style_raw = style[i]
                width_specs_percent = block_column_widths[i]

                # Convert percentage widths to absolute points.
                col_widths_in_points = [available_width * (float(p.strip('%')) / 100) if '%' in p else float(p) for p in width_specs_percent]

                # Process style commands to handle colors and add a default GRID.
                table_style_cmds = [('GRID', (0, 0), (-1, -1), 0.5, colors.grey)]
                for cmd_tuple in table_style_raw:
                    cmd, start, end, *rest = cmd_tuple
                    if cmd == 'BACKGROUND' and rest:
                        new_cmd = [cmd, start, end, self._parse_color(rest[0])]
                        table_style_cmds.append(tuple(new_cmd))
                    else:
                        table_style_cmds.append(cmd_tuple)

                # Check for data consistency before creating the table.
                if table_data and len(table_data[0]) != len(col_widths_in_points):
                    logger.error(f"Data inconsistency in table block {i}: "
                                 f"{len(table_data[0])} data columns vs {len(col_widths_in_points)} widths. Skipping block.")
                    continue

                # Create the simple Table object for the current block.
                table_obj = Table(table_data, colWidths=col_widths_in_points)
                table_obj.setStyle(TableStyle(table_style_cmds))

                # Place the table on the canvas.
                y_pos_after_last_table = self._place_table(table_obj, y_pos_after_last_table, alignment)

            if caption:
                y_pos_after_last_table = self._add_table_caption(caption, y_pos_after_last_table)

            return y_pos_after_last_table + 10

        except Exception as e:
            logger.error(f"Failed to add table with final simplified logic: {e}", exc_info=True)
            return current_pos + 50

    def _parse_color(self, color_spec: str):
        """Converts color names or hex codes into ReportLab color objects."""
        if isinstance(color_spec, str) and color_spec.startswith('#'): return colors.HexColor(color_spec)
        color_map = {'lightblue': colors.lightblue, 'lightgreen': colors.lightgreen, 'lightyellow': colors.lightyellow, 'lightgrey': colors.lightgrey, 'ltgrey': colors.lightgrey, 'lightcyan': colors.lightcyan, 'red': colors.red, 'blue': colors.blue, 'green': colors.green, 'yellow': colors.yellow, 'white': colors.white, 'black': colors.black, 'pink': colors.pink}
        return color_map.get(str(color_spec).lower(), colors.white)

    def _place_table(self, table: Table, current_pos: float, alignment: str) -> float:
        """Places a single table object on the canvas and updates the Y position."""
        available_width = self.page_size[0] - 2 * self.padding_h
        table_width, table_height = table.wrapOn(self.canvas, available_width, 0)

        if alignment == "center":
            x_pos = self.padding_h + (available_width - table_width) / 2
        elif alignment == "right":
            x_pos = self.page_size[0] - self.padding_h - table_width
        else: # "left"
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
