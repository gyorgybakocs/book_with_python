import os
from reportlab.lib.pagesizes import letter, portrait
from reportlab.pdfgen import canvas as cnv

def make_page(title, subtitle, path, paper_book, black_and_white, font_color, short=False):
    """
    Creates and configures a PDF canvas object with a dynamically generated filename.
    This is the only function that should remain in this utility file.
    """
    book_name = '{}_{}'.format(title.replace(' ', '_'), subtitle.replace(' ', '_'))
    book_file = f'{path}/{book_name}'

    if paper_book:
        book_file += '_paperbook'
    if black_and_white:
        book_file += '_blackandwhite'
    if short:
        book_file += '_short'
    book_file += '.pdf'

    os.makedirs(os.path.dirname(book_file), exist_ok=True)

    canvas_obj = cnv.Canvas(book_file, pagesize=letter)
    canvas_obj.setPageSize(portrait(letter))
    canvas_obj.setFillColor(font_color)

    return canvas_obj, portrait(letter)
