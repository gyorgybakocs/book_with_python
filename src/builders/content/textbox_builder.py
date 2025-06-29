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
            # SAVE current canvas state before modifying
            self.canvas.saveState()

            # Calculate box dimensions
            box_width = self._calculate_box_width(textbox_data.get('width', '100%'))
            x_pos = self._calculate_x_position(box_width, textbox_data.get('alignment', 'left'))

            # Get styling
            background_color = self._parse_color(textbox_data.get('background_color'))
            border_color = self._parse_color(textbox_data.get('border_color', 'black'))
            border_width = textbox_data.get('border_width', 1.0)

            # Get padding
            padding = {
                'top': textbox_data.get('padding_top', 8),
                'bottom': textbox_data.get('padding_bottom', 8),
                'left': textbox_data.get('padding_left', 8),
                'right': textbox_data.get('padding_right', 8)
            }

            # Process content and calculate required height
            content_height, content_elements = self._process_content(
                textbox_data.get('content', []),
                box_width - padding['left'] - padding['right'],
                textbox_data
            )

            # Calculate total box height
            total_height = content_height + padding['top'] + padding['bottom']

            # Apply min/max height constraints
            min_height = textbox_data.get('min_height')
            max_height = textbox_data.get('max_height')
            if min_height and total_height < min_height:
                total_height = min_height
            if max_height and total_height > max_height:
                total_height = max_height

            # Draw the box background and border
            box_y = self.page_size[1] - current_pos - total_height
            self._draw_box_frame(x_pos, box_y, box_width, total_height,
                                 background_color, border_color, border_width)

            # Draw the content inside the box
            content_y_start = current_pos + padding['top']
            self._draw_content_elements(content_elements, x_pos + padding['left'],
                                        content_y_start, box_width - padding['left'] - padding['right'])

            # RESTORE canvas state to original
            self.canvas.restoreState()

            # Add margins
            margin_top = textbox_data.get('margin_top', 5)
            margin_bottom = textbox_data.get('margin_bottom', 5)

            return current_pos + total_height + margin_bottom

        except Exception as e:
            # ALWAYS restore state even on error
            self.canvas.restoreState()
            logger.error(f"Failed to add text box: {e}")
            return current_pos + 50

    def _calculate_box_width(self, width_spec) -> float:
        """Calculate box width from specification."""
        available_width = self.page_size[0] - 2 * self.padding_h

        if isinstance(width_spec, str) and width_spec.endswith('%'):
            percentage = float(width_spec.rstrip('%')) / 100
            return available_width * percentage
        elif isinstance(width_spec, (int, float)):
            return float(width_spec)
        else:
            return available_width

    def _calculate_x_position(self, box_width: float, alignment: str) -> float:
        """Calculate X position based on alignment."""
        available_width = self.page_size[0] - 2 * self.padding_h

        if alignment == "center":
            return self.padding_h + (available_width - box_width) / 2
        elif alignment == "right":
            return self.page_size[0] - self.padding_h - box_width
        else:  # left
            return self.padding_h

    def _parse_color(self, color_spec):
        """Parse color specification using style manager."""
        if not color_spec:
            return None
        return self.style_manager._parse_color(color_spec)

    def _process_content(self, content_list, content_width, textbox_data) -> tuple:
        """
        Process mixed content and calculate total height.
        Uses StyleManager and FontManager registered fonts only.
        """
        content_elements = []
        total_height = 0

        # Default text styling from textbox - only use registered fonts
        main_font = self.config.get("fonts.main")  # FontManager already registered this
        default_size = textbox_data.get('font_size', 12)
        default_weight = textbox_data.get('font_weight', 'Regular')
        default_color = textbox_data.get('text_color', 'black')
        default_align = textbox_data.get('text_align', 'left')
        default_leading = textbox_data.get('line_height', 1.2) * default_size

        for item in content_list:
            if isinstance(item, str):
                # Simple text content
                element = self._create_text_element(
                    item, content_width, main_font, default_size,
                    default_weight, default_color, default_align, default_leading
                )
                content_elements.append(element)
                total_height += element['height']

            elif isinstance(item, dict):
                if item.get('type') == 'text':
                    # Styled text content - always use main font (FontManager registered)
                    size = item.get('font_size', default_size)
                    weight = item.get('font_weight', default_weight)
                    color = item.get('text_color', default_color)
                    align = item.get('text_align', default_align)
                    leading = item.get('line_height', size * 1.2)

                    element = self._create_text_element(
                        item.get('text', ''), content_width, main_font, size,
                        weight, color, align, leading
                    )
                    content_elements.append(element)
                    total_height += element['height']

                elif item.get('type') == 'image':
                    # Embedded image
                    element = self._create_image_element(item, content_width)
                    content_elements.append(element)
                    total_height += element['height']

                else:
                    logger.warning(f"Unknown content type in textbox: {item.get('type')}")

            # Add spacing between elements
            total_height += 3

        return total_height, content_elements

    def _create_text_element(self, text, width, font, size, weight, color, align, leading):
        """Create a text element with specified styling using StyleManager."""
        # Use the existing style manager system
        alignment_map = {'left': 0, 'center': 1, 'right': 2, 'justify': 4}

        # Create style using StyleManager.prepare_style() - this ensures proper font registration
        style_kwargs = {
            'fontSize': size,
            'leading': leading,
            'alignment': alignment_map.get(align, 0),
            'textColor': self.style_manager._parse_color(color)
        }

        # Only modify fontName if weight is different from Regular
        # StyleManager handles the registered font names properly
        if weight and weight != 'Regular':
            main_font = self.config.get("fonts.main")  # This is already registered by FontManager
            style_kwargs['fontName'] = f'{main_font}-{weight}'

        # Use StyleManager to create the style - it knows about registered fonts
        style = self.style_manager.prepare_style('paragraph_default', **style_kwargs)

        paragraph = Paragraph(text, style)
        _, height = paragraph.wrap(width, 10000)

        return {
            'type': 'text',
            'paragraph': paragraph,
            'height': height,
            'width': width
        }

    def _create_image_element(self, image_data, content_width):
        """Create an image element for textbox content."""
        src = image_data.get('src')
        width = image_data.get('width', 100)
        height = image_data.get('height', 'auto')
        alignment = image_data.get('alignment', 'left')
        caption = image_data.get('caption')

        # Calculate dimensions (simplified version)
        if isinstance(width, str) and width.endswith('%'):
            percentage = float(width.rstrip('%')) / 100
            img_width = content_width * percentage
        else:
            img_width = min(float(width), content_width)

        # Estimate height (you can improve this with actual image loading)
        if height == 'auto':
            img_height = img_width * 0.75  # Default aspect ratio
        else:
            img_height = float(height)

        caption_height = 15 if caption else 0
        total_height = img_height + caption_height + 5

        return {
            'type': 'image',
            'src': src,
            'width': img_width,
            'height': total_height,
            'img_height': img_height,
            'alignment': alignment,
            'caption': caption
        }

    def _draw_box_frame(self, x, y, width, height, bg_color, border_color, border_width):
        """Draw the background and border of the text box."""
        # Draw background
        if bg_color:
            self.canvas.setFillColor(bg_color)
            self.canvas.rect(x, y, width, height, stroke=0, fill=1)

        # Draw border
        if border_color and border_width > 0:
            self.canvas.setStrokeColor(border_color)
            self.canvas.setLineWidth(border_width)
            self.canvas.rect(x, y, width, height, stroke=1, fill=0)

    def _draw_content_elements(self, elements, x_start, y_start, content_width):
        """Draw all content elements inside the text box."""
        current_y = y_start

        for element in elements:
            if element['type'] == 'text':
                # Draw text paragraph
                y_pos = self.page_size[1] - current_y - element['height']
                element['paragraph'].drawOn(self.canvas, x_start, y_pos)
                current_y += element['height']

            elif element['type'] == 'image':
                # Draw image
                self._draw_textbox_image(element, x_start, current_y, content_width)
                current_y += element['height']

            current_y += 3  # Spacing between elements

    def _draw_textbox_image(self, image_element, x_start, current_y, content_width):
        """Draw an image inside a text box."""
        try:
            # SAVE state before modifying canvas for image
            self.canvas.saveState()

            image_path = os.path.join(self.images_path, image_element['src'])
            if not os.path.exists(image_path):
                logger.warning(f"Image not found: {image_path}")
                self.canvas.restoreState()
                return

            img_width = image_element['width']
            img_height = image_element['img_height']

            # Calculate X position based on alignment
            if image_element['alignment'] == 'center':
                x_pos = x_start + (content_width - img_width) / 2
            elif image_element['alignment'] == 'right':
                x_pos = x_start + content_width - img_width
            else:
                x_pos = x_start

            # Draw image
            y_pos = self.page_size[1] - current_y - img_height
            img_reader = ImageReader(image_path)
            self.canvas.drawImage(img_reader, x_pos, y_pos, width=img_width, height=img_height)

            # Draw caption if present
            if image_element.get('caption'):
                from reportlab.lib import colors
                caption_y = y_pos - 15
                self.canvas.setFont("Helvetica", 9)
                self.canvas.setFillColor(colors.black)
                caption_x = x_start + (content_width - len(image_element['caption']) * 4) / 2
                self.canvas.drawString(caption_x, caption_y, image_element['caption'])

            # RESTORE state after image drawing
            self.canvas.restoreState()

        except Exception as e:
            # ALWAYS restore state even on error
            self.canvas.restoreState()
            logger.error(f"Failed to draw textbox image {image_element['src']}: {e}")

    def estimate_textbox_height(self, textbox_data: dict) -> float:
        """Estimate textbox height without drawing."""
        try:
            box_width = self._calculate_box_width(textbox_data.get('width', '100%'))
            padding = {
                'top': textbox_data.get('padding_top', 8),
                'bottom': textbox_data.get('padding_bottom', 8),
                'left': textbox_data.get('padding_left', 8),
                'right': textbox_data.get('padding_right', 8)
            }

            content_height, _ = self._process_content(
                textbox_data.get('content', []),
                box_width - padding['left'] - padding['right'],
                textbox_data
            )

            total_height = content_height + padding['top'] + padding['bottom']

            # Apply min/max height constraints
            min_height = textbox_data.get('min_height')
            max_height = textbox_data.get('max_height')
            if min_height and total_height < min_height:
                total_height = min_height
            if max_height and total_height > max_height:
                total_height = max_height

            margin_bottom = textbox_data.get('margin_bottom', 5)
            return total_height + margin_bottom

        except Exception:
            return 100  # Default estimate
