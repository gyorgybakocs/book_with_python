from reportlab.lib import colors
from reportlab.platypus.paragraph import Paragraph
from src.managers.style_manager import modify_paragraph_style

class ContentBuilder:
    """
    A low-level toolbox for drawing elements onto a PDF canvas.
    This class manages the current drawing position and provides methods
    to add styled content to the PDF. It does not handle page breaks itself.
    """
    def __init__(self, canvas, page_size, style_manager, padding_h, padding_v):
        self.canvas = canvas
        self.page_size = page_size
        self.style_manager = style_manager
        self.padding_h = padding_h
        self.padding_v = padding_v
        self.current_pos = 0.0
        self.page_num = 1

    def start_from(self, pos: float):
        """Sets the vertical starting position (from top) for the next element."""
        self.current_pos = float(pos)
        return self

    def add_spacing(self, spacing: float):
        """Adds vertical empty space."""
        self.current_pos += float(spacing)
        return self

    def _draw_paragraph(self, text: str, style):
        """Private helper to draw a styled paragraph and return its height."""
        width = self.page_size[0] - 2 * self.padding_h
        y_pos = self.page_size[1] - self.current_pos

        p = Paragraph(text, style)
        w, h = p.wrap(width, 10000) # Use a large available height to get true height
        p.drawOn(self.canvas, self.padding_h, y_pos - h)

        self.current_pos += h
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

    def get_paragraph_height(self, text: str, **kwargs) -> float:
        """Calculates the height of a paragraph without drawing it."""
        # Kiemeljük a style_name-et a kwargs-ból, alapértelmezett a 'paragraph_default'
        style_name = kwargs.pop('style_name', 'paragraph_default')
        style = self.style_manager.prepare_style(style_name, **kwargs)
        width = self.page_size[0] - 2 * self.padding_h
        p = Paragraph(text, style)
        _w, h = p.wrap(width, 10000)
        return h

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
        y = self.padding_v # A vonal y pozíciója az oldal aljától

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
        """Létrehoz egy Paragraph objektumot anélkül, hogy kirajzolná."""
        style_name = kwargs.pop('style_name', 'paragraph_default')
        style = self.style_manager.prepare_style(style_name, **kwargs)
        return Paragraph(text, style)

    def draw_paragraph_object(self, p: Paragraph):
        """Kirajzol egy már létező Paragraph objektumot az aktuális pozícióra."""
        width = self.page_size[0] - 2 * self.padding_h
        _w, h = p.wrap(width, 10000)

        y_pos = self.page_size[1] - self.current_pos
        p.drawOn(self.canvas, self.padding_h, y_pos - h)
        self.current_pos += h
        return self