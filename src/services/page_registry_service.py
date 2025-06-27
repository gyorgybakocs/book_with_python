class PageRegistryService:
    """
    Service that tracks page numbers for dynamic TOC generation.
    Each page builder registers itself here with start/end pages.
    """

    def __init__(self):
        self.sections = []  # List of {'name', 'title', 'start_page', 'end_page', 'anchor'}
        self.toc_pages = 0  # Will be calculated after TOC generation
        self.toc_insert_position = None  # Where to insert TOC

    def register_section(self, name: str, title: str, start_page: int, end_page: int, anchor: str = None):
        """
        Register a section with its page information.

        Args:
            name: Internal section name (e.g., 'dedicate', 'preface', 'chapter_1')
            title: Display title for TOC
            start_page: Starting page number (before TOC adjustment)
            end_page: Ending page number (before TOC adjustment)
            anchor: HTML anchor for linking (optional)
        """
        section = {
            'name': name,
            'title': title,
            'start_page': start_page,
            'end_page': end_page,
            'anchor': anchor or name,
            'pages_count': end_page - start_page + 1
        }
        self.sections.append(section)

    def set_toc_insert_position(self, after_page: int):
        """
        Set where the TOC should be inserted.

        Args:
            after_page: Insert TOC after this page number
        """
        self.toc_insert_position = after_page

    def calculate_adjusted_page_numbers(self, toc_pages: int) -> list:
        """
        Calculate adjusted page numbers after TOC insertion.

        Args:
            toc_pages: Number of pages the TOC will take

        Returns:
            List of sections with adjusted page numbers
        """
        self.toc_pages = toc_pages
        adjusted_sections = []

        for section in self.sections:
            adjusted_section = section.copy()

            # If section starts after TOC insertion point, adjust pages
            if section['start_page'] > self.toc_insert_position:
                adjusted_section['start_page'] = section['start_page'] + toc_pages
                adjusted_section['end_page'] = section['end_page'] + toc_pages
                adjusted_section['adjusted'] = True
            else:
                adjusted_section['adjusted'] = False

            adjusted_sections.append(adjusted_section)

        return adjusted_sections

    def get_toc_entries(self) -> list:
        """
        Get entries for TOC generation (before adjustment).

        Returns:
            List of TOC entries with original page numbers
        """
        toc_entries = []

        for section in self.sections:
            # Skip cover and title pages from TOC
            if section['name'] in ['cover', 'title', 'copyright']:
                continue

            entry = {
                'title': section['title'],
                'page': section['start_page'],
                'anchor': section['anchor'],
                'is_chapter': section['name'].startswith('chapter_'),
                'is_main_chapter': section['name'].startswith('chapters.')
            }
            toc_entries.append(entry)

        return toc_entries

    def estimate_toc_pages(self, entries_per_page: int = 25) -> int:
        """
        Estimate how many pages the TOC will need.

        Args:
            entries_per_page: Approximate entries that fit on one page

        Returns:
            Estimated number of TOC pages
        """
        toc_entries = self.get_toc_entries()
        total_entries = len(toc_entries)

        # Add some buffer for headers and spacing
        estimated_pages = max(1, (total_entries + 5) // entries_per_page)

        return estimated_pages

    def get_sections_summary(self) -> str:
        """Get a summary of all registered sections for debugging."""
        summary = "REGISTERED SECTIONS:\n"
        for section in self.sections:
            summary += f"  {section['name']}: '{section['title']}' (pages {section['start_page']}-{section['end_page']})\n"
        return summary

    def clear(self):
        """Clear all registered sections (for testing)."""
        self.sections = []
        self.toc_pages = 0
        self.toc_insert_position = None
