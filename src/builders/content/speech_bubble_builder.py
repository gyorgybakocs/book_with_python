from .textbox_builder import TextBoxBuilder
from src.logger import logger
from reportlab.platypus import Table, TableStyle, Paragraph, Image
from reportlab.lib.utils import ImageReader
from reportlab.graphics.shapes import Drawing, Rect
import os

class SpeechBubbleBuilder(TextBoxBuilder):
    """
    Specialized builder for speech bubbles.
    This version includes fixes for padding between avatar and text,
    and correct text alignment for right-aligned bubbles.
    """

    def add_speech_bubble(self, bubble_data: dict, current_pos: float) -> float:
        """Add a speech bubble with avatar and text, with correct layout."""
        try:
            self.canvas.saveState()

            # 1. Calculate overall box properties
            box_width = self._calculate_box_width(bubble_data.get('width', '100%'))
            x_pos = self._calculate_x_position(box_width, bubble_data.get('alignment', 'left'))

            padding = {
                'top': bubble_data.get('padding_top', 15), 'bottom': bubble_data.get('padding_bottom', 15),
                'left': bubble_data.get('padding_left', 15), 'right': bubble_data.get('padding_right', 15)
            }
            content_width = box_width - padding['left'] - padding['right']

            # 2. Create the internal layout table (Image + Spacer + Text)
            layout_table = self._create_layout_table(bubble_data, content_width)

            # 3. Calculate height
            _, table_height = layout_table.wrapOn(self.canvas, content_width, self.page_size[1])
            total_height = table_height + padding['top'] + padding['bottom']
            min_height = bubble_data.get('min_height')
            if min_height and total_height < min_height: total_height = min_height

            # 4. Draw the main bubble frame (background and rounded border)
            box_y = self.page_size[1] - current_pos - total_height
            self._draw_box_frame(x_pos, box_y, box_width, total_height, bubble_data)

            # 5. Draw the layout table inside the frame
            table_x = x_pos + padding['left']
            table_y = box_y + padding['bottom']
            layout_table.drawOn(self.canvas, table_x, table_y)

            self.canvas.restoreState()
            return current_pos + total_height + bubble_data.get('margin_bottom', 5)

        except Exception as e:
            self.canvas.restoreState()
            logger.error(f"Failed to add speech bubble: {e}", exc_info=True)
            return current_pos + 50

    def _create_layout_table(self, bubble_data: dict, content_width: float) -> Table:
        """Creates a 1x3 invisible table to manage layout with spacing."""
        bubble_type = bubble_data.get('bubble_type', 'left')
        avatar_src = bubble_data.get('avatar_src')
        text = bubble_data.get('text', '')
        avatar_size = bubble_data.get('avatar_size', 80)
        spacing = 10 # Space between avatar and text

        # --- Create Image Flowable ---
        image_flowable = None
        if avatar_src:
            image_path = os.path.join(self.images_path, avatar_src)
            if os.path.exists(image_path):
                image_flowable = Image(image_path, width=avatar_size, height=avatar_size)
            else:
                logger.warning(f"Avatar image not found: {image_path}")
                image_flowable = self._create_placeholder(avatar_size, avatar_size, bubble_data.get('border_color', 'red'))

        # --- Create Text Paragraph Flowable ---
        text_width = content_width - avatar_size - spacing

        # --- FIX for Text Alignment ---
        # Align text to the right if the bubble is right-aligned
        text_align_value = 'right' if bubble_type == 'right' else 'left'

        style_data = {
            'font_size': bubble_data.get('text_size', 14),
            'text_color': bubble_data.get('text_color', 'black'),
            'font_weight': bubble_data.get('text_weight', 'Regular'),
            'text_align': text_align_value,
            'leading': bubble_data.get('text_size', 14) * 1.4
        }
        text_paragraph = self._create_text_element(text, text_width, style_data)['object']

        # --- Assemble Table with a spacer column ---
        # The empty string "" creates an empty spacer cell.
        if bubble_type == 'left':
            table_data = [[image_flowable, "", text_paragraph]]
            col_widths = [avatar_size, spacing, text_width]
        else: # right
            table_data = [[text_paragraph, "", image_flowable]]
            col_widths = [text_width, spacing, avatar_size]

        layout_table = Table(table_data, colWidths=col_widths, hAlign='LEFT')
        layout_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))

        return layout_table

    def _create_placeholder(self, width, height, color_str):
        d = Drawing(width, height)
        r = Rect(0, 0, width, height, stroke=None, fill=self._parse_color(color_str))
        d.add(r)
        return d

    def estimate_speech_bubble_height(self, bubble_data: dict) -> float:
        # Re-implementing this to be accurate
        try:
            box_width = self._calculate_box_width(bubble_data.get('width', '100%'))
            padding = {
                'top': bubble_data.get('padding_top', 15), 'bottom': bubble_data.get('padding_bottom', 15),
                'left': bubble_data.get('padding_left', 15), 'right': bubble_data.get('padding_right', 15)
            }
            content_width = box_width - padding['left'] - padding['right']
            layout_table = self._create_layout_table(bubble_data, content_width)
            _, table_height = layout_table.wrapOn(self.canvas, content_width, self.page_size[1])
            total_height = table_height + padding['top'] + padding['bottom']
            min_height = bubble_data.get('min_height')
            if min_height and total_height < min_height: total_height = min_height
            return total_height + bubble_data.get('margin_bottom', 5)
        except Exception as e:
            logger.error(f"Failed to estimate speech bubble height: {e}")
            return 150
