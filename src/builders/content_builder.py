from reportlab.lib import colors
from reportlab.platypus.paragraph import Paragraph
from reportlab.platypus import Table, TableStyle
from reportlab.lib.utils import ImageReader
from reportlab.lib.units import inch
import os
from src.services.layout_service import LayoutService
from src.logger import logger

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logger.warning("PIL (Pillow) not available. Image support will be limited.")

class ContentBuilder:
    """
    Content builder with integrated layout calculations, image and table support.
    Page builders only see the ContentBuilder interface, not LayoutService.
    """
    def __init__(self, canvas, page_size, style_manager, config):
        self.canvas = canvas
        self.page_size = page_size
        self.style_manager = style_manager
        self.config = config
        self.padding_h = config.get("common.padding.horizontal")
        self.padding_v = config.get("common.padding.vertical")
        self.current_pos = 0.0
        self.page_num = 1

        # Get images path from config
        self.images_path = config.get("paths.resources") + "/images"

        # Internal LayoutService - page builders don't know about this
        self.layout_service = LayoutService(self, config)

    # ==========================================
    # PUBLIC API FOR PAGE BUILDERS
    # ==========================================

    def start_from(self, pos: float):
        """Sets the vertical starting position."""
        self.current_pos = float(pos)
        return self

    def add_spacing(self, spacing: float):
        """Adds vertical empty space."""
        self.current_pos += float(spacing)
        return self

    def add_title(self, text: str, **kwargs):
        """Adds a main title."""
        style = self.style_manager.prepare_style('title_main', **kwargs)
        return self._draw_paragraph(text, style)

    def add_subtitle(self, text: str, **kwargs):
        """Adds a subtitle."""
        self.add_spacing(6)
        style = self.style_manager.prepare_style('title_sub', **kwargs)
        return self._draw_paragraph(text, style)

    def add_paragraph(self, text: str, **kwargs):
        """Adds a standard paragraph."""
        extra_spacing = kwargs.pop('extra_spacing', 0)
        if extra_spacing > 0:
            self.add_spacing(extra_spacing)

        style_name = kwargs.pop('style_name', 'paragraph_default')
        style = self.style_manager.prepare_style(style_name, **kwargs)
        return self._draw_paragraph(text, style)

    def add_table(self, headers: list, rows: list, caption: str = None,
                  alignment: str = "center", style: str = "default",
                  width: str = "100%", column_widths: list = None):
        """
        Adds a simple table to the document with intelligent page breaking.

        Args:
            headers: List of column headers
            rows: List of rows (each row is a list of cell values)
            caption: Optional table caption
            alignment: "left", "center", or "right"
            style: Table style preset from StyleManager
            width: Table width as percentage or pixels
            column_widths: List of individual column widths
        """
        try:
            logger.info(f"Adding simple table with {len(headers)} columns and {len(rows)} rows")

            # Add spacing before table
            self.add_spacing(10)

            # Calculate available space
            available_width = self.page_size[0] - 2 * self.padding_h
            available_height = self.layout_service.calculate_available_space(self.current_pos + 30)

            # Calculate table width
            if isinstance(width, str) and width.endswith('%'):
                percentage = float(width.rstrip('%')) / 100
                table_width = available_width * percentage
            else:
                table_width = width * 0.75 if isinstance(width, int) else available_width

            # Calculate column widths
            col_widths = self._calculate_column_widths(column_widths, table_width, len(headers))

            # Create table data with Paragraph objects for proper text wrapping
            table_data = []

            # Headers
            header_style = self.style_manager.prepare_style('paragraph_default',
                                                            fontSize=10,
                                                            alignment=1)  # Center alignment
            header_row = [Paragraph(f"<b>{header}</b>", header_style) for header in headers]
            table_data.append(header_row)

            # Data rows
            cell_style = self.style_manager.prepare_style('paragraph_default', fontSize=9)
            for row in rows:
                table_row = [Paragraph(str(cell), cell_style) for cell in row]
                table_data.append(table_row)

            # Create ReportLab Table
            table = Table(table_data, colWidths=col_widths, repeatRows=1)

            # Apply table style from StyleManager
            table_style_commands = self.style_manager.get_table_style(style)
            table.setStyle(TableStyle(table_style_commands))

            # Handle table placement and splitting
            self._place_table_with_splitting(table, table_width, alignment, available_height)

            # Add caption if provided
            if caption:
                self.add_spacing(5)
                caption_style = self.style_manager.prepare_style('paragraph_default',
                                                                 fontSize=9,
                                                                 alignment=1)
                self._draw_paragraph(f"<i>{caption}</i>", caption_style)

            # Add spacing after table
            self.add_spacing(15)

            logger.info("Successfully added simple table")

        except Exception as e:
            logger.error(f"Failed to add simple table: {e}")

        return self

    def add_advanced_table(self, headers: list, rows: list, caption: str = None,
                           alignment: str = "center", style_preset: str = "default",
                           width: str = "100%", column_widths: list = None,
                           border_style: str = "thin"):
        """
        Adds an advanced table with proper header styling and column widths.
        """
        try:
            logger.info(f"Adding advanced table with {len(headers)} columns and {len(rows)} rows")

            # Add spacing before table
            self.add_spacing(10)

            # Calculate available space
            available_width = self.page_size[0] - 2 * self.padding_h
            available_height = self.layout_service.calculate_available_space(self.current_pos + 30)

            # Calculate table width
            if isinstance(width, str) and width.endswith('%'):
                percentage = float(width.rstrip('%')) / 100
                table_width = available_width * percentage
            else:
                table_width = width * 0.75 if isinstance(width, int) else available_width

            # Process headers with their styling
            processed_headers = []
            header_style_commands = []

            header_style = self.style_manager.prepare_style('paragraph_default',
                                                            fontSize=10,
                                                            alignment=1)

            for col_idx, header in enumerate(headers):
                if isinstance(header, dict):  # TableCell-like object with styling
                    text = header.get('text', '')
                    header_style_def = header.get('style', {})

                    processed_headers.append(Paragraph(f"<b>{text}</b>", header_style))

                    # Apply header styling
                    if header_style_def:
                        self._apply_direct_cell_style(header_style_commands, header_style_def, col_idx, 0)
                else:  # Simple string
                    processed_headers.append(Paragraph(f"<b>{header}</b>", header_style))

            # Process rows and handle merged cells
            processed_rows, row_style_commands = self._process_table_rows(rows, len(processed_headers))

            # Calculate column widths
            col_widths = self._calculate_column_widths(column_widths, table_width, len(processed_headers))
            logger.info(f"Column widths: {[f'{w:.1f}' for w in col_widths]}")

            # Create table data
            table_data = [processed_headers] + processed_rows

            # Create ReportLab Table with proper repeat rows
            table = Table(table_data, colWidths=col_widths, repeatRows=1)

            # Get style from StyleManager and apply additional styling
            base_style = self.style_manager.get_table_style(style_preset)
            table_style_commands = list(base_style)  # Copy the base style

            # Add border styling
            border_commands = self._get_border_style_commands(border_style)
            table_style_commands.extend(border_commands)

            # Add header-specific styles
            table_style_commands.extend(header_style_commands)

            # Add row-specific styles
            table_style_commands.extend(row_style_commands)

            logger.info(f"Applied {len(table_style_commands)} style commands")
            table.setStyle(TableStyle(table_style_commands))

            # Handle table placement and splitting
            self._place_table_with_splitting(table, table_width, alignment, available_height)

            # Add caption if provided
            if caption:
                self.add_spacing(5)
                caption_style = self.style_manager.prepare_style('paragraph_default',
                                                                 fontSize=9,
                                                                 alignment=1)
                self._draw_paragraph(f"<i>{caption}</i>", caption_style)

            # Add spacing after table
            self.add_spacing(15)

            logger.info("Successfully added advanced table")

        except Exception as e:
            logger.error(f"Failed to add advanced table: {e}", exc_info=True)

        return self

    def _process_table_headers(self, headers: list) -> list:
        """Process headers, handling both strings and TableCell objects with styling."""
        processed = []
        header_style = self.style_manager.prepare_style('paragraph_default',
                                                        fontSize=10,
                                                        alignment=1)

        for header in headers:
            if isinstance(header, dict):  # TableCell-like object
                text = header.get('text', '')
                processed.append(Paragraph(f"<b>{text}</b>", header_style))
            else:  # Simple string
                processed.append(Paragraph(f"<b>{header}</b>", header_style))

        return processed

    def _process_table_rows(self, rows: list, header_count: int) -> tuple:
        """Process rows and generate style commands for merged cells and direct styling."""
        processed_rows = []
        style_commands = []

        cell_style = self.style_manager.prepare_style('paragraph_default', fontSize=9)

        for row_idx, row in enumerate(rows):
            if isinstance(row, dict):
                cells = row.get('cells', [])
            else:
                cells = row

            processed_row = []
            col_idx = 0

            for cell in cells:
                if isinstance(cell, dict):  # TableCell object
                    text = cell.get('text', '')
                    cell_style_def = cell.get('style', {})
                    colspan = cell.get('colspan', 1)
                    rowspan = cell.get('rowspan', 1)

                    # Create paragraph with cell text
                    processed_row.append(Paragraph(str(text), cell_style))

                    # Add merged cell commands if needed
                    if colspan > 1 or rowspan > 1:
                        end_col = col_idx + colspan - 1
                        end_row = row_idx + 1 + rowspan - 1
                        style_commands.append(
                            ('SPAN', (col_idx, row_idx + 1), (end_col, end_row))
                        )
                        logger.debug(f"Added SPAN: ({col_idx}, {row_idx + 1}) to ({end_col}, {end_row})")

                    # Apply direct cell styling if specified
                    if cell_style_def:
                        self._apply_direct_cell_style(style_commands, cell_style_def, col_idx, row_idx + 1)

                    col_idx += colspan

                else:  # Simple string
                    processed_row.append(Paragraph(str(cell), cell_style))
                    col_idx += 1

            # Fill remaining cells if row is shorter than header
            while len(processed_row) < header_count:
                processed_row.append(Paragraph("", cell_style))

            processed_rows.append(processed_row)

        return processed_rows, style_commands

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

    def _get_border_style_commands(self, border_style: str) -> list:
        """Get border style commands."""
        from reportlab.lib import colors

        border_width = {
            'none': 0,
            'thin': 0.5,
            'thick': 2.0,
            'double': 1.0
        }.get(border_style, 0.5)

        if border_style == 'none':
            return []
        elif border_style == 'double':
            return [
                ('GRID', (0, 0), (-1, -1), 1.0, colors.black),
                ('BOX', (0, 0), (-1, -1), 2.0, colors.black),
            ]
        else:
            return [
                ('GRID', (0, 0), (-1, -1), border_width, colors.black),
            ]

    def _calculate_column_widths(self, column_widths: list, table_width: float, header_count: int) -> list:
        """Calculate column widths with better defaults."""
        if column_widths:
            col_widths = []
            for col_width in column_widths:
                if isinstance(col_width, str) and col_width.endswith('%'):
                    percentage = float(col_width.rstrip('%')) / 100
                    col_widths.append(table_width * percentage)
                else:
                    col_widths.append(col_width * 0.75 if isinstance(col_width, int) else table_width / header_count)
            return col_widths
        else:
            # Better default column widths for the tense table
            if header_count == 4:  # Specific for our tense table
                return [
                    table_width * 0.15,  # First column (Si, Co, Pe, Mo) - narrow
                    table_width * 0.15,  # Time column - narrow
                    table_width * 0.35,  # Form column - wider
                    table_width * 0.35   # Example column - wider
                ]
            else:
                # Equal width columns for other tables
                return [table_width / header_count] * header_count

    def _place_table_with_splitting(self, table, table_width, alignment, available_height):
        """Handle table placement with intelligent splitting and proper header repetition."""
        # Check if table fits on current page
        try:
            table_width_final, table_height = table.wrapOn(self.canvas, table_width, available_height)
            logger.info(f"Table dimensions: {table_width_final:.1f}x{table_height:.1f}, available height: {available_height:.1f}")
        except Exception as e:
            logger.error(f"Error wrapping table: {e}")
            # Force page break and try on new page
            self.new_page()
            self.current_pos = self.padding_v
            available_height = self.layout_service.calculate_available_space(self.current_pos + 30)
            table_width_final, table_height = table.wrapOn(self.canvas, table_width, available_height)

        if table_height > available_height and available_height > 100:  # Only split if we have some space
            logger.info("Table doesn't fit, attempting to split")
            try:
                # Try to split the table
                split_tables = table.split(table_width, available_height)

                if len(split_tables) > 1:
                    logger.info(f"Table split into {len(split_tables)} parts")
                    # Draw first part
                    self._draw_table_part(split_tables[0], table_width, alignment)

                    # Page break and draw remaining parts
                    for i, table_part in enumerate(split_tables[1:], 1):
                        self.new_page()
                        self.current_pos = self.padding_v
                        logger.info(f"Drawing table part {i+1} on new page")
                        self._draw_table_part(table_part, table_width, alignment)
                else:
                    # Table can't be split properly, force page break
                    logger.info("Table can't be split properly, forcing page break")
                    self.new_page()
                    self.current_pos = self.padding_v
                    self._draw_table_part(table, table_width, alignment)
            except Exception as e:
                logger.error(f"Error splitting table: {e}")
                # Fallback: force page break
                self.new_page()
                self.current_pos = self.padding_v
                self._draw_table_part(table, table_width, alignment)
        else:
            # Table fits, draw it
            self._draw_table_part(table, table_width, alignment)

    def _draw_table_part(self, table, table_width, alignment):
        """Draw a table part at current position."""
        # Calculate table position based on alignment
        available_width = self.page_size[0] - 2 * self.padding_h

        if alignment == "center":
            x_pos = self.padding_h + (available_width - table_width) / 2
        elif alignment == "right":
            x_pos = self.page_size[0] - self.padding_h - table_width
        else:  # left
            x_pos = self.padding_h

        # Get actual table dimensions
        actual_width, actual_height = table.wrapOn(self.canvas, table_width, 1000)

        # Draw table
        y_pos = self.page_size[1] - self.current_pos - actual_height
        table.drawOn(self.canvas, x_pos, y_pos)

        # Update current position
        self.current_pos += actual_height + 5

    def add_image(self, src: str, alignment: str = "center", width = 300,
                  height = "auto", caption: str = None):
        """
        Adds an image to the document with intelligent sizing.

        Args:
            src: Image filename (from resources/images/)
            alignment: "left", "center", or "right"
            width: Image width in pixels or percentage string (e.g., "70%")
            height: Image height in pixels, "auto", or percentage string (e.g., "50%")
            caption: Optional image caption
        """
        image_path = os.path.join(self.images_path, src)

        if not os.path.exists(image_path):
            logger.warning(f"Image not found: {image_path} - skipping")
            return self

        if not PIL_AVAILABLE:
            logger.warning(f"PIL not available, cannot process image: {src} - skipping")
            return self

        try:
            # Add spacing before image
            self.add_spacing(10)

            # Load and process image
            img = Image.open(image_path)
            img_width, img_height = img.size
            aspect_ratio = img_height / img_width

            # Calculate available space
            available_width = self.page_size[0] - 2 * self.padding_h
            available_height = self.layout_service.calculate_available_space(self.current_pos + 30)

            logger.info(f"Processing image {src}: width={width} (type: {type(width)}), height={height} (type: {type(height)})")

            # Calculate final dimensions - support percentage strings and auto
            if isinstance(width, str) and width.endswith('%'):
                # Width as percentage
                percentage = float(width.rstrip('%')) / 100
                width_points = available_width * percentage
                height_points = width_points * aspect_ratio
                logger.info(f"Width percentage: {width} = {width_points:.1f} points")

                # Check if height would be too tall
                if height_points > available_height:
                    logger.info(f"Image {src}: width={width} would be too tall, scaling to fit height")
                    height_points = available_height
                    width_points = height_points / aspect_ratio

            elif isinstance(height, str) and height.endswith('%') and height != "auto":
                # Height as percentage
                percentage = float(height.rstrip('%')) / 100
                height_points = available_height * percentage
                width_points = height_points / aspect_ratio
                logger.info(f"Height percentage: {height} = {height_points:.1f} points")

                # Check if width would be too wide
                if width_points > available_width:
                    logger.info(f"Image {src}: height={height} would be too wide, scaling to fit width")
                    width_points = available_width
                    height_points = width_points * aspect_ratio

            elif width == "auto" and isinstance(height, str) and height.endswith('%'):
                # Auto width with percentage height
                percentage = float(height.rstrip('%')) / 100
                height_points = available_height * percentage
                width_points = height_points / aspect_ratio
                logger.info(f"Auto width with height {height}: {width_points:.1f}x{height_points:.1f} points")

                # Check if width would be too wide
                if width_points > available_width:
                    logger.info(f"Image {src}: auto width would be too wide, scaling to fit")
                    width_points = available_width
                    height_points = width_points * aspect_ratio

            else:
                # Normal pixel-based sizing
                width_points = width * 0.75  # Convert pixels to points

                if height == "auto":
                    height_points = width_points * aspect_ratio
                else:
                    height_points = height * 0.75

                # Check if dimensions exceed available space and scale down if needed
                if width_points > available_width:
                    scale_factor = available_width / width_points
                    width_points = available_width
                    height_points = height_points * scale_factor
                    logger.info(f"Image {src}: scaled down to fit width")

                if height_points > available_height:
                    scale_factor = available_height / height_points
                    height_points = available_height
                    width_points = width_points * scale_factor
                    logger.info(f"Image {src}: scaled down to fit height")

            # Only check page break for non-chapter content (simple chapters, etc.)
            # For main chapters, ChapterBuilder handles page breaks with headers/footers
            total_height = height_points + (25 if caption else 0) + 20

            # Don't auto-break pages in main chapters - let ChapterBuilder handle it
            # We can detect this by checking if we have headers (crude but works)
            has_headers = hasattr(self, '_in_main_chapter') and self._in_main_chapter

            if not has_headers and total_height > self.layout_service.calculate_available_space(self.current_pos):
                self.new_page()
                self.current_pos = self.padding_v
                # Recalculate available height for new page
                available_height = self.layout_service.calculate_available_space(self.current_pos + 30)

                # Re-check sizing on new page if needed
                if height_points > available_height:
                    height_points = available_height
                    width_points = height_points / aspect_ratio

            # Calculate X position based on alignment
            if alignment == "center":
                x_pos = self.padding_h + (available_width - width_points) / 2
            elif alignment == "right":
                x_pos = self.page_size[0] - self.padding_h - width_points
            else:  # left
                x_pos = self.padding_h

            # Draw image
            y_pos = self.page_size[1] - self.current_pos - height_points

            img_reader = ImageReader(image_path)
            self.canvas.drawImage(img_reader, x_pos, y_pos,
                                  width=width_points, height=height_points)

            self.current_pos += height_points + 5

            # Add caption if provided
            if caption:
                self.add_spacing(5)
                caption_style = self.style_manager.prepare_style('paragraph_default',
                                                                 fontSize=10,
                                                                 alignment=1)
                self._draw_paragraph(f"<i>{caption}</i>", caption_style)

            # Add spacing after image+caption
            self.add_spacing(10)

            logger.info(f"Successfully added image: {src} ({width_points:.0f}x{height_points:.0f} points)")

        except Exception as e:
            logger.error(f"Failed to add image {src}: {e}")

        return self

    def add_content_items(self, content_items: list):
        """
        Processes a list of content items (paragraphs, images, simple and advanced tables).
        Args:
            content_items: List of content items from the new JSON structure
        """
        # Convert content items to paragraphs list for the existing intelligent method
        paragraphs = []

        for item in content_items:
            if item.get('type') == 'paragraph':
                text = item.get('text', '')
                if text.strip():
                    paragraphs.append(text)
                else:
                    paragraphs.append("")  # Empty paragraph for spacing

            elif item.get('type') == 'image':
                # Handle image - check if it fits, if not do page break
                required_height = self._estimate_image_height_simple(item)
                available_height = self.layout_service.calculate_available_space(self.current_pos)

                if required_height > available_height:
                    # Force page break by adding current paragraphs and starting new page
                    if paragraphs:
                        self.add_chapter_paragraphs_with_breaks(
                            paragraphs=paragraphs,
                            chapter_title="",
                            has_header=False,
                            has_footer=False
                        )
                        paragraphs = []

                    self.new_page()
                    self.current_pos = self.padding_v

                # Add the image
                self.add_image(
                    src=item.get('src'),
                    alignment=item.get('alignment', 'center'),
                    width=item.get('width', 300),
                    height=item.get('height', 'auto'),
                    caption=item.get('caption')
                )

            elif item.get('type') == 'table':
                # Handle simple table - first add any pending paragraphs
                if paragraphs:
                    self.add_chapter_paragraphs_with_breaks(
                        paragraphs=paragraphs,
                        chapter_title="",
                        has_header=False,
                        has_footer=False
                    )
                    paragraphs = []

                # Add the simple table
                self.add_table(
                    headers=item.get('headers', []),
                    rows=item.get('rows', []),
                    caption=item.get('caption'),
                    alignment=item.get('alignment', 'center'),
                    style=item.get('style_preset', 'default'),
                    width=item.get('width', '100%'),
                    column_widths=item.get('column_widths')
                )

            elif item.get('type') == 'advanced_table':
                # Handle advanced table - first add any pending paragraphs
                if paragraphs:
                    self.add_chapter_paragraphs_with_breaks(
                        paragraphs=paragraphs,
                        chapter_title="",
                        has_header=False,
                        has_footer=False
                    )
                    paragraphs = []

                # Add the advanced table
                self.add_advanced_table(
                    headers=item.get('headers', []),
                    rows=item.get('rows', []),
                    caption=item.get('caption'),
                    alignment=item.get('alignment', 'center'),
                    style_preset=item.get('style_preset', 'default'),
                    width=item.get('width', '100%'),
                    column_widths=item.get('column_widths'),
                    border_style=item.get('border_style', 'thin')
                )

            else:
                logger.warning(f"Unknown content type: {item.get('type')} - skipping")

        # Add remaining paragraphs with intelligent page breaking
        if paragraphs:
            self.add_chapter_paragraphs_with_breaks(
                paragraphs=paragraphs,
                chapter_title="",
                has_header=False,
                has_footer=False
            )

        return self

    def _estimate_image_height_simple(self, image_item: dict) -> float:
        """
        Simple image height estimation for page break decisions.
        """
        width = image_item.get('width', 300)
        height = image_item.get('height', 'auto')
        caption = image_item.get('caption')

        # Quick estimation
        if isinstance(width, str) and width.endswith('%'):
            percentage = float(width.rstrip('%')) / 100
            available_width = self.page_size[0] - 2 * self.padding_h
            width_points = available_width * percentage
            height_points = width_points * 0.6  # Rough aspect ratio
        elif isinstance(height, str) and height.endswith('%') and height != "auto":
            percentage = float(height.rstrip('%')) / 100
            available_height = self.layout_service.calculate_available_space(self.current_pos + 30)
            height_points = available_height * percentage
        else:
            width_points = width * 0.75 if isinstance(width, int) else 225
            height_points = width_points * 0.6 if height == "auto" else height * 0.75

        # Add space for caption and margins
        total_height = height_points + (25 if caption else 0) + 20
        return total_height

    def add_chapter_paragraphs_with_breaks(self, paragraphs: list, chapter_title: str = "",
                                           has_header: bool = False, has_footer: bool = False):
        """
        Adds multiple paragraphs with intelligent page breaking.
        This is where LayoutService is used internally.
        """
        for i, par_text in enumerate(paragraphs):
            if not par_text.strip():
                self.add_spacing(10)
                continue

            # Use internal LayoutService to handle complex paragraph flow
            self._add_paragraph_with_breaks(par_text, chapter_title, has_header, has_footer)

    def _add_paragraph_with_breaks(self, text: str, chapter_title: str,
                                   has_header: bool, has_footer: bool):
        """
        Internal method that uses LayoutService for complex paragraph handling.
        Page builders don't call this directly.
        """
        par_obj = self.create_paragraph(text, firstLineIndent=20)

        while par_obj:
            # Use LayoutService to calculate available space
            available_height = self.layout_service.calculate_available_space(self.current_pos)

            # If no space, do page break
            if available_height <= 0:
                if has_footer:
                    self.add_footer(chapter_title)
                self.new_page()
                self.start_from(self.padding_v)
                if has_header:
                    self.add_header(f'<span>{chapter_title}</span>')
                available_height = self.layout_service.calculate_available_space(self.current_pos)

            # Use LayoutService to split paragraph
            width = self.page_size[0] - 2 * self.padding_h
            parts = par_obj.split(width, available_height)

            if not parts:
                break

            # Draw the part that fits
            self.draw_paragraph_object(parts[0])
            self.add_spacing(10)

            # Check if there's continuation
            if len(parts) > 1:
                par_obj = parts[1]
                # Will need page break for continuation
                if has_footer:
                    self.add_footer(chapter_title)
                self.new_page()
                self.start_from(self.padding_v)
                if has_header:
                    self.add_header(f'<span>{chapter_title}</span>')
            else:
                par_obj = None

    def add_separator_line(self):
        """Adds a horizontal line at the current position."""
        y = self.page_size[1] - self.current_pos
        self.canvas.line(self.padding_h, y, self.page_size[0] - self.padding_h, y)
        return self

    def add_header(self, text: str):
        """Adds a page header."""
        style = self.style_manager.prepare_style('title_sub', alignment=2)
        y = self.page_size[1] - self.padding_v

        self.canvas.line(self.padding_h, y, self.page_size[0] - self.padding_h, y)
        p = Paragraph(text, style)
        p.wrapOn(self.canvas, self.page_size[0] - 2 * self.padding_h, 50)
        p.drawOn(self.canvas, self.padding_h, y + 5)
        return self

    def add_footer(self, text: str):
        """Adds a page footer."""
        style = self.style_manager.get_style('paragraph_default')
        y = self.padding_v

        self.canvas.line(self.padding_h, y, self.page_size[0] - self.padding_h, y)
        txt_with_num = f"{self.page_num} | {text}"
        p = Paragraph(txt_with_num, style)
        p.wrapOn(self.canvas, self.page_size[0] - 2 * self.padding_h, 50)
        p.drawOn(self.canvas, self.padding_h, y - 18)
        return self

    def new_page(self):
        """Starts a new page."""
        self.canvas.showPage()
        self.page_num += 1
        self.current_pos = 0.0
        return self

    def add_blank_page(self):
        """Adds a completely blank page."""
        self.canvas.setFillColor(colors.white)
        self.canvas.rect(0, 0, self.page_size[0], self.page_size[1], stroke=0, fill=1)
        self.new_page()
        return self

    def create_paragraph(self, text: str, **kwargs):
        """Creates a Paragraph object without drawing it."""
        style_name = kwargs.pop('style_name', 'paragraph_default')
        style = self.style_manager.prepare_style(style_name, **kwargs)
        return Paragraph(text, style)

    def create_title_paragraph(self, text: str, **kwargs):
        """Creates a title paragraph."""
        style = self.style_manager.prepare_style('title_main', **kwargs)
        return Paragraph(text, style)

    def create_subtitle_paragraph(self, text: str, **kwargs):
        """Creates a subtitle paragraph."""
        style = self.style_manager.prepare_style('title_sub', **kwargs)
        return Paragraph(text, style)

    def draw_paragraph_object(self, p: Paragraph):
        """Draws an existing Paragraph object at current position."""
        width = self.page_size[0] - 2 * self.padding_h
        _w, h = p.wrap(width, 10000)

        y_pos = self.page_size[1] - self.current_pos
        p.drawOn(self.canvas, self.padding_h, y_pos - h)
        self.current_pos += h
        return self

    # ==========================================
    # INTERNAL METHODS (use LayoutService)
    # ==========================================

    def _draw_paragraph(self, text: str, style):
        """Internal helper to draw a styled paragraph."""
        width = self.page_size[0] - 2 * self.padding_h
        y_pos = self.page_size[1] - self.current_pos

        p = Paragraph(text, style)
        w, h = p.wrap(width, 10000)
        p.drawOn(self.canvas, self.padding_h, y_pos - h)

        self.current_pos += h
        return self

    def get_paragraph_height(self, text: str, **kwargs) -> float:
        """Gets paragraph height using LayoutService."""
        return self.layout_service.calculate_paragraph_height(text, **kwargs)
