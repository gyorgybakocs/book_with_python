from .base_page_builder import BasePageBuilder
from src.logger import logger
from src.utils.anchor_utils import generate_anchor_name
import os

class ChapterBuilder(BasePageBuilder):
    """
    Builds a chapter using ContentBuilder with support for both old and new content formats.
    Supports images, simple tables, advanced tables, textboxes and paragraphs in the new 'content' structure.
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
        """Builds a simple chapter with proper anchor and support for images, tables and textboxes."""
        starting_pos = self.config.get("common.padding.vertical")

        chapter_title = chapter_data.get("title", "")
        anchor = self._get_anchor_name(chapter_data)

        logger.info(f"Building simple chapter: '{chapter_title}' with anchor '{anchor}'")

        (self.content
         .start_from(starting_pos)
         .add_paragraph(f'<a name="{anchor}"></a>{chapter_title}', style_name='title_sub', extra_spacing=10))

        # Handle both old and new content formats
        if 'content' in chapter_data and chapter_data['content']:
            # NEW FORMAT with images, tables, textboxes and paragraphs - USE SMART CONTENT PROCESSING
            logger.info(f"Using new content format with {len(chapter_data['content'])} items")
            logger.info("Simple chapter will use smart content processing...")
            self._build_content_with_smart_breaks(chapter_data, has_headers_footers=False)
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
        """Builds a main chapter with title page and support for images, tables and textboxes."""
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
            # NEW FORMAT with images, tables, textboxes and paragraphs
            content_count = len(chapter_data['content'])
            logger.info(f"----- Using new content format with {content_count} items")
            logger.info("----- CALLING _build_content_with_smart_breaks...")
            self._build_content_with_smart_breaks(chapter_data, has_headers_footers=True)
            logger.info("----- RETURNED from _build_content_with_smart_breaks")
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

    def _build_content_with_smart_breaks(self, chapter_data: dict, has_headers_footers: bool = False):
        """
        Build content items with smart page breaking - works for both simple and main chapters.
        Now supports simple tables, advanced tables and textboxes!
        """
        content_items = chapter_data.get('content', [])
        chapter_title = chapter_data.get('title', '')

        logger.info(f"Processing {len(content_items)} content items with smart breaks for: {chapter_title}")

        for i, item in enumerate(content_items):
            logger.debug(f"Processing item {i+1}/{len(content_items)}: {item.get('type')}")

            if item.get('type') == 'paragraph':
                text = item.get('text', '')
                logger.debug(f"Paragraph {i+1}: {text[:50]}..." if len(text) > 50 else f"Paragraph {i+1}: {text}")

                if text.strip():
                    if has_headers_footers:
                        self._add_paragraph_with_headers_footers(text, chapter_title)
                    else:
                        self._add_paragraph_with_simple_breaks(text, chapter_title)
                else:
                    self.content.add_spacing(10)

            elif item.get('type') == 'speech_bubble':
                logger.debug(f"Speech Bubble {i+1}: {item.get('text', '')[:30]}...")

                # Check if speech bubble fits on current page
                required_height = self.content.speech_bubble_builder.estimate_speech_bubble_height(item)
                available_height = self.content.layout_service.calculate_available_space(self.content.current_pos)

                logger.debug(f"Speech Bubble height needed: {required_height:.1f}, available: {available_height:.1f}")

                if required_height > available_height:
                    self._handle_page_break(chapter_title, has_headers_footers)

                # Add the speech bubble
                self.content.add_speech_bubble(item)

            elif item.get('type') == 'textbox':
                logger.debug(f"TextBox {i+1}: {len(item.get('content', []))} content items")

                # Check if textbox fits on current page
                required_height = self.content.textbox_builder.estimate_textbox_height(item)
                available_height = self.content.layout_service.calculate_available_space(self.content.current_pos)

                logger.debug(f"TextBox height needed: {required_height:.1f}, available: {available_height:.1f}")

                if required_height > available_height:
                    self._handle_page_break(chapter_title, has_headers_footers)

                # Add the textbox
                self.content.add_textbox(item)

            elif item.get('type') == 'image':
                logger.debug(f"Image {i+1}: {item.get('src')}")

                # Check if image fits on current page
                required_height = self._estimate_image_height(item)
                available_height = self.content.layout_service.calculate_available_space(self.content.current_pos)

                logger.debug(f"Image height needed: {required_height:.1f}, available: {available_height:.1f}")

                if required_height > available_height:
                    self._handle_page_break(chapter_title, has_headers_footers)

                # Add the image
                self.content.add_image(
                    src=item.get('src'),
                    alignment=item.get('alignment', 'center'),
                    width=item.get('width', 300),
                    height=item.get('height', 'auto'),
                    caption=item.get('caption')
                )
                logger.debug(f"--------> WE ADDED A NEW IMAGE!!!! src: {item.get('src')}, w: {item.get('width', 300)}, h: {item.get('height', 'auto')}")
            elif item.get('type') == 'table':
                logger.debug(f"Table {i+1}: data matrix with {len(item.get('data', []))} rows")

                self.content.add_table(
                    data=item.get('data', []),
                    style=item.get('style', []),
                    caption=item.get('caption'),
                    alignment=item.get('alignment', 'center'),
                    block_column_widths=item.get('block_column_widths', None)
                )
            elif item.get('type') == 'list':
                logger.debug(f"List {i+1}: Unpacking {len(item.get('items', []))} items for page breaking.")
                list_items = item.get('items', [])
                for list_item_data in list_items:
                    # For each item in the list, perform the estimate -> check -> draw cycle
                    li_req_height = self.content.list_builder.estimate_list_item_height(list_item_data)
                    available_height = self.content.layout_service.calculate_available_space(self.content.current_pos)
                    logger.debug(f"  List item height needed: {li_req_height:.1f}, available: {available_height:.1f}")

                    if li_req_height > available_height:
                        self._handle_page_break(chapter_title, has_headers_footers)

                    # Draw this single list item
                    self.content.add_list_item(list_item_data)
            else:
                logger.warning(f"Unknown content type: {item.get('type')} - skipping")

        logger.info(f"Finished processing all {len(content_items)} content items with smart breaks")

    def _handle_page_break(self, chapter_title: str, has_headers_footers: bool):
        logger.debug("Item doesn't fit, performing page break")
        if has_headers_footers:
            self.content.add_footer(chapter_title)
            self.content.new_page()
            self.content.start_from(self.config.get("common.padding.vertical"))
            self.content.add_header(f'<span>{chapter_title}</span>')
        else:
            self.content.new_page()
            self.content.start_from(self.config.get("common.padding.vertical"))

    def _add_paragraph_with_simple_breaks(self, text: str, chapter_title: str):
        """
        Add a paragraph with simple page breaks (no headers/footers).
        """
        logger.debug(f"Adding paragraph with simple breaks: {text[:30]}...")

        par_obj = self.content.create_paragraph(text, firstLineIndent=20)

        while par_obj:
            # Use LayoutService to calculate available space
            available_height = self.content.layout_service.calculate_available_space(self.content.current_pos)
            logger.debug(f"Available height for paragraph: {available_height:.1f}")

            # If no space, do simple page break
            if available_height <= 20:  # Need some minimum space
                logger.debug("Not enough space for paragraph, doing simple page break")
                self.content.new_page()
                self.content.start_from(self.config.get("common.padding.vertical"))
                available_height = self.content.layout_service.calculate_available_space(self.content.current_pos)

            # Use LayoutService to split paragraph
            width = self.content.page_size[0] - 2 * self.content.padding_h
            parts = par_obj.split(width, available_height)

            if not parts:
                logger.warning("Could not split paragraph, forcing simple page break")
                self.content.new_page()
                self.content.start_from(self.config.get("common.padding.vertical"))
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
                # Simple page break for continuation
                self.content.new_page()
                self.content.start_from(self.config.get("common.padding.vertical"))
            else:
                par_obj = None
                logger.debug("Paragraph completed")

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
        This version uses the user's original logic and applies the agreed-upon fix
        for percentage-based height calculation.
        """
        width = image_item.get('width', 300)
        height = image_item.get('height', 'auto')
        caption = image_item.get('caption')
        src = image_item.get('src')

        # This is from the user's provided 'good' code.
        available_width = self.content.page_size[0] - 2 * self.content.padding_h
        available_height = self.content.layout_service.calculate_available_space(self.content.current_pos + 30)

        # Get the total content height of a full page for percentage calculations
        total_page_content_height = self.content.page_size[1] - (2 * self.config.get("common.padding.vertical"))

        real_aspect_ratio = 0.75  # Default fallback
        try:
            from PIL import Image
            image_path = os.path.join(self.config.get("paths.resources") + "/images", src)
            if os.path.exists(image_path):
                with Image.open(image_path) as img:
                    original_width, original_height = img.size
                    if original_width > 0:
                        real_aspect_ratio = original_height / original_width
                    logger.debug(f"Image {src}: {original_width}x{original_height}, ratio: {real_aspect_ratio:.3f}")
            else:
                logger.warning(f"Image file not found: {image_path}")
        except Exception as e:
            logger.warning(f"Could not load image {src}: {e}")

        # Handle different width/height formats using the user's original logic
        if isinstance(width, str) and width.endswith('%'):
            percentage = float(width.rstrip('%')) / 100
            width_points = available_width * percentage
            height_points = width_points * real_aspect_ratio
            logger.debug(f"Width percentage: {width} = {width_points:.1f} points")
            if height_points > available_height:
                logger.debug(f"Image would be too tall, scaling to fit height")
                height_points = available_height
                if real_aspect_ratio > 0: width_points = height_points / real_aspect_ratio

        elif isinstance(height, str) and height.endswith('%') and height != "auto":
            # --- FIX APPLIED HERE ---
            # Calculate from total page height, not remaining available height
            percentage = float(height.rstrip('%')) / 100
            height_points = total_page_content_height * percentage
            if real_aspect_ratio > 0: width_points = height_points / real_aspect_ratio
            else: width_points = available_width
            logger.debug(f"Height percentage: {height} = {height_points:.1f} points")
            if width_points > available_width:
                logger.debug(f"Image would be too wide, scaling to fit width")
                width_points = available_width
                height_points = width_points * real_aspect_ratio

        elif width == "auto" and isinstance(height, str) and height.endswith('%'):
            # --- FIX APPLIED HERE ---
            # Calculate from total page height, not remaining available height
            percentage = float(height.rstrip('%')) / 100
            height_points = total_page_content_height * percentage
            if real_aspect_ratio > 0: width_points = height_points / real_aspect_ratio
            else: width_points = available_width
            logger.debug(f"Auto width with height {height}: {width_points:.1f}x{height_points:.1f} points")
            if width_points > available_width:
                logger.debug(f"Auto width would be too wide, scaling to fit")
                width_points = available_width
                height_points = width_points * real_aspect_ratio

        else:
            width_points = width * 0.75 if isinstance(width, (int, float)) else width
            if height == "auto":
                height_points = width_points * real_aspect_ratio
            else:
                height_points = height * 0.75 if isinstance(height, (int, float)) else height
            if width_points > available_width:
                scale_factor = available_width / width_points
                width_points = available_width
                height_points = height_points * scale_factor
            if height_points > available_height:
                scale_factor = available_height / height_points
                height_points = available_height
                width_points = width_points * scale_factor

        caption_height = 25 if caption and caption.strip() else 0
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
