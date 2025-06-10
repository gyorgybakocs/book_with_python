from .base_page_builder import BasePageBuilder

class TitlePageBuilder(BasePageBuilder):
    """Builds the main title page of the book."""
    def build(self, source_path: str = None, **options):
        starting_pos = self.config.get("defaults.starting_pos")
        title_data = self.data_manager.get_data(self.language, 'title')

        (self.content
         .start_from(starting_pos)
         .add_title(f'<b>{title_data.get("title", "Unknown Title")}</b>', alignment=0)
         .add_separator_line()
         .add_subtitle(f'<b>{title_data.get("subtitle", "")}</b>')
         .new_page())
