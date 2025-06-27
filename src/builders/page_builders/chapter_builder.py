from .base_page_builder import BasePageBuilder
from src.logger import logger

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

    def _build_as_simple_chapter(self, chapter_data: dict):
        """Builds a simple chapter with proper anchor."""
        starting_pos = self.config.get("common.padding.vertical")

        chapter_title = chapter_data.get("title", "")
        anchor = self._get_anchor_name(chapter_data)

        (self.content
         .start_from(starting_pos)
         .add_paragraph(f'<a name="{anchor}"/>{chapter_title}', style_name='title_sub'))

        self._draw_paragraphs_with_page_breaks(
            chapter_data,
            has_header=False,
            has_footer=False,
            continue_from_current_pos=True
        )

        self.content.new_page()

    def _get_anchor_name(self, chapter_data: dict) -> str:
        """
        Generate anchor name for this chapter.
        """
        # Use the title to create a clean anchor
        title = chapter_data.get('title', 'chapter')
        # Clean up title for anchor (remove spaces, special chars)
        anchor = title.lower().replace(' ', '_').replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u').replace('ű', 'u').replace('ö', 'o').replace('ü', 'u')
        return anchor

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

    def _build_as_main_chapter(self, chapter_data: dict):
        """Builds a main chapter with title page and complex paragraph flow."""
        starting_pos = self.config.get("defaults.starting_pos")
        chapter_title = chapter_data.get('title', '')

        # Build title page
        (self.content
         .start_from(starting_pos)
         .add_title(chapter_title, alignment=1, font_size=64, leading=64)
         .new_page())

        # Build content pages with intelligent page breaking
        self.content.start_from(self.config.get("common.padding.vertical"))
        self.content.add_header(f'<span>{chapter_title}</span>')

        # Use ContentBuilder's intelligent paragraph flow method
        paragraphs = chapter_data.get('paragraphs', [])
        self.content.add_chapter_paragraphs_with_breaks(
            paragraphs=paragraphs,
            chapter_title=chapter_title,
            has_header=True,
            has_footer=True
        )

        self.content.add_footer(chapter_title)
        self.content.new_page()