from src.builders.page_builders.base_page_builder import BasePageBuilder
from src.logger import logger
from reportlab.platypus import Table, TableStyle
from reportlab.platypus.paragraph import Paragraph

class TOCBuilder(BasePageBuilder):
    """
    Builds Table of Contents with FIXED POSITION approach.
    Uses pre-registered page numbers from PageRegistryService.
    """

    def __init__(self, content_builder, data_manager, language, config, page_registry):
        super().__init__(content_builder, data_manager, language, config)
        self.page_registry = page_registry
        # Get style_manager from content_builder
        self.style_manager = content_builder.style_manager

    def build(self, source_path: str = None, toc_data: dict = None, **options):
        """
        Builds the TOC with FIXED POSITION approach.
        Page numbers come from pre-registered sections.
        """
        if not toc_data:
            toc_data = self.data_manager.get_data(self.language, 'toc') or {
                'title': 'Table of Contents'
            }

        # Get TOC entries from registry (pre-registered)
        toc_entries = self.page_registry.get_toc_entries()

        if not toc_entries:
            logger.warning("No TOC entries found in registry - building basic TOC")
            # DEBUG: Let's see what's in the registry
            logger.debug("Registry contents: " + self.page_registry.get_sections_summary())
            self._build_empty_toc(toc_data)
            return

        logger.info(f"Building TOC with {len(toc_entries)} pre-registered entries")

        # Record start page for TOC itself
        start_page = self.content.page_num

        # Build the TOC
        self._build_fixed_toc(toc_data, toc_entries)

        # Record end page
        end_page = self.content.page_num - 1

        # Register TOC itself (it won't appear in its own listing)
        self.register_section('toc', toc_data.get("title", "Table of Contents"), start_page, end_page, 'toc')

    def _build_fixed_toc(self, toc_data: dict, toc_entries: list):
        """
        Builds TOC with pre-calculated page numbers.
        """
        # Start TOC
        starting_pos = self.config.get("common.padding.vertical")
        self.content.start_from(starting_pos)

        # Add TOC title
        toc_title = toc_data.get("title", "Table of Contents")
        self.content.add_paragraph(f'<a name="toc"/><b>{toc_title}</b>', style_name='title_sub', alignment=1)
        self.content.add_spacing(30)

        logger.info(f"Adding {len(toc_entries)} TOC entries with pre-calculated page numbers")

        # Add each TOC entry
        for entry in toc_entries:
            title = entry['title']
            page = entry['page']
            anchor = entry['anchor']

            # Create dots for spacing (adjust length based on title)
            title_length = len(title)
            dots_count = max(10, 50 - title_length)  # Adaptive dot count
            dots = ' . ' * (dots_count // 3)

            # TEMPORARY: Skip problematic anchors
            if anchor in ['tul_a_szabalyokon_az_angol_igeid_k_valos_kihivasai', 'modellezzuk_le_a_valosagot_az_igeid_k_uj_megkozelitese']:
                # Format without links for problematic anchors
                if entry.get('is_main_chapter', False):
                    toc_line = f'&nbsp;&nbsp;&nbsp;&nbsp;<b>{title}</b>{dots}<b>{page}</b>'
                else:
                    toc_line = f'{title}{dots}{page}'
            else:
                # Format entry based on type - AS HTML STRINGS (like old code)
                if entry.get('is_main_chapter', False):
                    # Main chapter - indent and bold
                    toc_line = f'&nbsp;&nbsp;&nbsp;&nbsp;<b><a href="#{anchor}">{title}</a></b>{dots}<b>{page}</b>'
                else:
                    # Regular section
                    toc_line = f'<a href="#{anchor}">{title}</a>{dots}{page}'

            # Create a table for proper alignment (title left, page number right)
            from reportlab.platypus import Table, TableStyle
            from reportlab.platypus.paragraph import Paragraph

            # Left part (title) - ALL ANCHORS ENABLED!
            if entry.get('is_main_chapter', False):
                left_part = f'<b><a href="#{anchor}">{title}</a></b>'  # NO INDENT, WITH LINK!
            else:
                left_part = f'<a href="#{anchor}">{title}</a>'  # WITH LINK!

            # Right part (page number)
            if entry.get('is_main_chapter', False):
                right_part = f'<b>{page}</b>'
            else:
                right_part = str(page)

            # Create table row for proper alignment
            toc_row_data = [
                [Paragraph(left_part, self.style_manager.get_style('paragraph_default')),
                 Paragraph(right_part, self.style_manager.prepare_style('paragraph_default', alignment=2))]
            ]

            # Create table with proper column widths
            available_width = self.content.page_size[0] - 2 * self.config.get("common.padding.horizontal")
            toc_table = Table(toc_row_data, colWidths=[available_width - 40, 40])

            # Table style for clean TOC
            toc_table.setStyle(TableStyle([
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                ('VALIGN', (0, 0), (-1, -1), 'TOP')
            ]))

            # Draw the table
            width = self.content.page_size[0] - 2 * self.config.get("common.padding.horizontal")
            w, h = toc_table.wrapOn(self.content.canvas, width, 20)
            y_pos = self.content.page_size[1] - self.content.current_pos - h
            toc_table.drawOn(self.content.canvas, self.config.get("common.padding.horizontal"), y_pos)

            self.content.current_pos += h + 3  # Add small spacing between entries

        # Add some bottom spacing
        self.content.add_spacing(20)

        # IMPORTANT: End the TOC page properly
        self.content.new_page()

        logger.info("TOC content built successfully")

    def _build_empty_toc(self, toc_data: dict):
        """
        Builds a minimal TOC when no entries are available.
        """
        starting_pos = self.config.get("common.padding.vertical")
        self.content.start_from(starting_pos)

        toc_title = toc_data.get("title", "Table of Contents")
        self.content.add_paragraph(f'<a name="toc"/><b>{toc_title}</b>', style_name='title_sub', alignment=1)
        self.content.add_spacing(30)

        self.content.add_paragraph("(Content will be available in final version)", style_name='paragraph_default', alignment=1)

        # IMPORTANT: End the TOC page properly
        self.content.new_page()

        logger.warning("Built empty TOC - no pre-registered sections found")

    def calculate_actual_pages_used(self) -> int:
        """
        Calculate how many pages the TOC actually used.
        This can be called after building to get accurate count.
        """
        # In the fixed approach, we'll always use the reserved space
        return 2  # Fixed reservation