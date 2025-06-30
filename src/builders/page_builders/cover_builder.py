from .base_page_builder import BasePageBuilder
from src.logger import logger
from reportlab.lib.utils import ImageReader
import os

class CoverBuilder(BasePageBuilder):
    """Builds the cover page by drawing a language-specific cover image."""

    def build(self, **options):
        """
        Draws the cover image for the specified language onto a new page.
        The 'source_path' parameter is removed as it is not used.
        """
        start_page = self.content.page_num
        try:
            # Determine the correct image file based on the book's language
            image_filename = f"cover.{self.language}.png"
            images_path = os.path.join(self.config.get("paths.resources"), "images")
            image_full_path = os.path.join(images_path, image_filename)

            if not os.path.exists(image_full_path):
                logger.error(f"Cover image not found at '{image_full_path}'. Creating a blank page instead.")
                self.content.add_blank_page()
            else:
                logger.info(f"Adding cover page from image: {image_full_path}")

                # Get page dimensions
                page_width, page_height = self.content.page_size

                # Draw the image to fill the entire page
                self.content.canvas.drawImage(
                    ImageReader(image_full_path),
                    x=0,
                    y=0,
                    width=page_width,
                    height=page_height,
                    preserveAspectRatio=True,
                    anchor='c'
                )

                self.content.new_page()

        except Exception as e:
            logger.error(f"Failed to build cover page: {e}", exc_info=True)
            # Fallback to a blank page on error
            if self.content.page_num == start_page:
                self.content.add_blank_page()

        finally:
            end_page = self.content.page_num - 1
            self.register_section('cover', 'Cover', start_page, end_page, 'cover')
