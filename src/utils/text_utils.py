import re


def strip_html_tags(text):
    """Remove HTML tags but preserve original text"""
    return re.sub(r'<[^>]+>', '', text)


def split_html_text(original_text, first_part):
    """Split HTML text at the correct position based on clean text split"""
    # Get split position from clean text
    first_text = ' '.join(first_part.frags[0].words)
    split_pos_clean = len(first_text)

    # Count HTML tags and adjust split position
    html_tag_lengths = sum(len(tag) for tag in re.findall(r'<[^>]+>', original_text))
    for tag_match in re.finditer(r'<[^>]+>', original_text):
        if tag_match.start() > split_pos_clean + html_tag_lengths:
            html_tag_lengths -= len(tag_match.group())

    split_pos = split_pos_clean + html_tag_lengths

    return original_text[:split_pos], original_text[split_pos:]


def fix_html_tags(first_html, second_html):
    """Fix unclosed HTML tags at split point"""
    open_tags = re.findall(r'<([^/][^>]*)>', first_html)
    close_tags = re.findall(r'</([^>]*)>', first_html)

    for tag in reversed(open_tags):
        tag_name = tag.split()[0]
        if tag_name not in close_tags:
            first_html += f'</{tag_name}>'
            second_html = f'<{tag}>' + second_html

    return first_html, second_html
