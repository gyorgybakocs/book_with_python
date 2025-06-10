valid_json_data = {
    "book_hu": {
        "title": {"title": "Cím", "subtitle": "Alcím"},
        "copyright": {
            "copyright_text": "Szöveg", "author_text": "Szerző", "author": "Név",
            "design_text": "Tervező", "design": "Név", "publish_text": "Kiadó",
            "publish": "Név", "ISBN_pdf": "123", "ISBN_epub": "456",
            "ISBN_print": "789", "printing_text": "Nyomtatás",
            "printing": ["Első"], "email_text": "Email", "email": "email@example.com"
        },
        "dedicate": {"title": "Ajánlás", "paragraphs": ["Bekezdés"], "from": "Szerző"},
        "preface": {"title": "Előszó", "type": "simple", "paragraphs": ["Bekezdés"]},
        "chapters": {
            "ch1": {"title": "Fejezet 1", "type": "simple", "paragraphs": ["Bekezdés"]}
        }
    },
    "book_en": {
        "title": {"title": "Title", "subtitle": "Subtitle"},
        "copyright": {
            "copyright_text": "Text", "author_text": "Author", "author": "Name",
            "design_text": "Design", "design": "Name", "publish_text": "Publisher",
            "publish": "Name", "ISBN_pdf": "123", "ISBN_epub": "456",
            "ISBN_print": "789", "printing_text": "Printing",
            "printing": ["First"], "email_text": "Email", "email": "email@example.com"
        },
        "dedicate": {"title": "Dedication", "paragraphs": ["Paragraph"], "from": "Author"},
        "preface": {"title": "Preface", "type": "simple", "paragraphs": ["Paragraph"]},
        "chapters": {
            "ch1": {"title": "Chapter 1", "type": "simple", "paragraphs": ["Paragraph"]}
        }
    }
}