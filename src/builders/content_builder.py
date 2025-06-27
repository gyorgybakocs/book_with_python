from reportlab.lib import colors
from reportlab.platypus.paragraph import Paragraph
from reportlab.lib.utils import ImageReader
from reportlab.lib.units import inch
import os
from src.services.layout_service import LayoutService
from src.logger import logger

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logger.warning("PIL (Pillow) not available. Image support will be limited.")

class ContentBuilder:
    """
    Content builder with integrated layout calculations and image support.
    Page builders only see the ContentBuilder interface, not LayoutService.
    """
    def __init__(self, canvas, page_size, style_manager, config):
        self.canvas = canvas
        self.page_size = page_size
        self.style_manager = style_manager
        self.config = config
        self.padding_h = config.get("common.padding.horizontal")
        self.padding_v = config.get("common.padding.vertical")
        self.current_pos = 0.0
        self.page_num = 1

        # Get images path from config
        self.images_path = config.get("paths.resources") + "/images"

        # Internal LayoutService - page builders don't know about this
        self.layout_service = LayoutService(self, config)

    # ==========================================
    # PUBLIC API FOR PAGE BUILDERS
    # ==========================================

    def start_from(self, pos: float):
        """Sets the vertical starting position."""
        self.current_pos = float(pos)
        return self

    def add_spacing(self, spacing: float):
        """Adds vertical empty space."""
        self.current_pos += float(spacing)
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

    def add_image(self, src: str, alignment: str = "center", width = 300,
                  height = "auto", caption: str = None):
        """
        Adds an image to the document with intelligent sizing.

        Args:
            src: Image filename (from resources/images/)
            alignment: "left", "center", or "right"
            width: Image width in pixels or percentage string (e.g., "70%")
            height: Image height in pixels, "auto", or percentage string (e.g., "50%")
            caption: Optional image caption
        """
        image_path = os.path.join(self.images_path, src)

        if not os.path.exists(image_path):
            logger.warning(f"Image not found: {image_path} - skipping")
            return self

        if not PIL_AVAILABLE:
            logger.warning(f"PIL not available, cannot process image: {src} - skipping")
            return self

        try:
            # Add spacing before image
            self.add_spacing(10)

            # Load and process image
            img = Image.open(image_path)
            img_width, img_height = img.size
            aspect_ratio = img_height / img_width

            # Calculate available space
            available_width = self.page_size[0] - 2 * self.padding_h
            available_height = self.layout_service.calculate_available_space(self.current_pos + 30)

            logger.info(f"Processing image {src}: width={width} (type: {type(width)}), height={height} (type: {type(height)})")

            # Calculate final dimensions - support percentage strings and auto
            if isinstance(width, str) and width.endswith('%'):
                # Width as percentage
                percentage = float(width.rstrip('%')) / 100
                width_points = available_width * percentage
                height_points = width_points * aspect_ratio
                logger.info(f"Width percentage: {width} = {width_points:.1f} points")

                # Check if height would be too tall
                if height_points > available_height:
                    logger.info(f"Image {src}: width={width} would be too tall, scaling to fit height")
                    height_points = available_height
                    width_points = height_points / aspect_ratio

            elif isinstance(height, str) and height.endswith('%') and height != "auto":
                # Height as percentage
                percentage = float(height.rstrip('%')) / 100
                height_points = available_height * percentage
                width_points = height_points / aspect_ratio
                logger.info(f"Height percentage: {height} = {height_points:.1f} points")

                # Check if width would be too wide
                if width_points > available_width:
                    logger.info(f"Image {src}: height={height} would be too wide, scaling to fit width")
                    width_points = available_width
                    height_points = width_points * aspect_ratio

            elif width == "auto" and isinstance(height, str) and height.endswith('%'):
                # Auto width with percentage height
                percentage = float(height.rstrip('%')) / 100
                height_points = available_height * percentage
                width_points = height_points / aspect_ratio
                logger.info(f"Auto width with height {height}: {width_points:.1f}x{height_points:.1f} points")

                # Check if width would be too wide
                if width_points > available_width:
                    logger.info(f"Image {src}: auto width would be too wide, scaling to fit")
                    width_points = available_width
                    height_points = width_points * aspect_ratio

            else:
                # Normal pixel-based sizing
                width_points = width * 0.75  # Convert pixels to points

                if height == "auto":
                    height_points = width_points * aspect_ratio
                else:
                    height_points = height * 0.75

                # Check if dimensions exceed available space and scale down if needed
                if width_points > available_width:
                    scale_factor = available_width / width_points
                    width_points = available_width
                    height_points = height_points * scale_factor
                    logger.info(f"Image {src}: scaled down to fit width")

                if height_points > available_height:
                    scale_factor = available_height / height_points
                    height_points = available_height
                    width_points = width_points * scale_factor
                    logger.info(f"Image {src}: scaled down to fit height")

            # Only check page break for non-chapter content (simple chapters, etc.)
            # For main chapters, ChapterBuilder handles page breaks with headers/footers
            total_height = height_points + (25 if caption else 0) + 20

            # Don't auto-break pages in main chapters - let ChapterBuilder handle it
            # We can detect this by checking if we have headers (crude but works)
            has_headers = hasattr(self, '_in_main_chapter') and self._in_main_chapter

            if not has_headers and total_height > self.layout_service.calculate_available_space(self.current_pos):
                self.new_page()
                self.current_pos = self.padding_v
                # Recalculate available height for new page
                available_height = self.layout_service.calculate_available_space(self.current_pos + 30)

                # Re-check sizing on new page if needed
                if height_points > available_height:
                    height_points = available_height
                    width_points = height_points / aspect_ratio

            # Calculate X position based on alignment
            if alignment == "center":
                x_pos = self.padding_h + (available_width - width_points) / 2
            elif alignment == "right":
                x_pos = self.page_size[0] - self.padding_h - width_points
            else:  # left
                x_pos = self.padding_h

            # Draw image
            y_pos = self.page_size[1] - self.current_pos - height_points

            img_reader = ImageReader(image_path)
            self.canvas.drawImage(img_reader, x_pos, y_pos,
                                  width=width_points, height=height_points)

            self.current_pos += height_points + 5

            # Add caption if provided
            if caption:
                self.add_spacing(5)
                caption_style = self.style_manager.prepare_style('paragraph_default',
                                                                 fontSize=10,
                                                                 alignment=1)
                self._draw_paragraph(f"<i>{caption}</i>", caption_style)

            # Add spacing after image+caption
            self.add_spacing(10)

            logger.info(f"Successfully added image: {src} ({width_points:.0f}x{height_points:.0f} points)")

        except Exception as e:
            logger.error(f"Failed to add image {src}: {e}")

        return self

    def add_content_items(self, content_items: list):
        """
        Processes a list of content items (paragraphs and images).

        Args:
            content_items: List of content items from the new JSON structure
        """
        for item in content_items:
            if item.get('type') == 'paragraph':
                self.add_paragraph(item.get('text', ''), firstLineIndent=20)
                self.add_spacing(10)

            elif item.get('type') == 'image':
                # Ensure width and height are passed as-is from JSON
                width_value = item.get('width', 300)
                height_value = item.get('height', 'auto')

                self.add_image(
                    src=item.get('src'),
                    alignment=item.get('alignment', 'center'),
                    width=width_value,
                    height=height_value,
                    caption=item.get('caption')
                )

            else:
                logger.warning(f"Unknown content type: {item.get('type')} - skipping")

        return self

    def add_chapter_paragraphs_with_breaks(self, paragraphs: list, chapter_title: str = "",
                                           has_header: bool = False, has_footer: bool = False):
        """
        Adds multiple paragraphs with intelligent page breaking.
        This is where LayoutService is used internally.
        """
        for i, par_text in enumerate(paragraphs):
            if not par_text.strip():
                self.add_spacing(10)
                continue

            # Use internal LayoutService to handle complex paragraph flow
            self._add_paragraph_with_breaks(par_text, chapter_title, has_header, has_footer)

    def _add_paragraph_with_breaks(self, text: str, chapter_title: str,
                                   has_header: bool, has_footer: bool):
        """
        Internal method that uses LayoutService for complex paragraph handling.
        Page builders don't call this directly.
        """
        par_obj = self.create_paragraph(text, firstLineIndent=20)

        while par_obj:
            # Use LayoutService to calculate available space
            available_height = self.layout_service.calculate_available_space(self.current_pos)

            # If no space, do page break
            if available_height <= 0:
                if has_footer:
                    self.add_footer(chapter_title)
                self.new_page()
                self.start_from(self.padding_v)
                if has_header:
                    self.add_header(f'<span>{chapter_title}</span>')
                available_height = self.layout_service.calculate_available_space(self.current_pos)

            # Use LayoutService to split paragraph
            width = self.page_size[0] - 2 * self.padding_h
            parts = par_obj.split(width, available_height)

            if not parts:
                break

            # Draw the part that fits
            self.draw_paragraph_object(parts[0])
            self.add_spacing(10)

            # Check if there's continuation
            if len(parts) > 1:
                par_obj = parts[1]
                # Will need page break for continuation
                if has_footer:
                    self.add_footer(chapter_title)
                self.new_page()
                self.start_from(self.padding_v)
                if has_header:
                    self.add_header(f'<span>{chapter_title}</span>')
            else:
                par_obj = None

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
        y = self.padding_v

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
        """Creates a Paragraph object without drawing it."""
        style_name = kwargs.pop('style_name', 'paragraph_default')
        style = self.style_manager.prepare_style(style_name, **kwargs)
        return Paragraph(text, style)

    def create_title_paragraph(self, text: str, **kwargs):
        """Creates a title paragraph."""
        style = self.style_manager.prepare_style('title_main', **kwargs)
        return Paragraph(text, style)

    def create_subtitle_paragraph(self, text: str, **kwargs):
        """Creates a subtitle paragraph."""
        style = self.style_manager.prepare_style('title_sub', **kwargs)
        return Paragraph(text, style)

    def draw_paragraph_object(self, p: Paragraph):
        """Draws an existing Paragraph object at current position."""
        width = self.page_size[0] - 2 * self.padding_h
        _w, h = p.wrap(width, 10000)

        y_pos = self.page_size[1] - self.current_pos
        p.drawOn(self.canvas, self.padding_h, y_pos - h)
        self.current_pos += h
        return self

    # ==========================================
    # INTERNAL METHODS (use LayoutService)
    # ==========================================

    def _draw_paragraph(self, text: str, style):
        """Internal helper to draw a styled paragraph."""
        width = self.page_size[0] - 2 * self.padding_h
        y_pos = self.page_size[1] - self.current_pos

        p = Paragraph(text, style)
        w, h = p.wrap(width, 10000)
        p.drawOn(self.canvas, self.padding_h, y_pos - h)

        self.current_pos += h
        return self

    def get_paragraph_height(self, text: str, **kwargs) -> float:
        """Gets paragraph height using LayoutService."""
        return self.layout_service.calculate_paragraph_height(text, **kwargs)
