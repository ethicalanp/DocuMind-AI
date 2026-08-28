import re


def clean_text(text: str) -> str:
    """
    Clean extracted document text.
    """

    # Replace multiple spaces/tabs with one space
    text = re.sub(r"[ \t]+", " ", text)

    # Replace excessive newlines
    text = re.sub(r"\n\s*\n+", "\n\n", text)

    # Remove spaces at beginning/end
    text = text.strip()

    return text


def chunk_text(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200
):
    """
    Split text into overlapping chunks.
    """

    text = clean_text(text)

    if not text:
        return []

    chunks = []

    start = 0

    while start < len(text):

        end = start + chunk_size

        chunk = text[start:end]

        chunks.append(chunk)

        start = end - chunk_overlap

    return chunks