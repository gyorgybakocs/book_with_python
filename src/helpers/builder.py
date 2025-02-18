from copy import deepcopy
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import os
from reportlab.pdfgen import canvas as cnv
from reportlab.lib.pagesizes import letter, portrait


def make_page(title, subtitle, path, paper_book, black_and_white, font_color, short=False):
    """
    Creates a PDF canvas with a dynamically generated filename based on book properties.
    Ensures the target directory exists before saving.
    """
    book = '{}_{}'.format(title.replace(' ', '_'), subtitle.replace(' ', '_'))
    book_file = '{}/{}'.format(path, book)

    if paper_book:
        book_file = '{}_paperbook'.format(book_file)
    if black_and_white:
        book_file = '{}_blackandwhite'.format(book_file)
    if short:
        book_file = '{}_short'.format(book_file)

    book_file = '{}.pdf'.format(book_file)

    # 🔥 Ensure the directory exists
    os.makedirs(os.path.dirname(book_file), exist_ok=True)

    # Create the canvas
    canvas = cnv.Canvas(book_file, pagesize=letter)
    canvas.translate(0, 0)
    canvas.setPageSize(portrait(letter))
    pagesize = portrait(letter)
    canvas.setFillColor(font_color)

    return canvas, pagesize


def register_fonts(font, font_types, path):
    """
    Registers a font and its variations dynamically.

    :param font: The base font name (e.g., 'Arial')
    :param font_types: Dictionary of font variations (e.g., {'normal': 'Regular', 'bold': 'Bold'})
    :param path: The directory where the font files are located
    :return: True if ALL fonts were registered successfully, False otherwise
    """

    font_variants = {}
    required_fonts = [f"{path}/{font}-{font_type}.ttf" for font_type in font_types.values()]
    missing_fonts = [f for f in required_fonts if not os.path.exists(f)]

    if missing_fonts:
        print(f"Missing fonts: {', '.join(missing_fonts)}")  # Debug log
        return False  # 🔥 Fail if ANY font is missing

    for font_type_key, font_type in font_types.items():
        font_file = f"{path}/{font}-{font_type}.ttf"
        font_name = f"{font}-{font_type}"
        pdfmetrics.registerFont(TTFont(font_name, font_file))
        font_variants[font_type_key] = font_name

    pdfmetrics.registerFontFamily(font, **font_variants)
    return True  # 🔥 Success ONLY if all fonts were found and registered


def modify_paragraph_style(style, **kwargs):
    """
    Creates a modified copy of an existing paragraph style with new attributes.

    :param style: The original ParagraphStyle object to copy.
    :param kwargs: The attributes to override (e.g., fontSize=16, alignment=1).
    :return: A new ParagraphStyle object with the modified attributes.
    """

    # 🔥 Make a deep copy of the original style
    new_style = deepcopy(style)

    # 🔥 Apply modifications from kwargs
    for key, value in kwargs.items():
        if hasattr(new_style, key):
            setattr(new_style, key, value)
        else:
            print(f"Warning: '{key}' is not a valid attribute for ParagraphStyle.")

    return new_style
