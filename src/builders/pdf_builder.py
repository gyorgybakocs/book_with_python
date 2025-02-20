from reportlab.lib import colors
from src.builders.base_builder import BaseBuilder
from src.builders.content_builder import ContentBuilder
from src.managers.style_manager import modify_paragraph_style
from src.utils.page_utils import make_page, make_paragraph
from src.logger import logger
from reportlab.platypus import Frame, Paragraph, Frame


class PdfBuilder(BaseBuilder):
    def __init__(self, json_file, paper_book, black_and_white, short, language):
        """Initialize PdfBuilder with PDF-specific attributes."""
        super().__init__(json_file, paper_book=paper_book, black_and_white=black_and_white,
                         short=short, language=language)
        self.page_num = 0

    def run(self):
        """Main process to generate the PDF."""
        title_data = self.data_manager.get_data(self.language, 'title')

        # Create the initial canvas and page size
        self.canvas, self.PAGESIZE = make_page(
            title_data.get("title", "Unknown Title"),
            title_data.get("subtitle", ""),
            "/resources/book",
            self.paper_book,
            self.black_and_white,
            colors.black,
            self.short
        )

        # Create content builder instance
        self.content = ContentBuilder(
            self.canvas,
            self.PAGESIZE,
            self.style_manager,
            self.padding_h,
            self.padding_v
        )

        # Generate the document
        self.create_cover()
        self.create_title_page()
        self.create_copyright_page()

        # Optional sections
        print('************************************** dedicate *****************************************')
        if 'dedicate' in self.data_manager.get_data(self.language):
            self.create_simple_chapter_page(
                self.starting_pos,
                self.starting_pos,
                'dedicate',
                has_title_page=False,
                has_header=False,
                has_footer=False
            )
        print('************************************** preface *****************************************')
        if 'preface' in self.data_manager.get_data(self.language):
            self.create_simple_chapter_page(
                self.padding_v,
                self.starting_pos,
                'preface',
                has_title_page=True,
                has_header=True,
                has_footer=True
            )
        print('************************************** chapters *****************************************')
        if 'chapters' in self.data_manager.get_data(self.language):
            for chapter_name, chapter in self.data_manager.get_data(self.language, 'chapters').items():
                chapter_type = chapter.get('type', "")
                self.create_simple_chapter_page(
                    self.padding_v,
                    self.starting_pos,
                    f'chapters.{chapter_name}',
                    has_title_page=True,
                    has_header=True,
                    has_footer=True
                )
        self.print_page_numbers()
        self.canvas.save()
        logger.info(f"Successfully created the PDF!")

    def create_cover(self):
        """Creates a blank cover page."""
        self.canvas.setFillColor(colors.white)
        self.canvas.rect(0, 0, *self.PAGESIZE, stroke=0, fill=1)
        self.content.new_page()

    def create_title_page(self):
        """Creates a title page."""
        title_data = self.data_manager.get_data(self.language, 'title')

        (self.content
         .start_from(self.starting_pos)
         .add_title(f'<b>{title_data.get("title", "Unknown Title")}</b>', alignment=0, leading='default')
         .add_separator_line()
         .add_subtitle(f'<b>{title_data.get("subtitle", "")}</b>')
         .new_page())

    def create_copyright_page(self):
        """Creates the copyright page."""
        title_data = self.data_manager.get_data(self.language, 'title')
        copyright_data = self.data_manager.get_data(self.language, 'copyright')

        # Build copyright text components
        title = title_data.get("title", "Unknown Title")
        subtitle = title_data.get("subtitle", "")
        author = copyright_data.get('author', "")
        copyright_text = copyright_data.get("copyright_text", "")
        author_text = copyright_data.get('author_text', "")
        design_text = copyright_data.get('design_text', "")
        design = copyright_data.get('design', "")
        publish_text = copyright_data.get('publish_text', "")
        publish = copyright_data.get('publish', "")
        ISBN_pdf = copyright_data.get('ISBN_pdf', "")
        printing_text = copyright_data.get('printing_text', "")
        printing = copyright_data.get('printing', [])
        email_text = copyright_data.get('email_text', "")
        email = copyright_data.get('email', "")

        (self.content
        .start_from(self.starting_pos)
        .add_paragraph(
            f'<b>{title}: {subtitle}</b><br/>by {author}',
            border_padding=0
        )
        .add_paragraph(
            copyright_text,
            border_padding=0,
            extra_spacing=10
        )
        .add_paragraph(
            f'''<span>{author_text}: {author}</span><br/>
                <span>{design_text}: {design}</span><br/>
                <span>{publish_text}: {publish}</span>''' +
            (f'<br/><span>{ISBN_pdf}</span>' if ISBN_pdf else ''),
            border_padding=0,
            extra_spacing=10
        )
        .add_paragraph(
            f'<span>{printing_text}:</span>',
            border_padding=0,
            extra_spacing=10
        ))

        # Add printing items
        printing_text = '<br/>'.join(f'<span>{item}</span>' for item in printing)
        (self.content
         .add_paragraph(
            printing_text,
            border_padding=0,
            extra_spacing=0,
            extra_width=20
        )
         .add_paragraph(
            f'<span>{email_text}: {email}</span>',
            border_padding=0,
            extra_spacing=10
        )
         .new_page())

    def create_simple_chapter_page(self, pos, titlepos, chapter_name,
                                   has_title_page=True, has_header=True,
                                   has_footer=True):
        """Creates a chapter page with configurable options."""
        chapter_data = self.data_manager.get_data(self.language, chapter_name)
        chapter_title = chapter_data.get('title', "")
        chapter_paragraphs = chapter_data.get('paragraphs', [])
        # Title page if needed
        if has_title_page:
            self.content.set_available_height(self.PAGESIZE[1] - titlepos - self.padding_v)
            (self.content
             .start_from(titlepos)
             .add_title(chapter_title, alignment=1, font_size=64, leading=64)
             .new_page())

        # Chapter content
        self.content.set_available_height(self.PAGESIZE[1] - pos - self.padding_v)
        self.content.start_from(pos)

        if has_header:
            (self.content
             .add_header(f'<span>{chapter_title}</span>')
             .add_spacing(6))
        else:
            self.content.add_paragraph(f'<span>{chapter_title}</span>')

        # Add chapter paragraphs
        self.content.add_chapter_paragraphs(
            chapter_paragraphs,
            header_pos=pos,
            chapter_title=chapter_title,
            has_header=has_header,
            has_footer=has_footer
        )

        # Add footer if needed
        if has_footer:
            self.content.add_footer(chapter_title)

        self.content.new_page()

    def print_page_numbers(self):
        """Debug function to print page information."""
        print(f"Page {self.content.page_num}: Last Page")
