from natsort import natsorted
from reportlab.lib import colors

from src.builders.base_builder import BaseBuilder
from src.builders.content_builder import ContentBuilder
from src.utils.page_utils import make_page
from src.logger import logger
from src.services.page_registry_service import PageRegistryService

from .page_builders.cover_builder import CoverBuilder
from .page_builders.title_page_builder import TitlePageBuilder
from .page_builders.copyright_page_builder import CopyrightPageBuilder
from .page_builders.chapter_builder import ChapterBuilder
from .page_builders.toc_builder import TOCBuilder

class PdfBuilder(BaseBuilder):
    """
    Acts as a director for the PDF generation process.
    It reads the book's structure implicitly from the data's keys and dispatches
    the building task for each section to a specialized PageBuilder class.
    """
    def __init__(self, json_file, paper_book, black_and_white, short, language):
        super().__init__(json_file, paper_book=paper_book, black_and_white=black_and_white,
                         short=short, language=language)

        # Initialize page registry for dynamic TOC
        self.page_registry = PageRegistryService()

        self._dispatcher = {
            'title': TitlePageBuilder,
            'copyright': CopyrightPageBuilder,
            'dedicate': ChapterBuilder,
            'preface': ChapterBuilder,
            # 'chapters' key will be handled specially in the run method.
        }

    def run(self):
        """
        Main process with dynamic TOC generation.

        PHASE 1: Build all content EXCEPT TOC
        PHASE 2: Generate TOC with accurate page numbers
        PHASE 3: Finalize document
        """
        book_data = self.data_manager.get_data(language=self.language)
        if not book_data:
            logger.error(f"No book data found for language '{self.language}'. Aborting.")
            return

        title_info = book_data.get("title", {})
        canvas, pagesize = make_page(
            title_info.get("title", "Unknown Title"),
            title_info.get("subtitle", ""),
            self.config.get("paths.output_dir"),
            self.paper_book, self.black_and_white, colors.black, self.short
        )

        content_builder = ContentBuilder(canvas, pagesize, self.style_manager, self.config)

        # PHASE 1: Build everything except TOC
        logger.info("=== PHASE 1: Building content (no TOC yet) ===")

        # Cover
        CoverBuilder(content_builder, self.data_manager, self.language, self.config, self.page_registry).build()

        # Title and Copyright (these won't appear in TOC)
        for section_key in ['title', 'copyright']:
            if section_key in book_data:
                builder_class = self._dispatcher.get(section_key)
                if builder_class:
                    self._build_section(builder_class, content_builder, source_path=section_key)

        # Remember where to insert TOC (after copyright)
        toc_insert_after = content_builder.page_num - 1
        self.page_registry.set_toc_insert_position(toc_insert_after)

        # Build remaining sections that will appear in TOC
        for section_key in ['dedicate', 'preface']:
            if section_key in book_data:
                builder_class = self._dispatcher.get(section_key)
                if builder_class:
                    self._build_section(builder_class, content_builder, source_path=section_key)

        # PHASE 2: Generate TOC with accurate page numbers BEFORE main chapters
        logger.info("=== PHASE 2: Generating dynamic TOC ===")
        logger.info(self.page_registry.get_sections_summary())

        # Create fake TOC data if it doesn't exist
        toc_data = book_data.get('toc', {
            'title': 'Table of Contents'
        })

        # Build TOC NOW (this will calculate and adjust page numbers)
        toc_builder = TOCBuilder(content_builder, self.data_manager, self.language, self.config, self.page_registry)
        toc_builder.build(toc_data=toc_data)  # Pass toc_data directly

        # Build main chapters AFTER TOC
        if 'chapters' in book_data and book_data['chapters']:
            logger.info("--- Building Main Chapters AFTER TOC ---")
            chapters_data = book_data['chapters']
            for chapter_key in natsorted(chapters_data.keys()):
                self._build_section(ChapterBuilder, content_builder, source_path=f"chapters.{chapter_key}", is_main_chapter=True)

        canvas.save()
        logger.info("Successfully created the PDF with dynamic TOC!")

    def _build_section(self, builder_class, content_builder, source_path=None, **options):
        """
        Instantiates and runs a specialized page builder.
        Now passes page_registry to builders.
        """
        try:
            page_builder = builder_class(
                content_builder, self.data_manager, self.language, self.config, self.page_registry
            )
            page_builder.build(source_path=source_path, **options)
            logger.info(f"Successfully built section from source: '{source_path or 'N/A'}'")
        except Exception as e:
            logger.error(f"Failed to build section from source '{source_path}': {e}", exc_info=True)