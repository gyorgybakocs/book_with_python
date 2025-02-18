from src.builders.base_builder import BaseBuilder


class EpubBuilder(BaseBuilder):

    def __init__(self, json_file, epub_type):
        """
        Initialize EpubBuilder with EPUB-specific attributes.
        """
        super().__init__(json_file, format_type="epub", epub_type=epub_type)
        # Additional EPUB-specific initialization if needed

    def run(self):
        print("Running EPUB builder logic...")
