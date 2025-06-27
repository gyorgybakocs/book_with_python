from src.builders.page_builders.base_page_builder import BasePageBuilder
from src.logger import logger

class TOCBuilder(BasePageBuilder):
    """
    Builds Table of Contents with dynamic page numbers.
    Uses PageRegistryService to get accurate page numbers.
    """

    def __init__(self, content_builder, data_manager, language, config, page_registry):
        super().__init__(content_builder, data_manager, language, config)
        self.page_registry = page_registry

    def build(self, source_path: str = None, toc_data: dict = None, **options):
        """
        Builds the TOC with dynamic page numbers.
        """
        if not toc_data:
            # Try to get from data manager, but don't fail if missing
            toc_data = self.data_manager.get_data(self.language, 'toc') or {
                'title': 'Table of Contents'
            }

        # Get TOC entries from registry
        toc_entries = self.page_registry.get_toc_entries()

        if not toc_entries:
            logger.warning("No TOC entries found in registry")
            return

        logger.info(f"Building TOC with {len(toc_entries)} entries")

        # Build the TOC without complex page calculations for now
        self._build_simple_toc(toc_data, toc_entries)

    def _build_simple_toc(self, toc_data: dict, toc_entries: list):
        """
        Builds a simple TOC page.
        """
        # Start TOC
        starting_pos = self.config.get("common.padding.vertical")
        self.content.start_from(starting_pos)

        # Add TOC title
        toc_title = toc_data.get("title", "Table of Contents")
        self.content.add_paragraph(f'<b>{toc_title}</b>', style_name='title_sub', alignment=2)
        self.content.add_spacing(30)

        logger.info(f"Adding {len(toc_entries)} TOC entries")

        # Add each TOC entry
        for entry in toc_entries:
            title = entry['title']
            page = entry['page']
            anchor = entry['anchor']

            # Create dots for spacing
            dots = ' . ' * 40

            # Format entry based on type - WITH WORKING LINKS
            if entry.get('is_main_chapter', False):
                # Main chapter - indent
                toc_line = f'&nbsp;&nbsp;&nbsp;&nbsp;<a href="#{anchor}">{title}</a>{dots}{page}'
            else:
                # Regular section
                toc_line = f'<a href="#{anchor}">{title}</a>{dots}{page}'

            self.content.add_paragraph(toc_line, style_name='paragraph_default')
            self.content.add_spacing(5)

        # End TOC page
        self.content.add_footer("Table of Contents")
        self.content.new_page()

        logger.info("TOC built successfully")

    def _add_toc_entry(self, section: dict):
        """
        Add a single TOC entry.
        """
        title = section['title']
        page_num = section['start_page'] if not section['adjusted'] else section['start_page']
        anchor = section['anchor']

        # Create entry with dots and page number
        dots = ' . ' * 50  # Long string of dots

        if section['name'].startswith('chapters.'):
            # Main chapter - indent
            entry_text = f'&nbsp;&nbsp;&nbsp;&nbsp;<a href="#{anchor}">{title}</a>'
        else:
            # Regular section
            entry_text = f'<a href="#{anchor}">{title}</a>'

        # Create the TOC line with dots and page number
        self._create_toc_line(entry_text, page_num, dots)

    def _create_toc_line(self, title_text: str, page_num: int, dots: str):
        """
        Creates a TOC line with title, dots, and page number.
        Uses a table layout to align properly.
        """
        # For now, use simple paragraph approach
        # This could be enhanced with tables for better alignment

        full_line = f'{title_text}{dots}{page_num}'

        # Add the TOC line
        self.content.add_paragraph(full_line, style_name='paragraph_default')
        self.content.add_spacing(4)

    def calculate_actual_pages_used(self) -> int:
        """
        Calculate how many pages the TOC actually used.
        This can be called after building to get accurate count.
        """
        # This would need to be implemented based on actual content built
        # For now, return the estimate
        return self.page_registry.estimate_toc_pages()