from reportlab.lib import colors
from reportlab.platypus.paragraph import Paragraph
from src.services.layout_service import LayoutService

class ContentBuilder:
    """
    Content builder with integrated layout calculations.
    Page builders only see the ContentBuilder interface, not LayoutService.
    """
    def __init__(self, canvas, page_size, style_manager, config):
        self.canvas = canvas
        self.page_size = page_size
        self.style_manager = style_manager
        self.padding_h = config.get("common.padding.horizontal")
        self.padding_v = config.get("common.padding.vertical")
        self.current_pos = 0.0
        self.page_num = 1

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
                # Page break for continuation
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
