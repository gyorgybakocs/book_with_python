from pydantic import BaseModel, field_validator
from typing import List, Dict, Optional, Union, Literal

class TableCell(BaseModel):
    """Enhanced table cell with merging support."""
    text: str
    colspan: Optional[int] = 1  # Number of columns to span
    rowspan: Optional[int] = 1  # Number of rows to span
    style_class: Optional[str] = None  # Reference to style in StyleManager

    @field_validator('colspan', 'rowspan')
    @classmethod
    def validate_span(cls, v):
        if v is not None and v < 1:
            raise ValueError('Span values must be at least 1')
        return v

class TableRow(BaseModel):
    """Table row with enhanced cells."""
    cells: List[Union[str, TableCell]]  # Allow simple strings or complex cells
    style_class: Optional[str] = None  # Reference to row style

class AdvancedTableContent(BaseModel):
    """Advanced table content with merged cells and style references."""
    type: Literal["advanced_table"]
    headers: List[Union[str, TableCell]]  # Headers can also be complex
    rows: List[TableRow]  # Enhanced rows
    caption: Optional[str] = None
    alignment: Literal["left", "center", "right"] = "center"
    style_preset: Optional[str] = "default"  # Reference to predefined table style
    width: Union[int, str] = "100%"
    column_widths: Optional[List[Union[int, str]]] = None
    border_style: Optional[Literal["none", "thin", "thick", "double"]] = "thin"

class SimpleTableContent(BaseModel):
    """Simple table (backward compatibility)."""
    type: Literal["table"]
    headers: List[str]
    rows: List[List[str]]
    caption: Optional[str] = None
    alignment: Literal["left", "center", "right"] = "center"
    style_preset: Optional[str] = "default"  # Reference to table style
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
ContentItem = Union[ParagraphContent, ImageContent, SimpleTableContent, AdvancedTableContent]

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
