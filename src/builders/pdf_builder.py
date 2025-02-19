import os
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from src.builders.base_builder import BaseBuilder
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib import pagesizes
from src.logger import logger


from src.helpers.builder import modify_paragraph_style, make_page


class PdfBuilder(BaseBuilder):

    def __init__(self, json_file, paper_book, black_and_white, short, language):
        """
        Initialize PdfBuilder with PDF-specific attributes.
        """
        super().__init__(json_file, format_type="pdf", paper_book=paper_book, black_and_white=black_and_white, short=short, language=language)
        # Additional PDF-specific initialization if needed

    def run(self):
        """Main process to generate the PDF."""
        # Create the initial canvas
        book_data = self.data[f'book_{self.language}']
        # Use make_page() to create the canvas and page size
        self.canvas, self.PAGESIZE = make_page(
            book_data.get("title", "Unknown Title"),
            book_data.get("subtitle", ""),
            "/resources/book",
            self.paper_book,
            self.black_and_white,
            colors.black,
            self.short
        )

        # Add a cover page
        self.create_cover()
        # Add the title page
        self.create_title_page()

        self.print_page_numbers()

        # Save the PDF
        self.canvas.save()

        logger.info(f"Successfully created the PDF!")

    def create_cover(self):
        """Creates a blank cover page."""
        self.canvas.setFillColor(colors.white)
        self.canvas.rect(0, 0, *self.PAGESIZE, stroke=0, fill=1)
        self.page_num += 1
        self.canvas.showPage()

    def create_title_page(self):
        """Creates a title page using dynamically generated styles."""
        book_data = self.data.get(f"book_{self.language}", {})
        title = book_data.get("title", "Unknown Title")
        subtitle = book_data.get("subtitle", "")

        pos = self.starting_pos

        # 🔥 Generate left-aligned title style dynamically
        title_style = modify_paragraph_style(self.title_main, alignment=0)
        pos = self.make_paragraph(pos, f'<b>{title}</b>', title_style)

        # 🔥 Underline separator
        self.canvas.line(self.padding_h, self.PAGESIZE[1] - pos, self.PAGESIZE[0] - self.padding_h, self.PAGESIZE[1] - pos)

        # 🔥 Generate right-aligned subtitle style dynamically
        subtitle_style = modify_paragraph_style(self.title_sub, alignment=2)
        self.make_paragraph(pos, f'<b>{subtitle}</b>', subtitle_style)

        self.page_num += 1
        self.canvas.showPage()

    def print_page_numbers(self):
        """Prints all recorded page numbers with their corresponding types."""
        print(f"Page {self.page_num}: Cover Page")
        print(f"Page {self.page_num}: Title Page")
