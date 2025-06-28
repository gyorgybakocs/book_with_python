# src/builders/content/table_builder.py
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib import colors
from src.logger import logger

class TableBuilder:
    """Handles ONLY tables - simple and advanced."""

    def __init__(self, canvas, page_size, style_manager, config):
        self.canvas = canvas
        self.page_size = page_size
        self.style_manager = style_manager
        self.config = config
        self.padding_h = config.get("common.padding.horizontal")

    def add_simple_table(self, headers: list, rows: list, current_pos: float,
                         caption: str = None, alignment: str = "center",
                         style: str = "default", width: str = "100%",
                         column_widths: list = None) -> float:
        """Add simple table, return new position."""
        try:
            if not headers or not rows:
                return current_pos

            table_data = self._create_simple_table_data(headers, rows)
            table = self._create_table_object(table_data, width, column_widths, style)
            new_pos = self._place_table(table, current_pos, alignment)

            if caption:
                new_pos = self._add_table_caption(caption, new_pos)

            return new_pos + 15

        except Exception as e:
            logger.error(f"Failed to add simple table: {e}")
            return current_pos + 50

    def add_advanced_table(self, headers: list, rows: list, current_pos: float,
                           caption: str = None, alignment: str = "center",
                           style_preset: str = "default", width: str = "100%",
                           column_widths: list = None, border_style: str = "thin") -> float:
        """Add advanced table with merged cells, return new position."""
        try:
            processed_headers = self._process_headers(headers)
            processed_rows, merge_commands = self._process_rows(rows, len(processed_headers))

            table_data = [processed_headers] + processed_rows
            table = self._create_advanced_table_object(table_data, width, column_widths,
                                                       style_preset, border_style, merge_commands)

            new_pos = self._place_table(table, current_pos, alignment)

            if caption:
                new_pos = self._add_table_caption(caption, new_pos)

            return new_pos + 15

        except Exception as e:
            logger.error(f"Failed to add advanced table: {e}")
            return current_pos + 50

    def _create_simple_table_data(self, headers: list, rows: list) -> list:
        """Create table data with Paragraph objects."""
        header_style = self.style_manager.prepare_style('paragraph_default',
                                                        fontSize=10, alignment=1)
        cell_style = self.style_manager.prepare_style('paragraph_default', fontSize=9)

        header_row = [Paragraph(f"<b>{header}</b>", header_style) for header in headers]
        data_rows = []
        for row in rows:
            table_row = [Paragraph(str(cell), cell_style) for cell in row]
            data_rows.append(table_row)

        return [header_row] + data_rows

    def _create_table_object(self, table_data: list, width: str, column_widths: list,
                             style: str) -> Table:
        """Create basic table object."""
        col_widths = self._calculate_column_widths(width, column_widths, len(table_data[0]))
        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        table_style = self.style_manager.get_table_style(style)
        table.setStyle(TableStyle(table_style))
        return table

    def _create_advanced_table_object(self, table_data: list, width: str,
                                      column_widths: list, style_preset: str,
                                      border_style: str, merge_commands: list) -> Table:
        """Create advanced table object with merging."""
        col_widths = self._calculate_column_widths(width, column_widths, len(table_data[0]))
        table = Table(table_data, colWidths=col_widths, repeatRows=1)

        base_style = self.style_manager.get_table_style(style_preset)
        border_commands = self._get_border_commands(border_style)
        all_commands = list(base_style) + border_commands + merge_commands
        table.setStyle(TableStyle(all_commands))

        return table

    def _process_headers(self, headers: list) -> list:
        """Process headers for advanced tables."""
        processed = []
        header_style = self.style_manager.prepare_style('paragraph_default',
                                                        fontSize=10, alignment=1)

        for header in headers:
            if isinstance(header, dict):
                text = header.get('text', '')
                processed.append(Paragraph(f"<b>{text}</b>", header_style))
            else:
                processed.append(Paragraph(f"<b>{header}</b>", header_style))

        return processed

    def _process_rows(self, rows: list, header_count: int) -> tuple[list, list]:
        """Process rows with cell merging - handles missing cells due to rowspan properly."""
        processed_rows = []
        merge_commands = []
        cell_style = self.style_manager.prepare_style('paragraph_default', fontSize=9)

        # Track which cells are already occupied by previous rowspans
        occupied_cells = {}  # (row_idx, col_idx) -> cell_info

        for row_idx, row in enumerate(rows):
            if isinstance(row, dict):
                cells = row.get('cells', [])
            else:
                cells = row

            processed_row = []
            col_idx = 0
            cell_input_idx = 0

            # Fill the row column by column
            while col_idx < header_count:
                # Check if this position is occupied by a previous rowspan
                if (row_idx, col_idx) in occupied_cells:
                    # This cell is occupied by a previous rowspan, add empty placeholder
                    processed_row.append(Paragraph("", cell_style))
                    col_idx += 1
                    continue

                # Check if we have more cells to process from input
                if cell_input_idx >= len(cells):
                    # No more input cells, fill with empty
                    processed_row.append(Paragraph("", cell_style))
                    col_idx += 1
                    continue

                # Process the next input cell
                cell = cells[cell_input_idx]
                cell_input_idx += 1

                if isinstance(cell, dict):  # Advanced cell with merging
                    text = cell.get('text', '')
                    colspan = cell.get('colspan', 1)
                    rowspan = cell.get('rowspan', 1)

                    # Add the cell content
                    processed_row.append(Paragraph(str(text), cell_style))

                    # Add merge command if needed
                    if colspan > 1 or rowspan > 1:
                        end_col = col_idx + colspan - 1
                        end_row = row_idx + rowspan - 1
                        merge_commands.append(
                            ('SPAN', (col_idx, row_idx + 1), (end_col, end_row + 1))  # +1 for header row
                        )
                        logger.debug(f"SPAN: ({col_idx}, {row_idx + 1}) to ({end_col}, {end_row + 1}) for '{text}'")

                    # Mark cells as occupied for future rows
                    for r in range(row_idx, row_idx + rowspan):
                        for c in range(col_idx, col_idx + colspan):
                            if r > row_idx or c > col_idx:  # Don't mark current position
                                occupied_cells[(r, c)] = {
                                    'text': text,
                                    'source_row': row_idx,
                                    'source_col': col_idx
                                }

                    # Apply cell styling if specified
                    cell_style_def = cell.get('style', {})
                    if cell_style_def:
                        self._apply_direct_cell_style(merge_commands, cell_style_def, col_idx, row_idx + 1)

                    col_idx += colspan

                else:  # Simple cell (string)
                    processed_row.append(Paragraph(str(cell), cell_style))
                    col_idx += 1

            # Ensure row has exactly header_count columns
            while len(processed_row) < header_count:
                processed_row.append(Paragraph("", cell_style))

            # Trim if somehow we have too many
            processed_row = processed_row[:header_count]

            processed_rows.append(processed_row)
            logger.debug(f"Row {row_idx}: {len(processed_row)} columns, occupied: {[k for k in occupied_cells.keys() if k[0] == row_idx]}")

        return processed_rows, merge_commands

    def _apply_direct_cell_style(self, style_commands: list, cell_style_def: dict, col: int, row: int):
        """Apply direct cell styling from JSON to style commands."""
        if cell_style_def.get('background_color'):
            color = self._parse_color(cell_style_def['background_color'])
            style_commands.append(
                ('BACKGROUND', (col, row), (col, row), color)
            )
            logger.debug(f"Added background color {cell_style_def['background_color']} at ({col}, {row})")

        if cell_style_def.get('text_color'):
            color = self._parse_color(cell_style_def['text_color'])
            style_commands.append(
                ('TEXTCOLOR', (col, row), (col, row), color)
            )

        if cell_style_def.get('font_weight') == 'bold':
            style_commands.append(
                ('FONTNAME', (col, row), (col, row), 'Helvetica-Bold')
            )

    def _parse_color(self, color_spec: str):
        """Parse color specification to ReportLab color."""
        from reportlab.lib import colors

        # Handle hex colors
        if color_spec.startswith('#'):
            return colors.HexColor(color_spec)

        # Handle named colors
        color_map = {
            'lightblue': colors.lightblue,
            'lightgreen': colors.lightgreen,
            'lightyellow': colors.lightyellow,
            'lightgrey': colors.lightgrey,
            'lightgray': colors.lightgrey,
            'red': colors.red,
            'blue': colors.blue,
            'green': colors.green,
            'yellow': colors.yellow,
            'white': colors.white,
            'black': colors.black,
            'gray': colors.gray,
            'grey': colors.grey,
        }

        return color_map.get(color_spec.lower(), colors.white)

    def _calculate_column_widths(self, width: str, column_widths: list, col_count: int) -> list:
        """Calculate column widths."""
        available_width = self.page_size[0] - 2 * self.padding_h

        if isinstance(width, str) and width.endswith('%'):
            percentage = float(width.rstrip('%')) / 100
            table_width = available_width * percentage
        else:
            table_width = width * 0.75 if isinstance(width, int) else available_width

        if column_widths:
            col_widths = []
            for col_width in column_widths:
                if isinstance(col_width, str) and col_width.endswith('%'):
                    percentage = float(col_width.rstrip('%')) / 100
                    col_widths.append(table_width * percentage)
                else:
                    col_widths.append(col_width * 0.75 if isinstance(col_width, int) else table_width / col_count)
            return col_widths
        else:
            return [table_width / col_count] * col_count

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

    def _get_border_commands(self, border_style: str) -> list:
        """Get border style commands."""
        border_width = {
            'none': 0, 'thin': 0.5, 'thick': 2.0, 'double': 1.0
        }.get(border_style, 0.5)

        if border_style == 'none':
            return []
        elif border_style == 'double':
            return [
                ('GRID', (0, 0), (-1, -1), 1.0, colors.black),
                ('BOX', (0, 0), (-1, -1), 2.0, colors.black),
            ]
        else:
            return [('GRID', (0, 0), (-1, -1), border_width, colors.black)]

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
