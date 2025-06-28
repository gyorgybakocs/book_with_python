from pydantic import BaseModel, field_validator, model_validator
from typing import List, Dict, Optional, Union, Literal, Any

# All existing classes remain the same...
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


# --- MODIFIED TableContent CLASS ---
class TableContent(BaseModel):
    """
    Updated schema to handle a list of table blocks, with cross-field validation.
    """
    type: Literal["table"]

    # These types are updated to expect a list of tables.
    # e.g., data is a list of tables, where each table is a list of rows.
    data: List[List[List[str]]]
    style: List[List[List[Any]]] # Using 'Any' for flexibility with style command structure
    block_column_widths: List[List[str]]

    caption: Optional[str] = None
    alignment: Literal["left", "center", "right"] = "center"
    width: Union[int, str] = "100%"

    # This is the new validator you requested.
    @model_validator(mode='after')
    def check_list_lengths_match(self):
        """
        Ensures that the number of table blocks is consistent across
        data, style, and block_column_widths lists.
        """
        len_data = len(self.data)
        len_style = len(self.style)
        len_widths = len(self.block_column_widths)

        if not (len_data == len_style == len_widths):
            raise ValueError(
                f"Inconsistent number of table blocks defined. "
                f"Found {len_data} items in 'data', {len_style} in 'style', "
                f"and {len_widths} in 'block_column_widths'. All must be identical."
            )
        return self
# --- END OF MODIFICATION ---


# Union type for all content items now correctly includes the updated TableContent
ContentItem = Union[ParagraphContent, ImageContent, TableContent]

class Chapter(BaseModel):
    title: str
    type: Optional[str] = "simple"
    content: Optional[List[ContentItem]] = None

    # Removed the old 'paragraphs' field as 'content' is more flexible
    # paragraphs: Optional[List[str]] = None

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
