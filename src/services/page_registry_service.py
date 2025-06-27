from src.logger import logger

class PageRegistryService:
    """
    Service that tracks page numbers for dynamic TOC generation.
    UPDATED for Fixed TOC Position approach.
    """

    def __init__(self):
        self.sections = []  # List of {'name', 'title', 'start_page', 'end_page', 'anchor'}
        self.toc_position = 5  # Fixed TOC position
        self.toc_pages = 2     # Fixed TOC size

    def register_section(self, name: str, title: str, start_page: int, end_page: int, anchor: str = None):
        """
        Register a section with its page information.
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
        logger.debug(f"Registered section: {name} -> {title} (pages {start_page}-{end_page})")

    def get_toc_entries(self) -> list:
        """
        Get entries for TOC generation.
        In Fixed TOC approach, these are pre-calculated.
        """
        toc_entries = []
        seen_sections = set()  # Track seen section names to avoid duplicates

        for section in self.sections:
            # Skip sections that shouldn't appear in TOC
            if section['name'] in ['cover', 'title', 'copyright', 'toc']:
                continue

            # Skip duplicates
            if section['name'] in seen_sections:
                logger.debug(f"Skipping duplicate section: {section['name']}")
                continue

            seen_sections.add(section['name'])

            entry = {
                'title': section['title'],
                'page': section['start_page'],
                'anchor': section['anchor'],
                'is_chapter': section['name'].startswith('chapter_'),
                'is_main_chapter': section['name'].startswith('chapters.')
            }
            toc_entries.append(entry)

        # Sort by page number to ensure correct order
        toc_entries.sort(key=lambda x: x['page'])

        logger.info(f"Generated {len(toc_entries)} TOC entries (duplicates removed)")
        return toc_entries

    def get_sections_summary(self) -> str:
        """Get a summary of all registered sections for debugging."""
        summary = "REGISTERED SECTIONS (Fixed TOC approach):\n"
        summary += f"TOC Position: Page {self.toc_position} (reserved {self.toc_pages} pages)\n"

        # Sort sections by start page
        sorted_sections = sorted(self.sections, key=lambda x: x['start_page'])

        for section in sorted_sections:
            summary += f"  {section['name']}: '{section['title']}' (pages {section['start_page']}-{section['end_page']})\n"
        return summary

    def clear(self):
        """Clear all registered sections (for testing)."""
        self.sections = []

    # Legacy methods for compatibility (not used in Fixed approach)
    def set_toc_insert_position(self, after_page: int):
        """Legacy method - not used in Fixed TOC approach."""
        pass

    def calculate_adjusted_page_numbers(self, toc_pages: int) -> list:
        """Legacy method - not needed in Fixed TOC approach."""
        return self.sections

    def estimate_toc_pages(self, entries_per_page: int = 25) -> int:
        """Returns the fixed TOC size."""
        return self.toc_pages
