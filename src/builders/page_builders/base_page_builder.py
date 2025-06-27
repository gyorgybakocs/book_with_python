from abc import ABC, abstractmethod

class BasePageBuilder(ABC):
    """
    Abstract base class for all specialized page builders.
    Defines the common interface and constructor for building a section of the book.
    """
    def __init__(self, content_builder, data_manager, language, config, page_registry=None):
        """
        Initializes the page builder with necessary context.

        Args:
            content_builder (ContentBuilder): The helper object for creating PDF content.
            data_manager (DataManager): The service for accessing book data.
            language (str): The language of the content to build.
            config (ConfigService): The application's configuration service.
            page_registry (PageRegistryService): Service for tracking page numbers.
        """
        self.content = content_builder
        self.data_manager = data_manager
        self.language = language
        self.config = config
        self.page_registry = page_registry

    def register_section(self, name: str, title: str, start_page: int, end_page: int, anchor: str = None):
        """
        Helper method to register this section with the page registry.
        """
        if self.page_registry:
            self.page_registry.register_section(name, title, start_page, end_page, anchor)

    @abstractmethod
    def build(self, source_path: str = None, **options):
        """
        The main method to build the specific page or section. This must be
        implemented by all concrete subclasses.

        Args:
            source_path (str, optional): The dot-notation path to the data
                                         for this section. Defaults to None.
            **options: Additional flags or settings for the builder.
        """
        pass