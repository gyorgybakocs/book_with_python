from .base_page_builder import BasePageBuilder

class TitlePageBuilder(BasePageBuilder):
    """Builds the main title page of the book."""
    def build(self, source_path: str = None, **options):
        starting_pos = self.config.get("defaults.starting_pos")
        title_data = self.data_manager.get_data(self.language, 'title')

        start_page = self.content.page_num

        (self.content
         .start_from(starting_pos)
         .add_title(f'<a name="title"/><b>{title_data.get("title", "Unknown Title")}</b>', alignment=0, extra_spacing=5)
         .add_separator_line()
         .add_subtitle(f'<b>{title_data.get("subtitle", "")}</b>', alignment=2)
         .new_page())

        end_page = self.content.page_num - 1
        self.register_section('title', title_data.get("title", "Unknown Title"), start_page, end_page, 'title')
