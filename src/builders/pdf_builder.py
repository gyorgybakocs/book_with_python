from src.builders.base_builder import BaseBuilder


class PdfBuilder(BaseBuilder):

    def __init__(self, json_file, paper_book, black_and_white, short, language):
        """
        Initialize PdfBuilder with PDF-specific attributes.
        """
        super().__init__(json_file, format_type="pdf", paper_book=paper_book, black_and_white=black_and_white, short=short, language=language)
        # Additional PDF-specific initialization if needed

    def run(self):
        print("Running PDF builder logic...")

        print(f'paper_book {self.paper_book}')
        print(f'black_and_white {self.black_and_white}')
        print(f'short {self.short}')
        print(f'language {self.language}')

        print(f'data {self.data}')


