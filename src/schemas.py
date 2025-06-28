from pydantic import BaseModel, field_validator
from typing import List, Dict, Optional, Union, Literal


class TableContent(BaseModel):
    """Simple table (backward compatibility)."""
    type: Literal["table"]
    data: List[List[str]]
    style: List[List[Union[str, List[int], str]]]
    caption: Optional[str] = None
    alignment: Literal["left", "center", "right"] = "center"
    width: Union[int, str] = "100%"
    column_widths: Optional[List[Union[int, str]]] = None

# Keep all existing classes...
class Title(BaseModel):
    title: str
    subtitle: str

class Copyright(BaseModel):
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
    type: Literal["paragraph"]
    text: str

class ImageContent(BaseModel):
    type: Literal["image"]
    src: str
    alignment: Literal["left", "center", "right"] = "center"
    width: Union[int, str] = 300
    height: Union[int, Literal["auto"], str] = "auto"
    caption: Optional[str] = None

    @field_validator('src')
    @classmethod
    def validate_image_format(cls, v):
        if not v.lower().endswith(('.jpg', '.jpeg', '.png')):
            raise ValueError('Only JPEG and PNG images are supported')
        return v

# Union type for all content items
ContentItem = Union[ParagraphContent, ImageContent, TableContent]

class Chapter(BaseModel):
    title: str
    type: Optional[str] = "simple"
    paragraphs: Optional[List[str]] = None
    content: Optional[List[ContentItem]] = None

class Book(BaseModel):
    title: Title
    copyright: Copyright
    chapters: Dict[str, Chapter]
    dedicate: Optional[Chapter] = None
    preface: Optional[Chapter] = None

    @field_validator('chapters')
    @classmethod
    def chapters_must_not_be_empty(cls, v):
        if not v:
            raise ValueError('chapters dictionary must not be empty')
        return v

class BookData(BaseModel):
    book_hu: Book
    book_en: Book
