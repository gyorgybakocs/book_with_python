import os

from reportlab.lib.pagesizes import letter, portrait
from reportlab.pdfgen import canvas as cnv
from reportlab.platypus.paragraph import Paragraph


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


def make_paragraph(canvas, text, style, pos, pagesize, padding_h, increase_pos=True, extra_spacing=0, extra_width=0):
    """
    Creates a paragraph on the canvas at the specified position.

    Args:
        canvas: The PDF canvas
        text: Text content
        style: Paragraph style
        pos: Vertical position
        pagesize: Page size tuple
        padding_h: Horizontal padding
        increase_pos: If True, increases position by paragraph height
        extra_spacing: Additional vertical spacing
        extra_width: Additional horizontal spacing
    Returns:
        float: New vertical position after paragraph
    """
    paragraph = Paragraph(text, style)
    width, height = paragraph.wrapOn(canvas, pagesize[0] - 2 * padding_h - extra_width, 0)

    if increase_pos:
        pos += height
    pos += extra_spacing

    paragraph.drawOn(canvas, padding_h + extra_width, pagesize[1] - pos)
    return pos


def make_header(canvas, txt, style, pos, pagesize, padding_h, increase_pos=True, additional_pos=0, line=True):
    if line:
        canvas.line(padding_h, pagesize[1] - pos, pagesize[0] - padding_h,
                    pagesize[1] - pos)

    pos = make_paragraph(canvas, txt, style, pos, pagesize, padding_h, increase_pos, additional_pos)

    return pos


def make_footer(canvas, txt, style, padding_v, pagesize, padding_h, num):
    canvas.line(padding_h, padding_v, pagesize[0] - padding_h, padding_v)
    txt = Paragraph('{} | {}'.format(num, txt), style)
    txt.wrapOn(canvas, pagesize[0] - 2 * padding_h, 25)
    txt.drawOn(canvas, padding_h, padding_v - 25)
