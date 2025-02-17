import argparse

# Setup argument parser
from src.builders.epub_builder import EpubBuilder
from src.builders.pdf_builder import PdfBuilder

parser = argparse.ArgumentParser(description='Process EPUB or PDF pages.')

parser.add_argument('--format',
                    type=str,
                    required=True,
                    choices=['pdf', 'epub'],
                    help='Specify output format: pdf or epub'
                    )
parser.add_argument('--json',
                    type=str,
                    required=True,
                    help='Specify the source json file'
                    )

# PDF Arguments
parser.add_argument('--pb',
                    type=str,
                    choices=['0', '1'],
                    help='Paperbook (only for PDF)'
                    )
parser.add_argument('--bw',
                    type=str,
                    choices=['0', '1'],
                    help='Black and white (only for PDF)'
                    )
parser.add_argument('--s',
                    type=str,
                    choices=['0', '1'],
                    help='Short version (only for PDF)'
                    )
parser.add_argument('--l',
                    type=str,
                    choices=['en', 'hu'],
                    help='Language (only for PDF)'
                    )

# EPUB Arguments
parser.add_argument('--et',
                    type=str,
                    choices=['kindle', 'epub', 'web'],
                    help='EPUB type (only for EPUB)'
                    )

args = parser.parse_args()
json_file = args.json
# Determine processing mode
if args.format == 'pdf':
    if not all([args.pb, args.bw, args.s, args.l]):
        parser.error("PDF format requires --pb, --bw, --s, and --l arguments.")

    language = args.l == 'en'
    short = args.s == '1'
    paper_book = args.pb == '1' and not short
    black_and_white = args.bw == '1' and not short
    builder = PdfBuilder(json_file=json_file, paper_book=paper_book, black_and_white=black_and_white, short=short, language=language)
elif args.format == 'epub':
    if not args.et:
        parser.error("EPUB format requires --et argument.")

    builder = EpubBuilder(json_file=json_file, epub_type=args.et)

if builder.valid:
    builder.run()
