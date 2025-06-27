from reportlab.platypus import Paragraph

class LayoutService:
    """
    Service responsible ONLY for layout calculations.
    NO DRAWING! Only returns calculation results to builders.
    """
    def __init__(self, content_builder, config: dict):
        self.content = content_builder  # Only for getting dimensions and creating paragraphs
        self.config = config
        self.page_size = self.content.page_size
        self.padding_h = self.content.padding_h
        self.padding_v = self.config.get("common.padding.vertical")

    def calculate_available_space(self, current_pos: float, buffer: float = 15) -> float:
        """Calculates available height on current page."""
        return (self.page_size[1] - current_pos) - self.padding_v - buffer

    def calculate_paragraph_height(self, text: str, **kwargs) -> float:
        """
        Calculates height of a paragraph without drawing it.
        """
        paragraph = self.content.create_paragraph(text, **kwargs)
        width = self.page_size[0] - 2 * self.padding_h
        _w, h = paragraph.wrap(width, 10000)
        return h

    def will_paragraph_fit(self, text: str, current_pos: float, **kwargs) -> bool:
        """Determines if a paragraph will fit on current page."""
        required_height = self.calculate_paragraph_height(text, **kwargs)
        available_height = self.calculate_available_space(current_pos)
        return required_height <= available_height

    def calculate_paragraph_splits(self, text: str, current_pos: float, **kwargs) -> list:
        """
        Calculates how to split a paragraph across pages.
        Returns list of Paragraph objects that fit on pages.
        """
        paragraph = self.content.create_paragraph(text, **kwargs)
        width = self.page_size[0] - 2 * self.padding_h
        available_height = self.calculate_available_space(current_pos)

        parts = paragraph.split(width, available_height)
        return parts if parts else [paragraph]

    def calculate_chapter_layout(self, paragraphs: list, starting_pos: float = None) -> list:
        """
        Calculates the complete layout for a chapter.
        Returns list of layout instructions - NO DRAWING!

        Returns:
            List of dicts with layout instructions like:
            [
                {'type': 'set_position', 'position': 100},
                {'type': 'draw_paragraph', 'paragraph': Paragraph(...), 'spacing_after': 10},
                {'type': 'page_break'},
                {'type': 'draw_header', 'text': 'Chapter Title'},
                ...
            ]
        """
        if starting_pos is None:
            starting_pos = self.padding_v

        instructions = []
        current_pos = starting_pos

        instructions.append({'type': 'set_position', 'position': current_pos})

        for i, par_text in enumerate(paragraphs):
            if not par_text.strip():
                instructions.append({'type': 'add_spacing', 'amount': 10})
                current_pos += 10
                continue

            # Create paragraph for calculations
            paragraph = self.content.create_paragraph(par_text,
                                                      style_name='paragraph_default',
                                                      firstLineIndent=20)

            # Calculate if we need to split
            while paragraph:
                available_height = self.calculate_available_space(current_pos)

                # If no space, need page break
                if available_height <= 0:
                    instructions.append({'type': 'page_break'})
                    current_pos = self.padding_v
                    available_height = self.calculate_available_space(current_pos)

                # Split paragraph
                width = self.page_size[0] - 2 * self.padding_h
                parts = paragraph.split(width, available_height)

                if not parts:
                    # Force page break and try again
                    instructions.append({'type': 'page_break'})
                    current_pos = self.padding_v
                    available_height = self.calculate_available_space(current_pos)
                    parts = paragraph.split(width, available_height)

                    if not parts:
                        break  # Give up

                # Add instruction to draw the part that fits
                part_height = parts[0].wrap(width, available_height)[1]
                instructions.append({
                    'type': 'draw_paragraph',
                    'paragraph': parts[0],
                    'spacing_after': 10
                })
                current_pos += part_height + 10

                # Check if there's continuation
                if len(parts) > 1:
                    paragraph = parts[1]
                    # Will need page break for continuation
                else:
                    paragraph = None

        return instructions

    def calculate_optimal_positions(self) -> dict:
        """Returns optimal starting positions for different content types."""
        return {
            'title_page': self.config.get("defaults.starting_pos", 300.0),
            'chapter_title': self.config.get("defaults.starting_pos", 300.0),
            'chapter_content': self.padding_v,
            'simple_content': self.padding_v
        }

    def should_start_new_page(self, content_height: float, current_pos: float) -> bool:
        """Determines if content should start on a new page."""
        available_space = self.calculate_available_space(current_pos)
        return content_height > available_space

    def calculate_title_layout(self, title: str, subtitle: str, starting_pos: float) -> list:
        """
        Calculates layout for title page.
        Returns layout instructions.
        """
        instructions = []
        instructions.append({'type': 'set_position', 'position': starting_pos})

        # Calculate title
        title_paragraph = self.content.create_title_paragraph(f'<b>{title}</b>', alignment=0)
        instructions.append({'type': 'draw_paragraph', 'paragraph': title_paragraph, 'spacing_after': 0})

        # Add separator
        instructions.append({'type': 'draw_separator'})

        # Calculate subtitle
        subtitle_paragraph = self.content.create_subtitle_paragraph(f'<b>{subtitle}</b>')
        instructions.append({'type': 'add_spacing', 'amount': 6})
        instructions.append({'type': 'draw_paragraph', 'paragraph': subtitle_paragraph, 'spacing_after': 0})

        return instructions
