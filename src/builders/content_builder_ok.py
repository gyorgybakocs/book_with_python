import copy

from src.managers.style_manager import modify_paragraph_style
from src.utils.page_utils import make_paragraph, make_header, make_footer
from reportlab.platypus.paragraph import Paragraph
from reportlab.platypus import Frame


class ContentBuilder:
    def __init__(self, canvas, page_size, style_manager, padding_h, padding_v):
        self.canvas = canvas
        self.page_size = page_size
        self.style_manager = style_manager
        self.padding_h = padding_h
        self.padding_v = padding_v
        self.current_pos = 0
        self.page_num = 0
        self.available_height = self.page_size[1] - 2 * self.padding_v

    def set_available_height(self, height=None):
        self.available_height = height if height is not None else self.page_size[1] - 2 * self.padding_v

    def start_from(self, pos):
        """Set starting position"""
        self.current_pos = pos
        return self

    def add_spacing(self, spacing):
        """Add vertical spacing"""
        self.current_pos += spacing
        return self

    def add_title(self, text, alignment=1, font_size=None, leading=None, extra_spacing=0):
        """Add a title with specific style"""
        title_style = self.style_manager.get_style('title_main')
        if any([font_size, alignment, leading]):
            style_mods = {}
            if font_size:
                style_mods['fontSize'] = font_size
                style_mods['leading'] = leading or font_size
            if leading == 'default':
                style_mods['leading'] = title_style.leading + 6
            if alignment is not None:
                style_mods['alignment'] = alignment
            title_style = modify_paragraph_style(title_style, **style_mods)

        self.current_pos = make_paragraph(
            self.canvas,
            text,
            title_style,
            self.current_pos,
            self.page_size,
            self.padding_h,
            True,
            extra_spacing
        )
        return self

    def add_subtitle(self, text, alignment=2, extra_spacing=0):
        """Add a subtitle"""
        subtitle_style = self.style_manager.get_style('title_sub')
        if alignment is not None:
            subtitle_style = modify_paragraph_style(subtitle_style, alignment=alignment)

        self.current_pos = make_paragraph(
            self.canvas,
            text,
            subtitle_style,
            self.current_pos + 6,
            self.page_size,
            self.padding_h,
            True,
            extra_spacing
        )
        return self

    def add_separator_line(self):
        """Add a horizontal line"""
        self.canvas.line(
            self.padding_h,
            self.page_size[1] - self.current_pos,
            self.page_size[0] - self.padding_h,
            self.page_size[1] - self.current_pos
        )
        return self

    def add_break(self, chapter_title, header_pos, has_header=True, has_footer=True, spacing=6):
        if has_footer:
            self.add_footer(chapter_title)
        self.new_page()
        if has_header:
            self.current_pos = header_pos
            self.add_header(f'<span>{chapter_title}</span>').add_spacing(spacing)

    def add_paragraph(self, text, style_name='paragraph_default',
                      first_line_indent=0, extra_spacing=0, extra_width=0,
                      border_padding=None, header_pos=0, chapter_title=None, has_header=False, has_footer=False):
        """Add a paragraph with specific style"""
        is_empty = text == ""

        original_style = self.style_manager.get_style(style_name)
        style_mods = {}
        if first_line_indent:
            style_mods['firstLineIndent'] = first_line_indent
        if border_padding is not None:
            style_mods['borderPadding'] = border_padding
        style = modify_paragraph_style(original_style, **style_mods) if style_mods else original_style

        # Create paragraph and check height
        p = Paragraph(text, style)
        w, h = p.wrapOn(self.canvas, self.page_size[0] - 2 * self.padding_h - extra_width, 20)

        # Check if fits on current page
        if self.current_pos + h + extra_spacing > self.page_size[1] - self.padding_v:
            result = p.split(self.page_size[0] - 2 * self.padding_h, self.available_height)

            if result and len(result) == 2:
                first_part, second_part = result

                first_text = ""
                for frag in first_part.frags:
                    if hasattr(frag, 'text'):
                        first_text += frag.text
                    elif hasattr(frag, 'words'):
                        first_text += " ".join(frag.words)

                self.current_pos = make_paragraph(
                    self.canvas,
                    first_text,
                    style,
                    self.current_pos,
                    self.page_size,
                    self.padding_h,
                    True,
                    extra_spacing,
                    extra_width
                )
                text = ""
                for frag in second_part.frags:
                    if hasattr(frag, 'text'):
                        text += frag.text
                    elif hasattr(frag, 'words'):
                        text += " ".join(frag.words)
                style = original_style

            self.add_break(chapter_title, header_pos, has_header, has_footer, 6)
            if not is_empty:
                self.current_pos = make_paragraph(
                    self.canvas,
                    text,
                    style,
                    self.current_pos,
                    self.page_size,
                    self.padding_h,
                    True,
                    extra_spacing,
                    extra_width
                )

            # if is_empty:
            #     self.add_break(chapter_title, header_pos, has_header, has_footer, 6)
            # else:
            #     # frame = Frame(
            #     #     self.padding_h,
            #     #     self.page_size[1] - self.current_pos - (self.page_size[1] - self.current_pos - self.padding_v),
            #     #     self.page_size[0] - 2 * self.padding_h,
            #     #     self.page_size[1] - self.current_pos - self.padding_v
            #     # )
            #     # # Try to split the paragraph
            #     # result = frame.split(p, self.page_size[1])
            #     if result and len(result) == 2:
            #         first_part, second_part = result
            #         self.current_pos = make_paragraph(
            #             self.canvas,
            #             f'<p>{" ".join(first_part.frags[0].words)}</p>',
            #             style,
            #             self.current_pos,
            #             self.page_size,
            #             self.padding_h,
            #             True,
            #             extra_spacing,
            #             extra_width
            #         )
            #         self.add_break(chapter_title, header_pos, has_header, has_footer, 6)
            #         self.current_pos = make_paragraph(
            #             self.canvas,
            #             f'<p>{" ".join(second_part.frags[0].words)}</p>',
            #             original_style,
            #             self.current_pos,
            #             self.page_size,
            #             self.padding_h,
            #             True,
            #             extra_spacing,
            #             extra_width
            #         )
            #
            #     else:
            #         self.add_break(chapter_title, header_pos, has_header, has_footer, 6)
            #         self.current_pos = make_paragraph(
            #             self.canvas,
            #             text,
            #             style,
            #             self.current_pos,
            #             self.page_size,
            #             self.padding_h,
            #             True,
            #             extra_spacing,
            #             extra_width
            #         )

        else:
            self.current_pos = make_paragraph(
                self.canvas,
                text,
                style,
                self.current_pos,
                self.page_size,
                self.padding_h,
                True,
                extra_spacing,
                extra_width
            )

        self.available_height = self.page_size[1] - self.current_pos - self.padding_v

        return self

    def add_header(self, text, extra_spacing=-6):
        """Add a right-aligned header with subtitle style"""
        title_style = self.style_manager.get_style('title_sub')
        header_style = modify_paragraph_style(title_style, alignment=2)

        self.current_pos = make_header(
            self.canvas,
            text,
            header_style,
            self.current_pos,
            self.page_size,
            self.padding_h,
            False,
            extra_spacing,
            True
        )

        return self

    def add_footer(self, text, page_number=1):
        """Add a footer to the current page"""
        paragraph_style = self.style_manager.get_style('paragraph_default')
        make_footer(
            self.canvas,
            text,
            paragraph_style,
            self.padding_v,
            self.page_size,
            self.padding_h,
            page_number
        )

        return self

    def add_chapter_paragraphs(self, paragraphs, header_pos, chapter_title="", has_header=False, has_footer=False, first_line_indent=20, extra_spacing=10):
        """Add multiple paragraphs with indentation"""

        for par in paragraphs:
            self.add_paragraph(
                par,
                header_pos=header_pos,
                chapter_title=chapter_title,
                has_header=has_header,
                has_footer=has_footer,
                first_line_indent=first_line_indent,
                extra_spacing=extra_spacing
            )

        return self

    def new_page(self):
        """Start a new page"""
        self.canvas.showPage()
        self.page_num += 1
        self.current_pos = 0

        return self
