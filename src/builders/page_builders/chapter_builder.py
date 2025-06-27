from .base_page_builder import BasePageBuilder
from src.logger import logger
from src.utils.anchor_utils import generate_anchor_name
import os

class ChapterBuilder(BasePageBuilder):
    """
    Builds a chapter using ContentBuilder with support for both old and new content formats.
    Supports images and paragraphs in the new 'content' structure.
    """

    def build(self, source_path: str = None, **options):
        if not source_path:
            logger.error("ChapterBuilder requires a 'source_path'.")
            return

        chapter_data = self.data_manager.get_data(self.language, source_path)
        if not chapter_data:
            logger.warning(f"Could not find data for source '{source_path}'. Skipping.")
            return

        # Record start page
        start_page = self.content.page_num

        is_main_chapter = options.get('is_main_chapter', False)

        logger.info(f"Building chapter: '{chapter_data.get('title', 'Unknown Chapter')}' (main: {is_main_chapter})")

        if is_main_chapter:
            self._build_as_main_chapter(chapter_data)
        else:
            self._build_as_simple_chapter(chapter_data)

        # Record end page and register with registry
        end_page = self.content.page_num - 1  # -1 because we already called new_page()
        chapter_title = chapter_data.get('title', 'Unknown Chapter')

        # Create anchor name
        anchor = self._get_anchor_name(chapter_data)

        self.register_section(source_path, chapter_title, start_page, end_page, anchor)

    def _get_anchor_name(self, chapter_data: dict) -> str:
        """
        Generate anchor name for this chapter.
        """
        # Use the title to create a clean anchor
        title = chapter_data.get('title', 'chapter')
        # Clean up title for anchor (remove spaces, special chars)
        return generate_anchor_name(title)

    def _build_as_simple_chapter(self, chapter_data: dict):
        """Builds a simple chapter with proper anchor and support for images."""
        starting_pos = self.config.get("common.padding.vertical")

        chapter_title = chapter_data.get("title", "")
        anchor = self._get_anchor_name(chapter_data)

        logger.info(f"Building simple chapter: '{chapter_title}' with anchor '{anchor}'")

        (self.content
         .start_from(starting_pos)
         .add_paragraph(f'<a name="{anchor}"></a>{chapter_title}', style_name='title_sub'))

        # Handle both old and new content formats
        if 'content' in chapter_data and chapter_data['content']:
            # NEW FORMAT with images and paragraphs
            logger.info(f"Using new content format with {len(chapter_data['content'])} items")
            self.content.add_content_items(chapter_data['content'])
        elif 'paragraphs' in chapter_data and chapter_data['paragraphs']:
            # LEGACY FORMAT - just paragraphs
            logger.info(f"Using legacy paragraphs format with {len(chapter_data['paragraphs'])} paragraphs")
            self._draw_paragraphs_with_page_breaks(
                chapter_data,
                has_header=False,
                has_footer=False,
                continue_from_current_pos=True
            )
        else:
            logger.warning(f"No content found in chapter: {chapter_title}")

        self.content.new_page()

    def _build_as_main_chapter(self, chapter_data: dict):
        """Builds a main chapter with title page and support for images."""
        starting_pos = self.config.get("defaults.starting_pos")
        chapter_title = chapter_data.get('title', '')
        anchor = self._get_anchor_name(chapter_data)

        logger.info(f"Building main chapter: '{chapter_title}' with anchor '{anchor}'")

        # Build title page WITH ANCHOR
        (self.content
         .start_from(starting_pos)
         .add_title(f'<a name="{anchor}"></a>{chapter_title}', alignment=1, font_size=64, leading=64)
         .new_page())

        # Build content pages
        self.content.start_from(self.config.get("common.padding.vertical"))
        self.content.add_header(f'<span>{chapter_title}</span>')

        # Signal that we're in a main chapter (for image handling)
        self.content._in_main_chapter = True

        # Handle both old and new content formats
        logger.info("Checking content formats...")
        has_content = 'content' in chapter_data and chapter_data['content']
        has_paragraphs = 'paragraphs' in chapter_data and chapter_data['paragraphs']

        # logger.info(f"Has content: {has_content}")
        # logger.info(f"Has paragraphs: {has_paragraphs}")

        if has_content:
            # NEW FORMAT with images and paragraphs
            content_count = len(chapter_data['content'])
            logger.info(f"----- Using new content format with {content_count} items")
            logger.info("----- CALLING _build_content_with_headers_footers...")
            self._build_content_with_headers_footers(chapter_data)
            logger.info("----- RETURNED from _build_content_with_headers_footers")
        elif has_paragraphs:
            # LEGACY FORMAT with paragraphs
            paragraphs_count = len(chapter_data['paragraphs'])
            logger.info(f"Using legacy paragraphs format with {paragraphs_count} paragraphs")
            paragraphs = chapter_data.get('paragraphs', [])
            self.content.add_chapter_paragraphs_with_breaks(
                paragraphs=paragraphs,
                chapter_title=chapter_title,
                has_header=True,
                has_footer=True
            )
        else:
            logger.error(f"ERROR: No content found in main chapter: {chapter_title}")

        # Reset flag
        self.content._in_main_chapter = False

        logger.info("Adding footer and new page...")
        self.content.add_footer(chapter_title)
        self.content.new_page()
        logger.info("Main chapter building completed")

    def _build_content_with_headers_footers(self, chapter_data: dict):
        """
        Build content items with proper header/footer handling for main chapters.
        This handles page breaks manually for the new content format.
        """
        content_items = chapter_data.get('content', [])
        chapter_title = chapter_data.get('title', '')

        for i, item in enumerate(content_items):
            if item.get('type') == 'paragraph':
                # For paragraphs in main chapters, we need to handle page breaks
                text = item.get('text', '')
                print(f"!!!!!!!!!!!!!!!!!! Paragraph {i+1}: {text}")
                if text.strip():
                    self._add_paragraph_with_headers_footers(text, chapter_title)
                else:
                    self.content.add_spacing(10)

            elif item.get('type') == 'image':
                print(f"####################### image {i+1}: {item.get('src')}")
                # Check if image fits on current page
                required_height = self._estimate_image_height(item)
                available_height = self.content.layout_service.calculate_available_space(self.content.current_pos)

                if required_height > available_height:
                    # Need page break
                    self.content.add_footer(chapter_title)
                    self.content.new_page()
                    self.content.start_from(self.config.get("common.padding.vertical"))
                    self.content.add_header(f'<span>{chapter_title}</span>')

                # Add the image
                self.content.add_image(
                    src=item.get('src'),
                    alignment=item.get('alignment', 'center'),
                    width=item.get('width', 300),
                    height=item.get('height', 'auto'),
                    caption=item.get('caption')
                )

            else:
                logger.warning(f"Unknown content type: {item.get('type')} - skipping")

    def _add_paragraph_with_headers_footers(self, text: str, chapter_title: str):
        """
        Add a single paragraph with proper header/footer handling.
        Similar to the logic in add_chapter_paragraphs_with_breaks but for individual paragraphs.
        """
        par_obj = self.content.create_paragraph(text, firstLineIndent=20)

        while par_obj:
            # Use LayoutService to calculate available space
            available_height = self.content.layout_service.calculate_available_space(self.content.current_pos)

            # If no space, do page break
            if available_height <= 0:
                self.content.add_footer(chapter_title)
                self.content.new_page()
                self.content.start_from(self.config.get("common.padding.vertical"))
                self.content.add_header(f'<span>{chapter_title}</span>')
                available_height = self.content.layout_service.calculate_available_space(self.content.current_pos)

            # Use LayoutService to split paragraph
            width = self.content.page_size[0] - 2 * self.content.padding_h
            parts = par_obj.split(width, available_height)

            if not parts:
                break

            # Draw the part that fits
            self.content.draw_paragraph_object(parts[0])
            self.content.add_spacing(10)

            # Check if there's continuation
            if len(parts) > 1:
                par_obj = parts[1]
                # Page break for continuation
                self.content.add_footer(chapter_title)
                self.content.new_page()
                self.content.start_from(self.config.get("common.padding.vertical"))
                self.content.add_header(f'<span>{chapter_title}</span>')
            else:
                par_obj = None

    def _estimate_image_height(self, image_item: dict) -> float:
        """
        Estimate the height an image will take (including caption).
        Now loads actual image to get real dimensions with detailed logging.
        """
        width = image_item.get('width', 300)
        height = image_item.get('height', 'auto')
        caption = image_item.get('caption')
        src = image_item.get('src')

        # Calculate available space like ContentBuilder does
        available_width = self.content.page_size[0] - 2 * self.content.padding_h
        available_height = self.content.layout_service.calculate_available_space(self.content.current_pos + 30)

        # Get page dimensions for logging
        page_total_height = self.content.page_size[1] - 2 * self.content.padding_v
        current_used_height = self.content.current_pos
        remaining_height = page_total_height - current_used_height

        # Try to get real image dimensions
        real_aspect_ratio = 0.75  # Default fallback
        original_width = 0
        original_height = 0

        try:
            from PIL import Image
            image_path = os.path.join(self.config.get("paths.resources") + "/images", src)
            if os.path.exists(image_path):
                with Image.open(image_path) as img:
                    original_width, original_height = img.size
                    real_aspect_ratio = original_height / original_width
                    logger.info(f"Original image size: {original_width}x{original_height} pixels")
                    logger.info(f"Real aspect ratio: {real_aspect_ratio:.3f} (height/width)")
            else:
                logger.warning(f"Image file not found: {image_path}")
        except Exception as e:
            logger.warning(f"Could not load image {src}: {e}")

        # Handle different width formats
        if isinstance(width, str) and width.endswith('%'):
            percentage = float(width.rstrip('%')) / 100
            width_points = available_width * percentage
            logger.info(f"Width: {width} = {percentage:.1%} of {available_width:.1f} = {width_points:.1f} points")
        elif width == "auto":
            # If width is auto, we need to calculate from height
            if isinstance(height, str) and height.endswith('%') and height != "auto":
                percentage = float(height.rstrip('%')) / 100
                height_points = available_height * percentage
                width_points = height_points / real_aspect_ratio
                logger.info(f"Width: auto (from height {height} = {height_points:.1f} / {real_aspect_ratio:.3f} = {width_points:.1f} points)")

                # IMPORTANT: Check if calculated width exceeds available width!
                if width_points > available_width:
                    logger.info(f"WARNING: Calculated width {width_points:.1f} exceeds available width {available_width:.1f}!")
                    logger.info(f"Scaling down: using full width instead")
                    width_points = available_width
                    height_points = width_points * real_aspect_ratio
                    logger.info(f"Corrected: width={width_points:.1f}, height={height_points:.1f}")
            else:
                # Default width if both are auto
                width_points = 300 * 0.75
                logger.info(f"Width: auto (default 300px = {width_points:.1f} points)")
        else:
            # Convert pixels to points
            width_points = width * 0.75
            logger.info(f"Width: {width}px = {width_points:.1f} points")

        # Handle different height formats
        if isinstance(height, str) and height.endswith('%') and height != "auto":
            percentage = float(height.rstrip('%')) / 100
            height_points = available_height * percentage
            logger.info(f"Height: {height} = {percentage:.1%} of {available_height:.1f} = {height_points:.1f} points")

            # BUT if we already corrected width above, use the corrected height!
            if width == "auto" and isinstance(height, str) and height.endswith('%'):
                # Check if we corrected the width due to overflow
                calculated_width_from_height = (available_height * percentage) / real_aspect_ratio
                if calculated_width_from_height > available_width:
                    # We already corrected this above, use the corrected height
                    height_points = width_points * real_aspect_ratio
                    logger.info(f"Using corrected height instead: {height_points:.1f} points (from corrected width)")

        elif height == 'auto':
            # Use real aspect ratio
            height_points = width_points * real_aspect_ratio
            logger.info(f"Height: auto = {width_points:.1f} * {real_aspect_ratio:.3f} = {height_points:.1f} points")
        else:
            height_points = height * 0.75
            logger.info(f"Height: {height}px = {height_points:.1f} points")

        # Add space for caption if present
        caption_height = 25 if caption else 0
        spacing = 15

        total_estimated_height = height_points + caption_height + spacing

        return total_estimated_height

    def _draw_paragraphs_with_page_breaks(self, chapter_data: dict, has_header: bool, has_footer: bool, continue_from_current_pos: bool = False):
        """
        LEGACY METHOD for old 'paragraphs' format with intelligent page breaking.
        Now uses the ContentBuilder API.
        """
        paragraphs = chapter_data.get('paragraphs', [])
        chapter_title = chapter_data.get("title", "")

        if not paragraphs:
            return

        # Use ContentBuilder's intelligent paragraph breaking method
        self.content.add_chapter_paragraphs_with_breaks(
            paragraphs=paragraphs,
            chapter_title=chapter_title,
            has_header=has_header,
            has_footer=has_footer
        )
