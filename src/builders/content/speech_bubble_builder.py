from .textbox_builder import TextBoxBuilder
from src.logger import logger

class SpeechBubbleBuilder(TextBoxBuilder):
    """
    Specialized builder for speech bubbles, extends TextBoxBuilder.
    Handles avatar + text layout with rounded corners.
    """

    def add_speech_bubble(self, bubble_data: dict, current_pos: float) -> float:
        """
        Add a speech bubble with avatar and text.
        Returns new position after the bubble.
        """
        try:
            # SAVE current canvas state
            self.canvas.saveState()

            # Process speech bubble specific layout
            processed_data = self._process_speech_bubble_layout(bubble_data)

            # Use parent TextBoxBuilder to draw the actual box
            result_pos = super().add_textbox(processed_data, current_pos)

            # RESTORE canvas state
            self.canvas.restoreState()

            return result_pos

        except Exception as e:
            # ALWAYS restore state even on error
            self.canvas.restoreState()
            logger.error(f"Failed to add speech bubble: {e}")
            return current_pos + 50

    def _process_speech_bubble_layout(self, bubble_data: dict) -> dict:
        """
        Convert speech bubble data to textbox format with proper layout.
        """
        # Default speech bubble settings
        processed = {
            'type': 'textbox',
            'height': bubble_data.get('height', 150),
            'width': bubble_data.get('width', '100%'),
            'alignment': bubble_data.get('alignment', 'left'),
            'background_color': bubble_data.get('background_color', 'lightblue'),
            'border_color': bubble_data.get('border_color', 'blue'),
            'border_width': bubble_data.get('border_width', 2),
            'border_radius': bubble_data.get('border_radius', 10),
            'padding_top': bubble_data.get('padding_top', 25),
            'padding_bottom': bubble_data.get('padding_bottom', 25),
            'padding_left': bubble_data.get('padding_left', 25),
            'padding_right': bubble_data.get('padding_right', 25),
            'margin_top': bubble_data.get('margin_top', 5),
            'margin_bottom': bubble_data.get('margin_bottom', 5)
        }

        # Process content based on bubble type
        bubble_type = bubble_data.get('bubble_type', 'left')  # 'left' or 'right'
        avatar_src = bubble_data.get('avatar_src')
        text = bubble_data.get('text', '')

        if bubble_type == 'left':
            # Avatar on left, text on right
            processed['content'] = self._create_left_bubble_content(avatar_src, text, bubble_data)
        else:
            # Text on left, avatar on right
            processed['content'] = self._create_right_bubble_content(avatar_src, text, bubble_data)

        return processed

    def _create_left_bubble_content(self, avatar_src: str, text: str, bubble_data: dict) -> list:
        """Create content layout for left-aligned bubble (avatar left, text right)."""
        content = []

        # Add avatar image
        if avatar_src:
            avatar_config = {
                'type': 'image',
                'src': avatar_src,
                'width': bubble_data.get('avatar_size', 100),
                'height': bubble_data.get('avatar_size', 100),
                'alignment': 'left'
            }
            content.append(avatar_config)

        # Add text with proper styling
        if text:
            text_config = {
                'type': 'text',
                'text': text,
                'font_size': bubble_data.get('text_size', 14),
                'font_weight': bubble_data.get('text_weight', 'Regular'),
                'text_color': bubble_data.get('text_color', 'black'),
                'text_align': 'left'
            }
            content.append(text_config)

        return content

    def _create_right_bubble_content(self, avatar_src: str, text: str, bubble_data: dict) -> list:
        """Create content layout for right-aligned bubble (text left, avatar right)."""
        content = []

        # Add text first (will appear on left)
        if text:
            text_config = {
                'type': 'text',
                'text': text,
                'font_size': bubble_data.get('text_size', 14),
                'font_weight': bubble_data.get('text_weight', 'Regular'),
                'text_color': bubble_data.get('text_color', 'black'),
                'text_align': 'right'
            }
            content.append(text_config)

        # Add avatar image (will appear on right)
        if avatar_src:
            avatar_config = {
                'type': 'image',
                'src': avatar_src,
                'width': bubble_data.get('avatar_size', 100),
                'height': bubble_data.get('avatar_size', 100),
                'alignment': 'right'
            }
            content.append(avatar_config)

        return content

    def estimate_speech_bubble_height(self, bubble_data: dict) -> float:
        """Estimate speech bubble height without drawing."""
        processed_data = self._process_speech_bubble_layout(bubble_data)
        return super().estimate_textbox_height(processed_data)