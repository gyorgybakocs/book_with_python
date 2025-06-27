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

        logger.info(f"Processing {len(content_items)} content items for chapter: {chapter_title}")

        for i, item in enumerate(content_items):
            logger.debug(f"Processing item {i+1}/{len(content_items)}: {item.get('type')}")

            if item.get('type') == 'paragraph':
                # For paragraphs in main chapters, we need to handle page breaks
                text = item.get('text', '')
                logger.debug(f"Paragraph {i+1}: {text[:50]}..." if len(text) > 50 else f"Paragraph {i+1}: {text}")

                if text.strip():
                    self._add_paragraph_with_headers_footers(text, chapter_title)
                else:
                    self.content.add_spacing(10)

            elif item.get('type') == 'image':
                logger.debug(f"Image {i+1}: {item.get('src')}")

                # Check if image fits on current page
                required_height = self._estimate_image_height(item)
                available_height = self.content.layout_service.calculate_available_space(self.content.current_pos)

                logger.debug(f"Image height needed: {required_height:.1f}, available: {available_height:.1f}")

                if required_height > available_height:
                    # Need page break
                    logger.debug("Image doesn't fit, doing page break")
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

        logger.info(f"Finished processing all {len(content_items)} content items")

    def _add_paragraph_with_headers_footers(self, text: str, chapter_title: str):
        """
        Add a single paragraph with proper header/footer handling.
        Similar to the logic in add_chapter_paragraphs_with_breaks but for individual paragraphs.
        """
        logger.debug(f"Adding paragraph with headers/footers: {text[:30]}...")

        par_obj = self.content.create_paragraph(text, firstLineIndent=20)

        while par_obj:
            # Use LayoutService to calculate available space
            available_height = self.content.layout_service.calculate_available_space(self.content.current_pos)
            logger.debug(f"Available height for paragraph: {available_height:.1f}")

            # If no space, do page break
            if available_height <= 20:  # Need some minimum space
                logger.debug("Not enough space for paragraph, doing page break")
                self.content.add_footer(chapter_title)
                self.content.new_page()
                self.content.start_from(self.config.get("common.padding.vertical"))
                self.content.add_header(f'<span>{chapter_title}</span>')
                available_height = self.content.layout_service.calculate_available_space(self.content.current_pos)

            # Use LayoutService to split paragraph
            width = self.content.page_size[0] - 2 * self.content.padding_h
            parts = par_obj.split(width, available_height)

            if not parts:
                logger.warning("Could not split paragraph, forcing page break")
                self.content.add_footer(chapter_title)
                self.content.new_page()
                self.content.start_from(self.config.get("common.padding.vertical"))
                self.content.add_header(f'<span>{chapter_title}</span>')
                # Try again on new page
                available_height = self.content.layout_service.calculate_available_space(self.content.current_pos)
                parts = par_obj.split(width, available_height)
                if not parts:
                    logger.error("Still cannot split paragraph even on new page - skipping")
                    break

            # Draw the part that fits
            logger.debug(f"Drawing paragraph part, remaining parts: {len(parts)}")
            self.content.draw_paragraph_object(parts[0])
            self.content.add_spacing(10)

            # Check if there's continuation
            if len(parts) > 1:
                par_obj = parts[1]
                logger.debug("Paragraph continues on next page")
                # Page break for continuation
                self.content.add_footer(chapter_title)
                self.content.new_page()
                self.content.start_from(self.config.get("common.padding.vertical"))
                self.content.add_header(f'<span>{chapter_title}</span>')
            else:
                par_obj = None
                logger.debug("Paragraph completed")

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

        # Try to get real image dimensions
        real_aspect_ratio = 0.75  # Default fallback

        try:
            from PIL import Image
            image_path = os.path.join(self.config.get("paths.resources") + "/images", src)
            if os.path.exists(image_path):
                with Image.open(image_path) as img:
                    original_width, original_height = img.size
                    real_aspect_ratio = original_height / original_width
                    logger.debug(f"Image {src}: {original_width}x{original_height}, ratio: {real_aspect_ratio:.3f}")
            else:
                logger.warning(f"Image file not found: {image_path}")
        except Exception as e:
            logger.warning(f"Could not load image {src}: {e}")

        # Handle different width formats
        if isinstance(width, str) and width.endswith('%'):
            percentage = float(width.rstrip('%')) / 100
            width_points = available_width * percentage
            height_points = width_points * real_aspect_ratio
            logger.debug(f"Width percentage: {width} = {width_points:.1f} points")

            # Check if height would be too tall
            if height_points > available_height:
                logger.debug(f"Image would be too tall, scaling to fit height")
                height_points = available_height
                width_points = height_points / real_aspect_ratio

        elif isinstance(height, str) and height.endswith('%') and height != "auto":
            # Height as percentage
            percentage = float(height.rstrip('%')) / 100
            height_points = available_height * percentage
            width_points = height_points / real_aspect_ratio
            logger.debug(f"Height percentage: {height} = {height_points:.1f} points")

            # Check if width would be too wide
            if width_points > available_width:
                logger.debug(f"Image would be too wide, scaling to fit width")
                width_points = available_width
                height_points = width_points * real_aspect_ratio

        elif width == "auto" and isinstance(height, str) and height.endswith('%'):
            # Auto width with percentage height
            percentage = float(height.rstrip('%')) / 100
            height_points = available_height * percentage
            width_points = height_points / real_aspect_ratio
            logger.debug(f"Auto width with height {height}: {width_points:.1f}x{height_points:.1f} points")

            # Check if width would be too wide
            if width_points > available_width:
                logger.debug(f"Auto width would be too wide, scaling to fit")
                width_points = available_width
                height_points = width_points * real_aspect_ratio

        else:
            # Normal pixel-based sizing
            width_points = width * 0.75  # Convert pixels to points

            if height == "auto":
                height_points = width_points * real_aspect_ratio
            else:
                height_points = height * 0.75

            # Check if dimensions exceed available space and scale down if needed
            if width_points > available_width:
                scale_factor = available_width / width_points
                width_points = available_width
                height_points = height_points * scale_factor

            if height_points > available_height:
                scale_factor = available_height / height_points
                height_points = available_height
                width_points = width_points * scale_factor

        # Add space for caption if present
        caption_height = 25 if caption else 0
        spacing = 15

        total_estimated_height = height_points + caption_height + spacing
        logger.debug(f"Total estimated height for {src}: {total_estimated_height:.1f} points")

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
