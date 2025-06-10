from .base_page_builder import BasePageBuilder

class CoverBuilder(BasePageBuilder):
    """Builds the cover page (which is currently just a blank page)."""
    def build(self, source_path: str = None, **options):
        self.content.add_blank_page()
