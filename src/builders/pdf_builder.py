from natsort import natsorted
from reportlab.lib import colors

from src.builders.base_builder import BaseBuilder
from src.builders.content_builder import ContentBuilder
from src.utils.page_utils import make_page
from src.logger import logger

from .page_builders.cover_builder import CoverBuilder
from .page_builders.title_page_builder import TitlePageBuilder
from .page_builders.copyright_page_builder import CopyrightPageBuilder
from .page_builders.chapter_builder import ChapterBuilder

class PdfBuilder(BaseBuilder):
    """
    Acts as a director for the PDF generation process.
    It reads the book's structure implicitly from the data's keys and dispatches
    the building task for each section to a specialized PageBuilder class.
    """
    def __init__(self, json_file, paper_book, black_and_white, short, language):
        super().__init__(json_file, paper_book=paper_book, black_and_white=black_and_white,
                         short=short, language=language)

        self._dispatcher = {
            'title': TitlePageBuilder,
            'copyright': CopyrightPageBuilder,
            'dedicate': ChapterBuilder,
            'preface': ChapterBuilder,
            # 'chapters' key will be handled specially in the run method.
        }

    def run(self):
        """
        Main process to generate the PDF. It iterates through the book's
        data keys and uses the dispatcher to build each part in the order
        they appear in the JSON file.
        """
        book_data = self.data_manager.get_data(language=self.language)
        if not book_data:
            logger.error(f"No book data found for language '{self.language}'. Aborting.")
            return

        title_info = book_data.get("title", {})
        canvas, pagesize = make_page(
            title_info.get("title", "Unknown Title"),
            title_info.get("subtitle", ""),
            self.config.get("paths.output_dir"),
            self.paper_book, self.black_and_white, colors.black, self.short
        )
        content_builder = ContentBuilder(
            canvas, pagesize, self.style_manager,
            self.config.get("common.padding.horizontal"),
            self.config.get("common.padding.vertical")
        )

        CoverBuilder(content_builder, self.data_manager, self.language, self.config).build()

        for section_key in book_data:
            if section_key == 'chapters':
                continue

            builder_class = self._dispatcher.get(section_key)
            if builder_class:
                self._build_section(builder_class, content_builder, source_path=section_key)
            else:
                logger.warning(f"No builder found for section key '{section_key}'. Skipping.")

        if 'chapters' in book_data and book_data['chapters']:
            logger.info("--- Building Main Chapters ---")
            chapters_data = book_data['chapters']
            for chapter_key in natsorted(chapters_data.keys()):
                self._build_section(ChapterBuilder, content_builder, source_path=f"chapters.{chapter_key}", is_main_chapter=True)

        canvas.save()
        logger.info("Successfully created the PDF!")

    def _build_section(self, builder_class, content_builder, source_path=None, **options):
        """
        Instantiates and runs a specialized page builder.
        """
        try:
            page_builder = builder_class(
                content_builder, self.data_manager, self.language, self.config
            )
            page_builder.build(source_path=source_path, **options)
            logger.info(f"Successfully built section from source: '{source_path or 'N/A'}'")
        except Exception as e:
            logger.error(f"Failed to build section from source '{source_path}': {e}", exc_info=True)

# from reportlab.lib import colors
# from src.builders.base_builder import BaseBuilder
# from src.builders.content_builder import ContentBuilder
# from src.managers.style_manager import modify_paragraph_style
# from src.utils.page_utils import make_page, make_paragraph
# from src.logger import logger
# from reportlab.platypus import Frame, Paragraph, Frame
#
#
# class PdfBuilder(BaseBuilder):
#     def __init__(self, json_file, paper_book, black_and_white, short, language):
#         """Initialize PdfBuilder with PDF-specific attributes."""
#         super().__init__(json_file, paper_book=paper_book, black_and_white=black_and_white,
#                          short=short, language=language)
#         self.page_num = 0
#
#     def run(self):
#         """Main process to generate the PDF."""
#         title_data = self.data_manager.get_data(self.language, 'title')
#
#         # Create the initial canvas and page size
#         self.canvas, self.PAGESIZE = make_page(
#             title_data.get("title", "Unknown Title"),
#             title_data.get("subtitle", ""),
#             "/resources/book",
#             self.paper_book,
#             self.black_and_white,
#             colors.black,
#             self.short
#         )
#
#         # Create content builder instance
#         self.content = ContentBuilder(
#             self.canvas,
#             self.PAGESIZE,
#             self.style_manager,
#             self.padding_h,
#             self.padding_v
#         )
#
#         # Generate the document
#         self.create_cover()
#         self.create_title_page()
#         self.create_copyright_page()
#
#         # Optional sections
#         print('************************************** dedicate *****************************************')
#         if 'dedicate' in self.data_manager.get_data(self.language):
#             self.create_simple_chapter_page(
#                 self.starting_pos,
#                 self.starting_pos,
#                 'dedicate',
#                 has_title_page=False,
#                 has_header=False,
#                 has_footer=False
#             )
#         print('************************************** preface *****************************************')
#         if 'preface' in self.data_manager.get_data(self.language):
#             self.create_simple_chapter_page(
#                 self.padding_v,
#                 self.starting_pos,
#                 'preface',
#                 has_title_page=True,
#                 has_header=True,
#                 has_footer=True
#             )
#         print('************************************** chapters *****************************************')
#         if 'chapters' in self.data_manager.get_data(self.language):
#             for chapter_name, chapter in self.data_manager.get_data(self.language, 'chapters').items():
#                 chapter_type = chapter.get('type', "")
#                 self.create_simple_chapter_page(
#                     self.padding_v,
#                     self.starting_pos,
#                     f'chapters.{chapter_name}',
#                     has_title_page=True,
#                     has_header=True,
#                     has_footer=True
#                 )
#         self.print_page_numbers()
#         self.canvas.save()
#         logger.info(f"Successfully created the PDF!")
#
#     def create_cover(self):
#         """Creates a blank cover page."""
#         self.canvas.setFillColor(colors.white)
#         self.canvas.rect(0, 0, *self.PAGESIZE, stroke=0, fill=1)
#         self.content.new_page()
#
#     def create_title_page(self):
#         """Creates a title page."""
#         title_data = self.data_manager.get_data(self.language, 'title')
#
#         (self.content
#          .start_from(self.starting_pos)
#          .add_title(f'<b>{title_data.get("title", "Unknown Title")}</b>', alignment=0, leading='default')
#          .add_separator_line()
#          .add_subtitle(f'<b>{title_data.get("subtitle", "")}</b>')
#          .new_page())
#
#     def create_copyright_page(self):
#         """Creates the copyright page."""
#         title_data = self.data_manager.get_data(self.language, 'title')
#         copyright_data = self.data_manager.get_data(self.language, 'copyright')
#
#         # Build copyright text components
#         title = title_data.get("title", "Unknown Title")
#         subtitle = title_data.get("subtitle", "")
#         author = copyright_data.get('author', "")
#         copyright_text = copyright_data.get("copyright_text", "")
#         author_text = copyright_data.get('author_text', "")
#         design_text = copyright_data.get('design_text', "")
#         design = copyright_data.get('design', "")
#         publish_text = copyright_data.get('publish_text', "")
#         publish = copyright_data.get('publish', "")
#         ISBN_pdf = copyright_data.get('ISBN_pdf', "")
#         printing_text = copyright_data.get('printing_text', "")
#         printing = copyright_data.get('printing', [])
#         email_text = copyright_data.get('email_text', "")
#         email = copyright_data.get('email', "")
#
#         (self.content
#         .start_from(self.starting_pos)
#         .add_paragraph(
#             f'<b>{title}: {subtitle}</b><br/>by {author}',
#             border_padding=0
#         )
#         .add_paragraph(
#             copyright_text,
#             border_padding=0,
#             extra_spacing=10
#         )
#         .add_paragraph(
#             f'''<span>{author_text}: {author}</span><br/>
#                 <span>{design_text}: {design}</span><br/>
#                 <span>{publish_text}: {publish}</span>''' +
#             (f'<br/><span>{ISBN_pdf}</span>' if ISBN_pdf else ''),
#             border_padding=0,
#             extra_spacing=10
#         )
#         .add_paragraph(
#             f'<span>{printing_text}:</span>',
#             border_padding=0,
#             extra_spacing=10
#         ))
#
#         # Add printing items
#         printing_text = '<br/>'.join(f'<span>{item}</span>' for item in printing)
#         (self.content
#          .add_paragraph(
#             printing_text,
#             border_padding=0,
#             extra_spacing=0,
#             extra_width=20
#         )
#          .add_paragraph(
#             f'<span>{email_text}: {email}</span>',
#             border_padding=0,
#             extra_spacing=10
#         )
#          .new_page())
#
#     def create_simple_chapter_page(self, pos, titlepos, chapter_name,
#                                    has_title_page=True, has_header=True,
#                                    has_footer=True):
#         """Creates a chapter page with configurable options."""
#         chapter_data = self.data_manager.get_data(self.language, chapter_name)
#         chapter_title = chapter_data.get('title', "")
#         chapter_paragraphs = chapter_data.get('paragraphs', [])
#         # Title page if needed
#         if has_title_page:
#             self.content.set_available_height(self.PAGESIZE[1] - titlepos - self.padding_v)
#             (self.content
#              .start_from(titlepos)
#              .add_title(chapter_title, alignment=1, font_size=64, leading=64)
#              .new_page())
#
#         # Chapter content
#         self.content.set_available_height(self.PAGESIZE[1] - pos - self.padding_v)
#         self.content.start_from(pos)
#
#         if has_header:
#             (self.content
#              .add_header(f'<span>{chapter_title}</span>')
#              .add_spacing(6))
#         else:
#             self.content.add_paragraph(f'<span>{chapter_title}</span>')
#
#         # Add chapter paragraphs
#         self.content.add_chapter_paragraphs(
#             chapter_paragraphs,
#             header_pos=pos,
#             chapter_title=chapter_title,
#             has_header=has_header,
#             has_footer=has_footer
#         )
#
#         # Add footer if needed
#         if has_footer:
#             self.content.add_footer(chapter_title)
#
#         self.content.new_page()
#
#     def print_page_numbers(self):
#         """Debug function to print page information."""
#         print(f"Page {self.content.page_num}: Last Page")
