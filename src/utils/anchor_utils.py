"""
Utility functions for generating consistent anchor names across the application.
"""
import re

def generate_anchor_name(title: str) -> str:
    """
    Generate a clean anchor name from a title.

    Args:
        title: The title to convert to anchor

    Returns:
        Clean anchor name suitable for HTML anchors

    Example:
        "Túl a szabályokon: Az angol igeidők" -> "tul_a_szabalyokon_az_angol_igeidok"
    """
    if not title:
        return 'chapter'

    anchor = title.lower()

    # Replace Hungarian characters
    hungarian_chars = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'ű': 'u', 'ö': 'o', 'ü': 'u'
    }
    for hun_char, eng_char in hungarian_chars.items():
        anchor = anchor.replace(hun_char, eng_char)

    # Replace all non-alphanumeric characters with underscore
    anchor = re.sub(r'[^a-z0-9]', '_', anchor)
    # Replace multiple underscores with single underscore
    anchor = re.sub(r'_+', '_', anchor)
    # Remove leading/trailing underscores
    anchor = anchor.strip('_')

    # Ensure we have something
    if not anchor:
        anchor = 'chapter'

    return anchor
