from reportlab.platypus.paragraph import Paragraph
from src.logger import logger

class TextBuilder:
    """Handles ONLY text: paragraphs, titles, subtitles."""

    def __init__(self, canvas, page_size, style_manager, config):
        self.canvas = canvas
        self.page_size = page_size
        self.style_manager = style_manager
        self.config = config
        self.padding_h = config.get("common.padding.horizontal")

    def add_paragraph(self, text: str, current_pos: float, **kwargs) -> float:
        """Add paragraph, return new position."""
        style_name = kwargs.pop('style_name', 'paragraph_default')
        style = self.style_manager.prepare_style(style_name, **kwargs)
        return self._draw_paragraph(text, style, current_pos)

    def add_title(self, text: str, current_pos: float, **kwargs) -> float:
        """Add title, return new position."""
        style = self.style_manager.prepare_style('title_main', **kwargs)
        return self._draw_paragraph(text, style, current_pos)

    def add_subtitle(self, text: str, current_pos: float, **kwargs) -> float:
        """Add subtitle, return new position."""
        style = self.style_manager.prepare_style('title_sub', **kwargs)
        return self._draw_paragraph(text, style, current_pos + 6)

    def create_paragraph(self, text: str, **kwargs) -> Paragraph:
        """Create Paragraph object without drawing."""
        style_name = kwargs.pop('style_name', 'paragraph_default')
        style = self.style_manager.prepare_style(style_name, **kwargs)
        return Paragraph(text, style)

    def draw_paragraph_object(self, paragraph: Paragraph, current_pos: float) -> float:
        """Draw existing Paragraph object."""
        width = self.page_size[0] - 2 * self.padding_h
        _, height = paragraph.wrap(width, 10000)

        y_pos = self.page_size[1] - current_pos - height
        paragraph.drawOn(self.canvas, self.padding_h, y_pos)

        return current_pos + height

    def get_paragraph_height(self, text: str, **kwargs) -> float:
        """Calculate paragraph height without drawing."""
        paragraph = self.create_paragraph(text, **kwargs)
        width = self.page_size[0] - 2 * self.padding_h
        _, height = paragraph.wrap(width, 10000)
        return height

    def _draw_paragraph(self, text: str, style, current_pos: float) -> float:
        """Internal helper to draw paragraph."""
        width = self.page_size[0] - 2 * self.padding_h
        paragraph = Paragraph(text, style)
        _, height = paragraph.wrap(width, 10000)

        y_pos = self.page_size[1] - current_pos - height
        paragraph.drawOn(self.canvas, self.padding_h, y_pos)

        return current_pos + height
