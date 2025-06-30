from .base_page_builder import BasePageBuilder

class CopyrightPageBuilder(BasePageBuilder):
    """Builds the copyright page."""
    def build(self, source_path: str = None, **options):
        starting_pos = self.config.get("defaults.starting_pos") - 50
        title_data = self.data_manager.get_data(self.language, 'title')
        copyright_data = self.data_manager.get_data(self.language, 'copyright')

        start_page = self.content.page_num

        title = title_data.get("title", "Unknown Title")
        subtitle = title_data.get("subtitle", "")
        author = copyright_data.get('author', "")
        printing_items_html = '<br/>'.join(f'<span>{item}</span>' for item in copyright_data.get('printing', []))

        (self.content
         .start_from(starting_pos)
         .add_paragraph(f'<a name="copyright"/><b>{title}: {subtitle}</b> by {author}', border_padding=0, extra_spacing=10)
         .add_paragraph(copyright_data.get("copyright", ""), border_padding=0, extra_spacing=10)
         .add_paragraph(copyright_data.get("copyright_text", ""), border_padding=0, extra_spacing=10)
         .add_paragraph(
            f'''<span>{copyright_data.get('author_text', '')}: {author}</span><br/>
                    <span>{copyright_data.get('design_text', '')}: {copyright_data.get('design', '')}</span><br/>
                    <span>{copyright_data.get('publish_text', '')}: {copyright_data.get('publish', '')}</span>''' +
            (f'<br/><span>{copyright_data.get("ISBN_pdf", "")}</span>' if copyright_data.get("ISBN_pdf") else ''),
            border_padding=0, extra_spacing=10
        )
         .add_paragraph(f'<span>{copyright_data.get("printing_text", "")}:</span>', border_padding=0)
         .add_paragraph(printing_items_html, leftIndent=20, extra_spacing=10)
         .add_paragraph(f'<span>{copyright_data.get("email_text", "")}: {copyright_data.get("email", "")}</span>', border_padding=0, extra_spacing=10)
         .new_page())

        end_page = self.content.page_num - 1
        self.register_section('copyright', 'Copyright', start_page, end_page, 'copyright')