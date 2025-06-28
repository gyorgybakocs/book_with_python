# src/builders/content_builder.py (UPDATED FOR SIMPLE TABLES)
from src.logger import logger
from src.services.layout_service import LayoutService
from .content.text_builder import TextBuilder
from .content.image_builder import ImageBuilder
from .content.table_builder import TableBuilder
from .content.layout_builder import LayoutBuilder

class ContentBuilder:
    """Refactored ContentBuilder that delegates to specialized builders."""

    def __init__(self, canvas, page_size, style_manager, config):
        self.canvas = canvas
        self.page_size = page_size
        self.style_manager = style_manager
        self.config = config
        self.padding_h = config.get("common.padding.horizontal")
        self.padding_v = config.get("common.padding.vertical")
        self.current_pos = 0.0
        self.page_num = 1

        # Initialize specialized builders
        self.text_builder = TextBuilder(canvas, page_size, style_manager, config)
        self.image_builder = ImageBuilder(canvas, page_size, style_manager, config)
        self.table_builder = TableBuilder(canvas, page_size, style_manager, config)
        self.layout_builder = LayoutBuilder(canvas, page_size, style_manager, config)

        # Keep layout service for complex operations
        self.layout_service = LayoutService(self, config)

    # ==========================================
    # PUBLIC API - DELEGATE TO SPECIALIZED BUILDERS
    # ==========================================

    def start_from(self, pos: float):
        """Set starting position."""
        self.current_pos = float(pos)
        return self

    def add_spacing(self, spacing: float):
        """Add vertical spacing."""
        self.current_pos = self.layout_builder.add_spacing(self.current_pos, spacing)
        return self

    def add_title(self, text: str, **kwargs):
        """Add main title."""
        self.current_pos = self.text_builder.add_title(text, self.current_pos, **kwargs)
        return self

    def add_subtitle(self, text: str, **kwargs):
        """Add subtitle."""
        self.current_pos = self.text_builder.add_subtitle(text, self.current_pos, **kwargs)
        return self

    def add_paragraph(self, text: str, **kwargs):
        """Add paragraph."""
        extra_spacing = kwargs.pop('extra_spacing', 0)
        self.current_pos = self.text_builder.add_paragraph(text, self.current_pos, **kwargs)
        if extra_spacing > 0:
            self.add_spacing(extra_spacing)
        return self

    def add_image(self, src: str, **kwargs):
        """Add image."""
        self.current_pos = self.image_builder.add_image(src, self.current_pos, **kwargs)
        return self

    def add_table(self, data: list, style: list = None, **kwargs):
        """Add table with data matrix and style commands."""
        self.current_pos = self.table_builder.add_table(
            data, style, self.current_pos, **kwargs)
        return self

    def add_separator_line(self):
        """Add horizontal line."""
        self.current_pos = self.layout_builder.add_separator_line(self.current_pos)
        return self

    def add_header(self, text: str):
        """Add page header."""
        self.layout_builder.add_header(text, self.page_num)
        return self

    def add_footer(self, text: str):
        """Add page footer."""
        self.layout_builder.add_footer(text, self.page_num)
        return self

    def new_page(self):
        """Start new page."""
        self.canvas.showPage()
        self.page_num += 1
        self.current_pos = 0.0
        return self

    def add_blank_page(self):
        """Add blank page."""
        self.layout_builder.add_blank_page()
        self.new_page()
        return self

    # ==========================================
    # COMPLEX OPERATIONS - PROCESS CONTENT ITEMS
    # ==========================================

    def add_content_items(self, content_items: list):
        """Process list of mixed content items."""
        paragraphs = []

        for item in content_items:
            if item.get('type') == 'paragraph':
                text = item.get('text', '')
                if text.strip():
                    paragraphs.append(text)
                else:
                    paragraphs.append("")

            elif item.get('type') == 'image':
                # Add pending paragraphs first
                if paragraphs:
                    self.add_chapter_paragraphs_with_breaks(
                        paragraphs=paragraphs,
                        chapter_title="",
                        has_header=False,
                        has_footer=False
                    )
                    paragraphs = []

                # Check if image fits
                required_height = self.image_builder.estimate_image_height(
                    item.get('src'), item.get('width', 300),
                    item.get('height', 'auto'), item.get('caption'))
                available_height = self.layout_service.calculate_available_space(self.current_pos)

                if required_height > available_height:
                    self.new_page()
                    self.current_pos = self.padding_v

                self.add_image(
                    src=item.get('src'),
                    alignment=item.get('alignment', 'center'),
                    width=item.get('width', 300),
                    height=item.get('height', 'auto'),
                    caption=item.get('caption')
                )

            elif item.get('type') == 'table':
                # Add pending paragraphs first
                if paragraphs:
                    self.add_chapter_paragraphs_with_breaks(
                        paragraphs=paragraphs,
                        chapter_title="",
                        has_header=False,
                        has_footer=False
                    )
                    paragraphs = []

                self.add_table(
                    data=item.get('data', []),
                    style=item.get('style', []),
                    caption=item.get('caption'),
                    alignment=item.get('alignment', 'center')
                )

            else:
                logger.warning(f"Unknown content type: {item.get('type')} - skipping")

        # Add remaining paragraphs
        if paragraphs:
            self.add_chapter_paragraphs_with_breaks(
                paragraphs=paragraphs,
                chapter_title="",
                has_header=False,
                has_footer=False
            )

        return self

    def add_chapter_paragraphs_with_breaks(self, paragraphs: list, chapter_title: str = "",
                                           has_header: bool = False, has_footer: bool = False):
        """Add multiple paragraphs with intelligent page breaking."""
        for par_text in paragraphs:
            if not par_text.strip():
                self.add_spacing(10)
                continue

            # Use layout service for complex paragraph flow
            self._add_paragraph_with_breaks(par_text, chapter_title, has_header, has_footer)

        return self

    def _add_paragraph_with_breaks(self, text: str, chapter_title: str,
                                   has_header: bool, has_footer: bool):
        """Internal method using LayoutService for complex paragraph handling."""
        par_obj = self.text_builder.create_paragraph(text, firstLineIndent=20)

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
            self.current_pos = self.text_builder.draw_paragraph_object(parts[0], self.current_pos)
            self.add_spacing(10)

            # Check if there's continuation
            if len(parts) > 1:
                par_obj = parts[1]
                if has_footer:
                    self.add_footer(chapter_title)
                self.new_page()
                self.start_from(self.padding_v)
                if has_header:
                    self.add_header(f'<span>{chapter_title}</span>')
            else:
                par_obj = None

    # ==========================================
    # BACKWARD COMPATIBILITY METHODS
    # ==========================================

    def create_paragraph(self, text: str, **kwargs):
        """Create Paragraph object without drawing."""
        return self.text_builder.create_paragraph(text, **kwargs)

    def create_title_paragraph(self, text: str, **kwargs):
        """Create title paragraph."""
        style = self.style_manager.prepare_style('title_main', **kwargs)
        from reportlab.platypus.paragraph import Paragraph
        return Paragraph(text, style)

    def create_subtitle_paragraph(self, text: str, **kwargs):
        """Create subtitle paragraph."""
        style = self.style_manager.prepare_style('title_sub', **kwargs)
        from reportlab.platypus.paragraph import Paragraph
        return Paragraph(text, style)

    def draw_paragraph_object(self, p):
        """Draw existing Paragraph object."""
        self.current_pos = self.text_builder.draw_paragraph_object(p, self.current_pos)
        return self

    def get_paragraph_height(self, text: str, **kwargs) -> float:
        """Get paragraph height using text builder."""
        return self.text_builder.get_paragraph_height(text, **kwargs)

    def get_available_width(self) -> float:
        """Get available width for content."""
        return self.page_size[0] - 2 * self.padding_h

    def get_available_height(self, current_pos: float) -> float:
        """Get available height from current position."""
        return self.layout_service.calculate_available_space(current_pos)

    def _estimate_image_height_simple(self, image_item: dict) -> float:
        """Simple image height estimation for page break decisions."""
        return self.image_builder.estimate_image_height(
            image_item.get('src'),
            image_item.get('width', 300),
            image_item.get('height', 'auto'),
            image_item.get('caption')
        )
