from reportlab.platypus.paragraph import Paragraph
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.lib.styles import ParagraphStyle
from src.logger import logger
import os

class TextBoxBuilder:
    """Handles customizable text boxes with backgrounds, borders, and mixed content."""

    def __init__(self, canvas, page_size, style_manager, config):
        self.canvas = canvas
        self.page_size = page_size
        self.style_manager = style_manager
        self.config = config
        self.padding_h = config.get("common.padding.horizontal")
        self.images_path = config.get("paths.resources") + "/images"

    def add_textbox(self, textbox_data: dict, current_pos: float) -> float:
        """
        Add a customizable text box with mixed content.
        Returns new position after the text box.
        """
        try:
            self.canvas.saveState()

            box_width = self._calculate_box_width(textbox_data.get('width', '100%'))
            x_pos = self._calculate_x_position(box_width, textbox_data.get('alignment', 'left'))

            padding = {
                'top': textbox_data.get('padding_top', 8), 'bottom': textbox_data.get('padding_bottom', 8),
                'left': textbox_data.get('padding_left', 8), 'right': textbox_data.get('padding_right', 8)
            }

            content_height, content_elements = self._process_content(
                textbox_data.get('content', []),
                box_width - padding['left'] - padding['right'],
                textbox_data
            )

            total_height = content_height + padding['top'] + padding['bottom']
            min_height = textbox_data.get('min_height')
            if min_height and total_height < min_height: total_height = min_height

            box_y = self.page_size[1] - current_pos - total_height
            self._draw_box_frame(x_pos, box_y, box_width, total_height, textbox_data)

            content_y_start = box_y + total_height - padding['top']
            self._draw_content_elements(content_elements, x_pos + padding['left'], content_y_start)

            self.canvas.restoreState()
            return current_pos + total_height + textbox_data.get('margin_bottom', 5)

        except Exception as e:
            self.canvas.restoreState()
            logger.error(f"Failed to add text box: {e}", exc_info=True)
            return current_pos + 50

    # --- NEW METHOD ADDED TO FIX THE ATTRIBUTEERROR ---
    def estimate_textbox_height(self, textbox_data: dict) -> float:
        """Estimate textbox height without drawing for page break calculations."""
        try:
            box_width = self._calculate_box_width(textbox_data.get('width', '100%'))
            padding = {'top': textbox_data.get('padding_top', 8), 'bottom': textbox_data.get('padding_bottom', 8),
                       'left': textbox_data.get('padding_left', 8), 'right': textbox_data.get('padding_right', 8)}

            content_width = box_width - padding['left'] - padding['right']
            content_height, _ = self._process_content(textbox_data.get('content', []), content_width, textbox_data)

            total_height = content_height + padding['top'] + padding['bottom']
            min_height = textbox_data.get('min_height')
            if min_height and total_height < min_height: total_height = min_height

            return total_height + textbox_data.get('margin_bottom', 5)
        except Exception as e:
            logger.error(f"Failed to estimate textbox height: {e}")
            return 100 # Return a default fallback height

    def _draw_box_frame(self, x, y, width, height, textbox_data):
        """Draw the background and border of the text box, with rounded corners support."""
        bg_color = self._parse_color(textbox_data.get('background_color'))
        border_color = self._parse_color(textbox_data.get('border_color', 'black'))
        border_width = textbox_data.get('border_width', 1.0)
        border_radius = textbox_data.get('border_radius', 0)

        self.canvas.saveState()
        if bg_color:
            self.canvas.setFillColor(bg_color)
            self.canvas.roundRect(x, y, width, height, radius=border_radius, stroke=0, fill=1)

        if border_color and border_width > 0:
            self.canvas.setStrokeColor(border_color)
            self.canvas.setLineWidth(border_width)
            self.canvas.roundRect(x, y, width, height, radius=border_radius, stroke=1, fill=0)
        self.canvas.restoreState()

    def _process_content(self, content_list, content_width, textbox_data):
        content_elements = []
        total_height = 0
        for item in content_list:
            element = None
            if isinstance(item, str):
                element = self._create_text_element(item, content_width, textbox_data)
            elif isinstance(item, dict):
                content_type = item.get('type')
                if content_type == 'text':
                    element = self._create_text_element(item.get('text', ''), content_width, {**textbox_data, **item})
                elif content_type == 'image':
                    element = self._create_image_element(item, content_width)

            if element:
                content_elements.append(element)
                total_height += element['height'] + 3 # Add spacing
        return total_height, content_elements

    def _create_text_element(self, text, width, style_data):
        alignment_map = {'left': 0, 'center': 1, 'right': 2, 'justify': 4}
        size = style_data.get('font_size', 12)
        font_name = f'{self.config.get("fonts.main")}-{style_data.get("font_weight", "Regular")}'

        style = self.style_manager.prepare_style('paragraph_default',
                                                 fontSize=size,
                                                 leading=style_data.get('leading', size * 1.2),
                                                 alignment=alignment_map.get(style_data.get('text_align', 'left'), 0),
                                                 textColor=self._parse_color(style_data.get('text_color', 'black')),
                                                 fontName=font_name
                                                 )
        paragraph = Paragraph(text, style)
        _, height = paragraph.wrapOn(self.canvas, width, 10000)
        return {'type': 'text', 'object': paragraph, 'height': height}

    def _create_image_element(self, image_data, content_width):
        # This is a simplified image processing, can be expanded
        img_width = self._calculate_box_width(image_data.get('width', 100))
        img_height = image_data.get('height', 100)
        return {'type': 'image', 'data': image_data, 'height': img_height, 'width': img_width}

    def _draw_content_elements(self, elements, x_start, y_start):
        current_y = y_start
        for element in elements:
            if element['type'] == 'text':
                current_y -= element['height']
                element['object'].drawOn(self.canvas, x_start, current_y)
                current_y -= 3

    def _calculate_box_width(self, width_spec) -> float:
        available_width = self.page_size[0] - 2 * self.padding_h
        if isinstance(width_spec, str) and width_spec.endswith('%'):
            return available_width * (float(width_spec.rstrip('%')) / 100)
        return float(width_spec)

    def _calculate_x_position(self, box_width: float, alignment: str) -> float:
        available_width = self.page_size[0] - 2 * self.padding_h
        if alignment == "center": return self.padding_h + (available_width - box_width) / 2
        if alignment == "right": return self.page_size[0] - self.padding_h - box_width
        return self.padding_h

    def _parse_color(self, color_spec):
        return self.style_manager._parse_color(color_spec) if color_spec else None
