import os
from reportlab.lib.utils import ImageReader
from src.logger import logger

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

class ImageBuilder:
    """Handles ONLY images with sizing and captions."""

    def __init__(self, canvas, page_size, style_manager, config):
        self.canvas = canvas
        self.page_size = page_size
        self.style_manager = style_manager
        self.config = config
        self.padding_h = config.get("common.padding.horizontal")
        self.images_path = config.get("paths.resources") + "/images"

    def add_image(self, src: str, current_pos: float, alignment: str = "center",
                  width=300, height="auto", caption: str = None) -> float:
        """Add image, return new position."""
        image_path = os.path.join(self.images_path, src)

        if not os.path.exists(image_path):
            logger.warning(f"Image not found: {image_path}")
            return current_pos + 20

        if not PIL_AVAILABLE:
            logger.warning(f"PIL not available for image: {src}")
            return current_pos + 20

        try:
            width_points, height_points = self._calculate_dimensions(src, width, height)
            x_pos = self._calculate_x_position(width_points, alignment)

            # Draw image
            y_pos = self.page_size[1] - current_pos - height_points
            img_reader = ImageReader(image_path)
            self.canvas.drawImage(img_reader, x_pos, y_pos,
                                  width=width_points, height=height_points)

            new_pos = current_pos + height_points + 5

            # Add caption if present
            if caption:
                new_pos = self._add_caption(caption, new_pos)

            return new_pos + 10

        except Exception as e:
            logger.error(f"Failed to add image {src}: {e}")
            return current_pos + 20

    def estimate_image_height(self, src: str, width=300, height="auto",
                              caption: str = None) -> float:
        """Estimate image height without drawing."""
        try:
            width_points, height_points = self._calculate_dimensions(src, width, height)
            caption_height = 25 if caption else 0
            return height_points + caption_height + 15
        except Exception:
            return 200  # Default estimate

    def _calculate_dimensions(self, src: str, width, height) -> tuple[float, float]:
        """Calculate final image dimensions in points."""
        available_width = self.page_size[0] - 2 * self.padding_h
        aspect_ratio = self._get_aspect_ratio(src)

        # Handle percentage values
        if isinstance(width, str) and width.endswith('%'):
            percentage = float(width.rstrip('%')) / 100
            width_points = available_width * percentage
            height_points = width_points * aspect_ratio
        elif isinstance(height, str) and height.endswith('%') and height != "auto":
            percentage = float(height.rstrip('%')) / 100
            max_height = self.page_size[1] - 100  # Leave some margin
            height_points = max_height * percentage
            width_points = height_points / aspect_ratio
        else:
            # Pixel-based sizing
            width_points = width * 0.75 if isinstance(width, (int, float)) else 225
            if height == "auto":
                height_points = width_points * aspect_ratio
            else:
                height_points = height * 0.75 if isinstance(height, (int, float)) else width_points * aspect_ratio

        # Ensure it fits available space
        if width_points > available_width:
            scale = available_width / width_points
            width_points = available_width
            height_points *= scale

        return width_points, height_points

    def _get_aspect_ratio(self, src: str) -> float:
        """Get real aspect ratio from image file."""
        try:
            image_path = os.path.join(self.images_path, src)
            if os.path.exists(image_path):
                with Image.open(image_path) as img:
                    width, height = img.size
                    return height / width
        except Exception:
            pass
        return 0.75  # Default ratio

    def _calculate_x_position(self, width_points: float, alignment: str) -> float:
        """Calculate X position based on alignment."""
        available_width = self.page_size[0] - 2 * self.padding_h

        if alignment == "center":
            return self.padding_h + (available_width - width_points) / 2
        elif alignment == "right":
            return self.page_size[0] - self.padding_h - width_points
        else:  # left
            return self.padding_h

    def _add_caption(self, caption: str, current_pos: float) -> float:
        """Add image caption."""
        from reportlab.platypus.paragraph import Paragraph

        caption_style = self.style_manager.prepare_style('paragraph_default',
                                                         fontSize=10, alignment=1)
        caption_p = Paragraph(f"<i>{caption}</i>", caption_style)
        width = self.page_size[0] - 2 * self.padding_h
        _, caption_height = caption_p.wrap(width, 50)

        y_pos = self.page_size[1] - current_pos - caption_height
        caption_p.drawOn(self.canvas, self.padding_h, y_pos)

        return current_pos + caption_height + 5
