from .base_page_builder import BasePageBuilder
from src.logger import logger

class ChapterBuilder(BasePageBuilder):
    """
    Builds a chapter, handling different layouts for simple vs. main chapters.
    This class is now responsible for its own page-breaking logic.
    """
    def build(self, source_path: str = None, **options):
        if not source_path:
            logger.error("ChapterBuilder requires a 'source_path'.")
            return

        chapter_data = self.data_manager.get_data(self.language, source_path)
        if not chapter_data:
            logger.warning(f"Could not find data for source '{source_path}'. Skipping.")
            return

        is_main_chapter = options.get('is_main_chapter', False)

        if is_main_chapter:
            self._build_as_main_chapter(chapter_data)
        else:
            self._build_as_simple_chapter(chapter_data)

    def _build_as_simple_chapter(self, chapter_data: dict):
        """Builds a simple, single-page chapter (e.g., for dedicate/preface)."""
        starting_pos = self.config.get("common.padding.vertical")
        self.content.start_from(starting_pos)

        self.content.add_paragraph(f'{chapter_data.get("title", "")}', style_name='title_sub')

        self._draw_paragraphs_with_page_breaks(chapter_data, has_header=False, has_footer=False, continue_from_current_pos=True)
        self.content.new_page()

    def _build_as_main_chapter(self, chapter_data: dict):
        """Builds a standard main chapter with a title page and headers/footers."""
        starting_pos = self.config.get("defaults.starting_pos")

        # Build title page for the chapter
        (self.content
         .start_from(starting_pos)
         .add_title(chapter_data.get('title', ''), alignment=1, font_size=64, leading=64)
         .new_page())

        # Build content pages
        self._draw_paragraphs_with_page_breaks(chapter_data, has_header=True, has_footer=True)
        self.content.new_page()

    def _draw_paragraphs_with_page_breaks(self, chapter_data: dict, has_header: bool, has_footer: bool, continue_from_current_pos: bool = False):
        """Kirajzolja a fejezet összes bekezdését, intelligens, soron belüli oldaltöréssel."""

        padding_v = self.config.get("common.padding.vertical")
        page_height = self.content.page_size[1]

        if not continue_from_current_pos:
            self.content.start_from(padding_v)

        paragraphs = chapter_data.get('paragraphs', [])
        for i, par_text in enumerate(paragraphs):
            if not par_text.strip():
                self.content.add_spacing(10)
                continue

            par_obj = self.content.create_paragraph(par_text, firstLineIndent=20)

            # Ciklus, ami addig fut, amíg a teljes bekezdés kiírásra nem kerül
            while par_obj:
                # Elérhető hely kiszámítása az aktuális oldalon
                avail_width = self.content.page_size[0] - 2 * self.content.padding_h
                avail_height = (page_height - self.content.current_pos) - padding_v - 15 # Kis buffer

                # Ha már egy sor sem fér el, új oldalt kezdünk
                if avail_height <= 0:
                    if has_footer: self.content.add_footer(chapter_data.get("title", ""))
                    self.content.new_page()
                    self.content.start_from(padding_v)
                    if has_header: self.content.add_header(f'<span>{chapter_data.get("title", "")}</span>')
                    avail_height = (page_height - self.content.current_pos) - padding_v - 15

                # A bekezdés felosztása: ami elfér, és ami a maradék.
                parts = par_obj.split(avail_width, avail_height)

                if not parts:
                    break # Üres vagy tördelhetetlen bekezdés, kilépünk

                # Az első rész (ami elfér) kirajzolása
                self.content.draw_paragraph_object(parts[0])
                self.content.add_spacing(10) # Hely a bekezdések között

                # Megnézzük, maradt-e folytatás
                if len(parts) > 1:
                    par_obj = parts[1] # A maradék lesz a következő körben a kiírandó objektum

                    # Új oldalt kezdünk a folytatásnak
                    if has_footer: self.content.add_footer(chapter_data.get("title", ""))
                    self.content.new_page()
                    self.content.start_from(padding_v)
                    if has_header: self.content.add_header(f'<span>{chapter_data.get("title", "")}</span>')
                else:
                    par_obj = None # Kész, a teljes bekezdés elfért, kilépünk a ciklusból

        if has_footer and paragraphs:
            self.content.add_footer(chapter_data.get("title", ""))