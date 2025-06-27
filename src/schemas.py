from pydantic import BaseModel, field_validator
from typing import List, Dict, Optional, Union, Literal

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

class ParagraphContent(BaseModel):
    """Content item for paragraphs."""
    type: Literal["paragraph"]
    text: str

class ImageContent(BaseModel):
    """Content item for images."""
    type: Literal["image"]
    src: str  # Image filename
    alignment: Literal["left", "center", "right"] = "center"
    width: Union[int, str] = 300  # Allow both int and string (for percentages)
    height: Union[int, Literal["auto"], str] = "auto"  # Allow int, "auto", or string (for percentages)
    caption: Optional[str] = None

    @field_validator('src')
    @classmethod
    def validate_image_format(cls, v):
        """Validate that image is JPEG or PNG."""
        if not v.lower().endswith(('.jpg', '.jpeg', '.png')):
            raise ValueError('Only JPEG and PNG images are supported')
        return v

    @field_validator('width')
    @classmethod
    def validate_width(cls, v):
        """Validate image width - allow int, percentage string, or 'auto'."""
        if isinstance(v, int):
            if v <= 0 or v > 2000:
                raise ValueError('Width must be between 1 and 2000 pixels')
        elif isinstance(v, str):
            if v == "auto":
                return v  # Allow "auto" for width
            elif v.endswith('%'):
                try:
                    percentage = float(v.rstrip('%'))
                    if percentage <= 0:
                        raise ValueError('Width percentage must be greater than 0%')
                    # Auto-correct percentages over 100%
                    if percentage > 100:
                        return "100%"
                except ValueError:
                    raise ValueError('Invalid percentage format')
            else:
                raise ValueError('Width string must be "auto" or a percentage (e.g., "100%")')
        return v

    @field_validator('height')
    @classmethod
    def validate_height(cls, v):
        """Validate image height - allow int, "auto", or percentage string."""
        if v == "auto":
            return v
        elif isinstance(v, int):
            if v <= 0 or v > 2000:
                raise ValueError('Height must be "auto" or between 1 and 2000 pixels')
        elif isinstance(v, str):
            if v != "auto":
                if not v.endswith('%'):
                    raise ValueError('Height string must be "auto" or a percentage (e.g., "50%")')
                try:
                    percentage = float(v.rstrip('%'))
                    if percentage <= 0:
                        raise ValueError('Height percentage must be greater than 0%')
                    # Auto-correct percentages over 100%
                    if percentage > 100:
                        return "100%"
                except ValueError:
                    raise ValueError('Invalid percentage format')
        return v

# Union type for content items
ContentItem = Union[ParagraphContent, ImageContent]

class Chapter(BaseModel):
    """
    Defines the structure for a generic content chapter with support for images.
    Can use either old 'paragraphs' format or new 'content' format.
    """
    title: str
    type: Optional[str] = "simple"

    # Legacy support
    paragraphs: Optional[List[str]] = None

    # New content structure with images
    content: Optional[List[ContentItem]] = None

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
    @classmethod
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
