from .base_page_builder import BasePageBuilder
from src.logger import logger
from src.utils.anchor_utils import generate_anchor_name

class ChapterBuilder(BasePageBuilder):
    """
    Builds a chapter using ContentBuilder.
    Doesn't know anything about LayoutService - that's internal to ContentBuilder.
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

        print(f"BEFORE SELECTION ------------------- CREATING ANCHOR: '{self._get_anchor_name(chapter_data)}' FOR TITLE: '{chapter_data.get('title', 'Unknown Chapter')}'")

        if is_main_chapter:
            print(f"CREATING MAIN CHAPTER ANCHOR: '{self._get_anchor_name(chapter_data)}' FOR TITLE: '{chapter_data.get('title',)}'")
            self._build_as_main_chapter(chapter_data)
        else:
            print(f"CREATING SIMPLE CHAPTER ANCHOR: '{self._get_anchor_name(chapter_data)}' FOR TITLE: '{chapter_data.get('title',)}'")
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

    def _draw_paragraphs_with_page_breaks(self, chapter_data: dict, has_header: bool, has_footer: bool, continue_from_current_pos: bool = False):
        """
        RESTORED ORIGINAL METHOD with intelligent page breaking.
        Now uses the new ContentBuilder API.
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
        if 'content' in chapter_data:
            # New format with images
            self.content.add_content_items(chapter_data['content'])
        else:
            # Legacy format - just paragraphs
            self._draw_paragraphs_with_page_breaks(
                chapter_data,
                has_header=False,
                has_footer=False,
                continue_from_current_pos=True
            )

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

        # Handle both old and new content formats
        if 'content' in chapter_data:
            # New format with images
            self.content.add_content_items(chapter_data['content'])
        else:
            # Legacy format with paragraphs
            paragraphs = chapter_data.get('paragraphs', [])
            self.content.add_chapter_paragraphs_with_breaks(
                paragraphs=paragraphs,
                chapter_title=chapter_title,
                has_header=True,
                has_footer=True
            )

        self.content.add_footer(chapter_title)
        self.content.new_page()
