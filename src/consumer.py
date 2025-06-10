import argparse
import logging

from src.builders.epub_builder import EpubBuilder
from src.builders.pdf_builder import PdfBuilder
from src.services.config_service import ConfigService
from src.services.logger_service import LoggerService


def main():
    """
    Main entry point for the book generation process.
    Parses command-line arguments to determine the output format and
    other settings, then initializes services and triggers the appropriate builder.
    """
    parser = argparse.ArgumentParser(description='Process EPUB or PDF pages.')

    parser.add_argument('--format',
                        type=str,
                        required=True,
                        choices=['pdf', 'epub'],
                        help='Specify output format: pdf or epub'
                        )
    parser.add_argument('--data',
                        type=str,
                        required=True,
                        help='Specify the source json file for book content'
                        )
    parser.add_argument('--config',
                        type=str,
                        required=True,
                        help='Specify the unified YAML config file'
                        )

    # PDF-specific arguments
    parser.add_argument('--pb',
                        type=str,
                        choices=['0', '1'],
                        help='Paperbook version (PDF only)'
                        )
    parser.add_argument('--bw',
                        type=str,
                        choices=['0', '1'],
                        help='Black and white version (PDF only)'
                        )
    parser.add_argument('--s',
                        type=str,
                        choices=['0', '1'],
                        help='Short version (PDF only)'
                        )
    parser.add_argument('--l',
                        type=str,
                        choices=['en', 'hu'],
                        help='Language (PDF only)'
                        )

    # EPUB-specific arguments
    parser.add_argument('--et',
                        type=str,
                        choices=['kindle', 'epub', 'web'],
                        help='EPUB type (EPUB only)'
                        )

    args = parser.parse_args()

    try:
        ConfigService.initialize(config_file=args.config)
        logging.info("Config loaded successfully")

        LoggerService.get_instance().initialize_from_config(ConfigService.get_instance())
        logging.info("Logger initialized from config")

    except Exception as e:
        logging.error(f"Startup failed: {e}")
        return

    json_file = args.data
    builder = None

    if args.format == 'pdf':
        if not all([args.pb, args.bw, args.s, args.l]):
            parser.error("PDF format requires --pb, --bw, --s, and --l arguments.")

        language = args.l
        short = args.s == '1'
        paper_book = args.pb == '1' and not short
        black_and_white = args.bw == '1' and not short

        builder = PdfBuilder(
            json_file=json_file,
            paper_book=paper_book,
            black_and_white=black_and_white,
            short=short,
            language=language
        )
    elif args.format == 'epub':
        if not args.et:
            parser.error("EPUB format requires --et argument.")

        builder = EpubBuilder(
            json_file=json_file,
            epub_type=args.et
        )

    if builder and builder.valid:
        builder.run()


if __name__ == "__main__": # pragma: no cover
    main()
