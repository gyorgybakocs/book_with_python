from reportlab.platypus.paragraph import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT

class ListBuilder:
    """Handles the creation of nested lists with improved styling."""

    def __init__(self, canvas, page_size, style_manager, config):
        self.canvas = canvas
        self.page_size = page_size
        self.style_manager = style_manager
        self.config = config
        self.padding_h = config.get("common.padding.horizontal")

    def add_list(self, items: list, current_pos: float, **kwargs) -> float:
        """Public method to start drawing a list."""
        return self._draw_list_level(items, current_pos, 0)

    def _draw_list_level(self, items: list, current_pos: float, level: int) -> float:
        """
        Recursively draws list items. Increased level means deeper nesting.
        Now with improved styling for bullets and indentation.
        """
        y_pos = current_pos
        base_style = self.style_manager.prepare_style('paragraph_default', fontSize=12, leading=16)

        # Define bullet characters per level. Replaced open circle with a more reliable en-dash.
        bullets = ['•', '–', '▪']
        bullet_char = bullets[level] if level < len(bullets) else bullets[-1]

        # New indentation logic for a smaller gap
        base_indent = 20
        text_indent = base_indent * (level + 1) # e.g., Level 0 -> 20, Level 1 -> 40
        bullet_indent = text_indent - 10        # Place bullet 10 points before the text starts

        for item in items:
            item_text = ""
            sub_items = None

            if isinstance(item, dict):
                item_text = item.get('text', '')
                sub_items = item.get('sub_items')
            elif isinstance(item, str):
                item_text = item

            # Create style for the current list item
            item_style = ParagraphStyle(
                name=f"list-level-{level}",
                parent=base_style,
                leftIndent=text_indent,
                bulletIndent=bullet_indent,
                # firstLineIndent is set to 0 to rely on the clean indent logic above
                firstLineIndent=0,
                bulletText=bullet_char,
                # Set bullet font size to be smaller than the text
                bulletFontSize=base_style.fontSize * 0.8,
            )

            paragraph = Paragraph(item_text, item_style)

            # Draw the paragraph (list item)
            width = self.page_size[0] - 2 * self.padding_h
            _, height = paragraph.wrap(width, 10000)

            draw_y_pos = self.page_size[1] - y_pos - height
            paragraph.drawOn(self.canvas, self.padding_h, draw_y_pos)
            y_pos += height + 4

            # If there are sub-items, recursively call this function for the next level
            if sub_items:
                # Add a little extra space before a nested list
                y_pos += 4
                y_pos = self._draw_list_level(sub_items, y_pos, level + 1)

        # Add extra space after a sublist is finished
        if level > 0:
            y_pos += 5

        return y_pos

    def estimate_list_height(self, items: list, level: int = 0) -> float:
        """Recursively estimates the total height of a list."""
        total_height = 0
        style = self.style_manager.prepare_style('paragraph_default', fontSize=12, leading=16)
        width = self.page_size[0] - 2 * self.padding_h

        for item in items:
            item_text = ""
            sub_items = None
            if isinstance(item, dict):
                item_text = item.get('text', '')
                sub_items = item.get('sub_items')
            elif isinstance(item, str):
                item_text = item

            p = Paragraph(item_text, style)
            _, height = p.wrap(width, 10000)
            total_height += height + 4

            if sub_items:
                total_height += 4 # Space before nested list
                total_height += self.estimate_list_height(sub_items, level + 1)

        if level > 0:
            total_height += 5 # Space after nested list

        return total_height
