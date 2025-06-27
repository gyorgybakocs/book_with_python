from natsort import natsorted
from reportlab.lib import colors

from src.builders.base_builder import BaseBuilder
from src.builders.content_builder import ContentBuilder
from src.utils.page_utils import make_page
from src.logger import logger
from src.services.page_registry_service import PageRegistryService
from src.utils.anchor_utils import generate_anchor_name

from .page_builders.cover_builder import CoverBuilder
from .page_builders.title_page_builder import TitlePageBuilder
from .page_builders.copyright_page_builder import CopyrightPageBuilder
from .page_builders.chapter_builder import ChapterBuilder
from .page_builders.toc_builder import TOCBuilder

class PdfBuilder(BaseBuilder):
    """
    Acts as a director for the PDF generation process using DRY RUN approach.
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
        Main process with DRY RUN approach for accurate TOC generation.
        
        PHASE 1: DRY RUN - Build everything without TOC to collect page numbers
        PHASE 2: Generate TOC with accurate page numbers  
        PHASE 3: REAL RUN - Build final document with correct TOC
        """
        book_data = self.data_manager.get_data(language=self.language)
        if not book_data:
            logger.error(f"No book data found for language '{self.language}'. Aborting.")
            return

        title_info = book_data.get("title", {})

        # PHASE 1: DRY RUN to collect page numbers
        logger.info("=== PHASE 1: DRY RUN - Collecting accurate page numbers ===")
        page_counts = self._dry_run_collect_page_numbers(book_data)

        # PHASE 2: Generate TOC with accurate page numbers
        logger.info("=== PHASE 2: Registering sections with REAL page numbers ===")
        self._register_sections_with_real_page_numbers(book_data, page_counts)

        # PHASE 3: REAL RUN with correct TOC
        logger.info("=== PHASE 3: REAL RUN - Building final document ===")
        canvas, pagesize = make_page(
            title_info.get("title", "Unknown Title"),
            title_info.get("subtitle", ""),
            self.config.get("paths.output_dir"),
            self.paper_book, self.black_and_white, colors.black, self.short
        )

        content_builder = ContentBuilder(canvas, pagesize, self.style_manager, self.config)

        # Build final document with accurate TOC
        self._build_final_document(content_builder, book_data)

        canvas.save()
        logger.info("Successfully created PDF with ACCURATE TOC!")
        logger.info(self.page_registry.get_sections_summary())

    def _dry_run_collect_page_numbers(self, book_data):
        """
        DRY RUN: Build all content to a temporary canvas to collect accurate page numbers.
        Returns dictionary with section names and their page counts.
        """
        from io import BytesIO
        from reportlab.pdfgen import canvas as temp_canvas
        from reportlab.lib.pagesizes import letter, portrait

        # Create temporary canvas for dry run
        temp_buffer = BytesIO()
        dry_canvas = temp_canvas.Canvas(temp_buffer, pagesize=letter)
        dry_canvas.setPageSize(portrait(letter))

        dry_content = ContentBuilder(dry_canvas, portrait(letter), self.style_manager, self.config)

        page_counts = {}

        logger.info("DRY RUN: Building front matter...")
        # Cover (page 1)
        start_page = dry_content.page_num
        CoverBuilder(dry_content, self.data_manager, self.language, self.config, None).build()
        page_counts['cover'] = dry_content.page_num - start_page

        # Title and Copyright (pages 2-3)
        for section_key in ['title', 'copyright']:
            if section_key in book_data:
                start_page = dry_content.page_num
                builder_class = self._dispatcher.get(section_key)
                if builder_class:
                    self._build_section_dry_run(builder_class, dry_content, source_path=section_key)
                page_counts[section_key] = dry_content.page_num - start_page

        # Dedication (page 4)
        if 'dedicate' in book_data:
            start_page = dry_content.page_num
            self._build_section_dry_run(ChapterBuilder, dry_content, source_path='dedicate')
            page_counts['dedicate'] = dry_content.page_num - start_page

        # Reserve space for TOC (will be inserted later)
        toc_pages = 2  # Fixed 2 pages for TOC
        page_counts['toc'] = toc_pages
        dry_content.page_num += toc_pages  # Simulate TOC pages

        logger.info("DRY RUN: Building main content...")
        # Preface
        if 'preface' in book_data:
            start_page = dry_content.page_num
            self._build_section_dry_run(ChapterBuilder, dry_content, source_path='preface')
            page_counts['preface'] = dry_content.page_num - start_page

        # Main chapters
        if 'chapters' in book_data and book_data['chapters']:
            chapters_data = book_data['chapters']
            for chapter_key in natsorted(chapters_data.keys()):
                start_page = dry_content.page_num
                self._build_section_dry_run(ChapterBuilder, dry_content, source_path=f"chapters.{chapter_key}", is_main_chapter=True)
                page_counts[f'chapters.{chapter_key}'] = dry_content.page_num - start_page

        # Close dry run canvas
        dry_canvas.save()

        logger.info(f"DRY RUN completed. Total pages: {dry_content.page_num}")
        for section, pages in page_counts.items():
            logger.info(f"  {section}: {pages} pages")

        return page_counts

    def _build_section_dry_run(self, builder_class, content_builder, source_path=None, **options):
        """
        Build a section in DRY RUN mode (without page registry).
        """
        try:
            page_builder = builder_class(
                content_builder, self.data_manager, self.language, self.config, None  # No page registry
            )
            page_builder.build(source_path=source_path, **options)
            logger.debug(f"DRY RUN: Built section '{source_path or 'N/A'}'")
        except Exception as e:
            logger.error(f"DRY RUN: Failed to build section '{source_path}': {e}")

    def _register_sections_with_real_page_numbers(self, book_data, page_counts):
        """
        Register all sections with REAL page numbers collected from dry run.
        """
        current_page = 1

        # Skip cover, title, copyright (don't appear in TOC)
        current_page += page_counts.get('cover', 0)
        current_page += page_counts.get('title', 0)
        current_page += page_counts.get('copyright', 0)

        # Dedication
        if 'dedicate' in book_data:
            dedicate_data = self.data_manager.get_data(self.language, 'dedicate')
            if dedicate_data:
                dedication_pages = page_counts.get('dedicate', 1)
                anchor = generate_anchor_name(dedicate_data.get('title', 'Dedication'))

                start_page = current_page
                end_page = current_page + dedication_pages - 1

                self.page_registry.register_section(
                    'dedicate',
                    dedicate_data.get('title', 'Fiamnak, Alexandernek'),
                    start_page,
                    end_page,
                    anchor
                )
                logger.info(f"Registered dedication: pages {start_page} to {end_page} ({dedication_pages} pages)")
                current_page += dedication_pages

        # TOC takes next 2 pages
        current_page += page_counts.get('toc', 2)

        # Preface - FIXED PAGE CALCULATION
        if 'preface' in book_data:
            preface_data = self.data_manager.get_data(self.language, 'preface')
            if preface_data:
                preface_pages = page_counts.get('preface', 1)
                anchor = generate_anchor_name(preface_data.get('title', 'Preface'))

                start_page = current_page
                end_page = current_page + preface_pages - 1

                self.page_registry.register_section(
                    'preface',
                    preface_data.get('title', 'Preface'),
                    start_page,
                    end_page,
                    anchor
                )
                logger.info(f"Registered preface: pages {start_page} to {end_page} ({preface_pages} pages)")
                current_page += preface_pages

        # Main chapters with REAL page counts
        if 'chapters' in book_data:
            chapters_data = book_data['chapters']
            for chapter_key in natsorted(chapters_data.keys()):
                chapter_data = self.data_manager.get_data(self.language, f'chapters.{chapter_key}')
                if chapter_data:
                    chapter_pages = page_counts.get(f'chapters.{chapter_key}', 1)
                    anchor = generate_anchor_name(chapter_data.get('title', f'Chapter {chapter_key}'))

                    start_page = current_page
                    end_page = current_page + chapter_pages - 1

                    self.page_registry.register_section(
                        f'chapters.{chapter_key}',
                        chapter_data.get('title', f'Chapter {chapter_key}'),
                        start_page,
                        end_page,
                        anchor
                    )
                    logger.info(f"Registered chapter '{chapter_key}': pages {start_page} to {end_page} ({chapter_pages} pages)")
                    current_page += chapter_pages

    def _build_final_document(self, content_builder, book_data):
        """
        Build the final document with accurate TOC.
        """
        # Cover
        CoverBuilder(content_builder, self.data_manager, self.language, self.config, self.page_registry).build()

        # Title and Copyright
        for section_key in ['title', 'copyright']:
            if section_key in book_data:
                builder_class = self._dispatcher.get(section_key)
                if builder_class:
                    self._build_section(builder_class, content_builder, source_path=section_key)

        # Dedication
        if 'dedicate' in book_data:
            self._build_section(ChapterBuilder, content_builder, source_path='dedicate')

        # TOC with accurate page numbers
        toc_data = book_data.get('toc', {'title': 'Table of Contents'})
        toc_builder = TOCBuilder(content_builder, self.data_manager, self.language, self.config, self.page_registry)
        toc_builder.build(toc_data=toc_data)

        # Ensure TOC takes exactly 2 pages
        while (content_builder.page_num - 5) < 2:  # TOC should be on pages 5-6
            content_builder.add_blank_page()

        # Main content
        if 'preface' in book_data:
            self._build_section(ChapterBuilder, content_builder, source_path='preface')

        # Main chapters
        if 'chapters' in book_data and book_data['chapters']:
            chapters_data = book_data['chapters']
            for chapter_key in natsorted(chapters_data.keys()):
                self._build_section(ChapterBuilder, content_builder, source_path=f"chapters.{chapter_key}", is_main_chapter=True)

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
