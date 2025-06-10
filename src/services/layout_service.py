from reportlab.platypus import Paragraph
from src.managers.style_manager import StyleManager
from src.builders.content_builder import ContentBuilder

class LayoutService:
    def __init__(self, content_builder: ContentBuilder, style_manager: StyleManager, config: dict):
        self.content = content_builder
        self.style_manager = style_manager
        self.config = config
        self.page_size = self.content.page_size
        self.padding_h = self.content.padding_h
        self.padding_v = self.config.get("common.padding.vertical")
        self.current_pos = 0.0
        self.current_page_number = 1

    def start_from(self, pos: float):
        self.current_pos = float(pos)
        return self

    def add_spacing(self, spacing: float):
        self.current_pos += float(spacing)
        return self

    def _add_paragraph_internal(self, text: str, style: object):
        if hasattr(style, 'spaceBefore'):
            self.current_pos += style.spaceBefore

        p = Paragraph(text, style)
        _w, h = p.wrapOn(self.content.canvas, self.page_size[0] - (self.padding_h * 2), 10000)

        self.content.draw_paragraph(p, self.current_pos)
        self.current_pos += h

        if hasattr(style, 'spaceAfter'):
            self.current_pos += style.spaceAfter

    def add_paragraph(self, text: str, **kwargs):
        style_name = kwargs.pop('style_name', 'paragraph_default')
        style = self.style_manager.prepare_style(style_name, **kwargs)
        self._add_paragraph_internal(text, style)
        return self

    def add_title(self, text: str, **kwargs):
        kwargs['style_name'] = 'title_main'
        self.add_paragraph(text, **kwargs)
        return self

    def add_subtitle(self, text: str, **kwargs):
        kwargs['style_name'] = 'title_sub'
        self.add_paragraph(text, **kwargs)
        return self

    def add_separator_line(self):
        self.add_spacing(12)
        self.content.draw_line(self.current_pos)
        self.add_spacing(12)
        return self

    def flow_paragraphs(self, paragraphs: list, has_header: bool = False, has_footer: bool = False, chapter_title: str = ""):
        page_height = self.page_size[1]

        for par_text in paragraphs:
            if not par_text.strip():
                self.add_spacing(10)
                continue

            style = self.style_manager.prepare_style('paragraph_default', firstLineIndent=20)
            par_obj = Paragraph(par_text, style)

            self.add_spacing(10)

            while par_obj:
                avail_width = self.page_size[0] - 2 * self.padding_h
                avail_height = (page_height - self.current_pos) - self.padding_v

                if avail_height < style.fontSize + 5: # Buffer for safety
                    if has_footer: self.content.draw_footer(self.current_page_number, chapter_title)
                    self.new_page()
                    if has_header: self.content.draw_header(chapter_title)
                    avail_height = (page_height - self.current_pos) - self.padding_v

                parts = par_obj.split(avail_width, avail_height)
                if not parts: break

                _w, h = parts[0].wrapOn(self.content.canvas, avail_width, avail_height)
                self.content.draw_paragraph(parts[0], self.current_pos)
                self.current_pos += h

                if len(parts) > 1:
                    par_obj = parts[1]
                    if has_footer: self.content.draw_footer(self.current_page_number, chapter_title)
                    self.new_page()
                    if has_header: self.content.draw_header(chapter_title)
                else:
                    par_obj = None

    def new_page(self):
        self.content.new_page()
        self.start_from(self.padding_v)
        self.current_page_number += 1
