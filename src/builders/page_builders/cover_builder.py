from .base_page_builder import BasePageBuilder

class CoverBuilder(BasePageBuilder):
    """Builds the cover page (which is currently just a blank page)."""
    def build(self, source_path: str = None, **options):
        start_page = self.content.page_num
        self.content.add_blank_page()
        end_page = self.content.page_num - 1
        self.register_section('cover', 'Cover', start_page, end_page, 'cover')
