from pydantic import BaseModel, field_validator
from typing import List, Dict, Optional

class Title(BaseModel):
    """Defines the structure for the book's title and subtitle."""
    title: str
    subtitle: str

class Copyright(BaseModel):
    """Defines the structure for all copyright page information."""
    copyright_text: str
    author_text: str
    author: str
    design_text: str
    design: str
    publish_text: str
    publish: str
    ISBN_pdf: str
    ISBN_epub: str
    ISBN_print: str
    printing_text: str
    printing: List[str]
    email_text: str
    email: str

class Chapter(BaseModel):
    """Defines the structure for a generic content chapter (like dedicate, preface, or main chapters)."""
    title: str
    paragraphs: List[str]
    type: Optional[str] = "simple"

class Book(BaseModel):
    """
    Defines the structure for a single language version of the book.
    It specifies which sections are mandatory and which are optional.
    """
    title: Title
    copyright: Copyright
    chapters: Dict[str, Chapter]
    dedicate: Optional[Chapter] = None
    preface: Optional[Chapter] = None

    @field_validator('chapters')
    def chapters_must_not_be_empty(cls, v):
        """Ensures the 'chapters' dictionary is not empty."""
        if not v:
            raise ValueError('chapters dictionary must not be empty')
        return v

class BookData(BaseModel):
    """
    The root model for the entire book_01.json data file.
    It expects a key for each language.
    """
    book_hu: Book
    book_en: Book
