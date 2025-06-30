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

class ListItem(BaseModel):
    text: str
    # A sub_items list can contain simple strings (for 2nd level)
    # or it could be expanded to contain ListItem objects again for deeper nesting.
    sub_items: Optional[List[str]] = None

class ListContent(BaseModel):
    type: Literal["list"]
    items: List[ListItem] # The main list contains ListItem objects
    bullet_type: Optional[str] = "bullet"

class TextBoxContent(BaseModel):
    """
    Schema for customizable text boxes with background, borders, and mixed content.
    """
    type: Literal["textbox"]

    # Content can be mixed: text strings or structured items
    content: List[Union[str, Dict[str, Any]]]

    # Box styling
    background_color: Optional[str] = None  # Color name or hex
    border_color: Optional[str] = "black"
    border_width: Optional[float] = 1.0
    border_style: Optional[Literal["solid", "dashed", "dotted"]] = "solid"
    border_radius: Optional[float] = 0  # Rounded corners

    # Padding and margins
    padding_top: Optional[float] = 8
    padding_bottom: Optional[float] = 8
    padding_left: Optional[float] = 8
    padding_right: Optional[float] = 8
    margin_top: Optional[float] = 5
    margin_bottom: Optional[float] = 5

    # Box dimensions
    width: Union[int, str] = "100%"  # Can be pixels or percentage
    height: Optional[float] = None  # Fixed height
    min_height: Optional[float] = None
    max_height: Optional[float] = None

    # Text styling (default for text content)
    font_family: Optional[str] = None  # Override default font
    font_size: Optional[float] = 12
    font_weight: Optional[Literal["Regular", "Bold", "Italic", "BoldItalic"]] = "Regular"
    text_color: Optional[str] = "black"
    text_align: Optional[Literal["left", "center", "right", "justify"]] = "left"
    line_height: Optional[float] = 1.2

    # Positioning
    alignment: Literal["left", "center", "right"] = "left"

    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        if not v:
            raise ValueError('TextBox content cannot be empty')
        return v

class SpeechBubbleContent(BaseModel):
    """
    Schema for speech bubbles with avatar and text.
    """
    type: Literal["speech_bubble"]

    # Speech bubble specific
    bubble_type: Literal["left", "right"] = "left"  # Avatar position
    avatar_src: str  # Image filename
    text: str  # Speech text

    # Bubble styling
    background_color: Optional[str] = "lightblue"
    border_color: Optional[str] = "blue"
    border_width: Optional[float] = 2
    border_radius: Optional[float] = 10

    # Dimensions
    height: Optional[float] = 150
    width: Union[int, str] = "100%"
    avatar_size: Optional[float] = 100

    # Spacing
    padding_top: Optional[float] = 25
    padding_bottom: Optional[float] = 25
    padding_left: Optional[float] = 25
    padding_right: Optional[float] = 25
    margin_top: Optional[float] = 5
    margin_bottom: Optional[float] = 5

    # Text styling
    text_size: Optional[float] = 14
    text_weight: Optional[Literal["Regular", "Bold", "Italic", "BoldItalic"]] = "Regular"
    text_color: Optional[str] = "black"

    # Positioning
    alignment: Literal["left", "center", "right"] = "left"

    @field_validator('avatar_src')
    @classmethod
    def validate_avatar_format(cls, v):
        if not v.lower().endswith(('.jpg', '.jpeg', '.png')):
            raise ValueError('Only JPEG and PNG avatars are supported')
        return v

# Union type for all content items now correctly includes SpeechBubbleContent
ContentItem = Union[ParagraphContent, ImageContent, TableContent, TextBoxContent, SpeechBubbleContent, ListContent]

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
