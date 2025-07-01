from reportlab.platypus.paragraph import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT

class ListBuilder:
    """Handles the creation of nested lists with item-by-item drawing."""

    def __init__(self, canvas, page_size, style_manager, config):
        self.canvas = canvas
        self.page_size = page_size
        self.style_manager = style_manager
        self.config = config
        self.padding_h = config.get("common.padding.horizontal")

    def add_list_item(self, item: dict, current_pos: float, level: int = 0) -> float:
        """
        Draws a single list item and its potential sub-items recursively.
        This is the core drawing method called by ChapterBuilder for each item.
        """
        y_pos = current_pos
        base_style = self.style_manager.prepare_style('paragraph_default', fontSize=12, leading=16)

        bullets = ['•', '–', '▪']
        bullet_char = bullets[level] if level < len(bullets) else bullets[-1]

        base_indent = 20
        text_indent = base_indent * (level + 1)
        bullet_indent = text_indent - 10

        item_text = item.get('text', '')
        sub_items = item.get('sub_items')

        item_style = ParagraphStyle(
            name=f"list-level-{level}", parent=base_style,
            leftIndent=text_indent, bulletIndent=bullet_indent,
            firstLineIndent=0, bulletText=bullet_char,
            bulletFontSize=base_style.fontSize * 0.8,
        )

        paragraph = Paragraph(item_text, item_style)

        width = self.page_size[0] - 2 * self.padding_h
        _, height = paragraph.wrap(width, 10000)

        draw_y_pos = self.page_size[1] - y_pos - height
        paragraph.drawOn(self.canvas, self.padding_h, draw_y_pos)
        y_pos += height + 4

        if sub_items:
            y_pos += 4
            # Call recursively for sub-items
            for sub_item_text in sub_items:
                # Sub-items are drawn as a new level
                y_pos = self.add_list_item({'text': sub_item_text}, y_pos, level + 1)

        return y_pos

    def estimate_list_item_height(self, item: dict, level: int = 0) -> float:
        """Recursively estimates the total height of a single list item and its children."""
        total_height = 0
        style = self.style_manager.prepare_style('paragraph_default', fontSize=12, leading=16)
        width = self.page_size[0] - 2 * self.padding_h

        item_text = item.get('text', '')
        sub_items = item.get('sub_items')

        p = Paragraph(item_text, style)
        _, height = p.wrap(width, 10000)
        total_height += height + 4

        if sub_items:
            total_height += 4 # Space before nested list
            for sub_item_text in sub_items:
                total_height += self.estimate_list_item_height({'text': sub_item_text}, level + 1)

        return total_height
