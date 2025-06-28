from reportlab.lib import colors
from reportlab.platypus.paragraph import Paragraph
from src.logger import logger

class LayoutBuilder:
    """Handles ONLY layout: spacing, separators, headers, footers, page breaks."""

    def __init__(self, canvas, page_size, style_manager, config):
        self.canvas = canvas
        self.page_size = page_size
        self.style_manager = style_manager
        self.config = config
        self.padding_h = config.get("common.padding.horizontal")
        self.padding_v = config.get("common.padding.vertical")

    def add_spacing(self, current_pos: float, amount: float) -> float:
        """Add vertical spacing, return new position."""
        return current_pos + amount

    def add_separator_line(self, current_pos: float) -> float:
        """Add horizontal separator line, return new position."""
        y = self.page_size[1] - current_pos
        self.canvas.line(self.padding_h, y, self.page_size[0] - self.padding_h, y)
        return current_pos + 5

    def add_header(self, text: str, page_num: int) -> None:
        """Add page header at fixed position."""
        style = self.style_manager.prepare_style('title_sub', alignment=2)
        y = self.page_size[1] - self.padding_v

        # Draw header line
        self.canvas.line(self.padding_h, y, self.page_size[0] - self.padding_h, y)

        # Draw header text
        p = Paragraph(text, style)
        p.wrapOn(self.canvas, self.page_size[0] - 2 * self.padding_h, 50)
        p.drawOn(self.canvas, self.padding_h, y + 5)

    def add_footer(self, text: str, page_num: int) -> None:
        """Add page footer at fixed position."""
        style = self.style_manager.get_style('paragraph_default')
        y = self.padding_v

        # Draw footer line
        self.canvas.line(self.padding_h, y, self.page_size[0] - self.padding_h, y)

        # Draw footer text with page number
        footer_text = f"{page_num} | {text}"
        p = Paragraph(footer_text, style)
        p.wrapOn(self.canvas, self.page_size[0] - 2 * self.padding_h, 50)
        p.drawOn(self.canvas, self.padding_h, y - 18)

    def add_blank_page(self) -> None:
        """Add completely blank page."""
        self.canvas.setFillColor(colors.white)
        self.canvas.rect(0, 0, self.page_size[0], self.page_size[1], stroke=0, fill=1)
