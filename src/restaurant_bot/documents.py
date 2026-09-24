import re
from io import BytesIO

from pypdf import PdfReader

from restaurant_bot.config import CHUNK_TARGET_WORDS

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
_PARAGRAPH_SPLIT = re.compile(r"\n\s*\n")


def extract_text(filename: str, content: bytes) -> str:
    if filename.lower().endswith(".pdf"):
        reader = PdfReader(BytesIO(content))
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)
    return content.decode("utf-8", errors="replace")


def _split_sentences(paragraph: str) -> list[str]:
    return [s for s in _SENTENCE_SPLIT.split(paragraph) if s.strip()]


def chunk_text(text: str, target_words: int = CHUNK_TARGET_WORDS) -> list[str]:
    chunks: list[str] = []

    for paragraph in _PARAGRAPH_SPLIT.split(text):
        paragraph = paragraph.strip()
        if not paragraph:
            continue

        if len(paragraph.split()) <= target_words:
            chunks.append(paragraph)
            continue

        current: list[str] = []
        current_words = 0
        for sentence in _split_sentences(paragraph):
            sentence_words = len(sentence.split())
            if current and current_words + sentence_words > target_words:
                chunks.append(" ".join(current))
                current = []
                current_words = 0
            current.append(sentence)
            current_words += sentence_words
        if current:
            chunks.append(" ".join(current))

    return chunks
