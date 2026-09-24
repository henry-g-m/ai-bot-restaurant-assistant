from restaurant_bot.documents import chunk_text, extract_text


def test_extract_text_txt():
    assert extract_text("notes.txt", b"hello world") == "hello world"


def test_chunk_short_paragraph_is_one_chunk():
    text = "This is a short paragraph."
    assert chunk_text(text) == ["This is a short paragraph."]


def test_chunk_multiple_paragraphs():
    text = "First paragraph.\n\nSecond paragraph."
    assert chunk_text(text) == ["First paragraph.", "Second paragraph."]


def test_chunk_long_paragraph_splits_on_sentences():
    sentence = "This is a sentence with several words in it. "
    long_paragraph = sentence * 40  # ~320 words, exceeds default 180-word target
    chunks = chunk_text(long_paragraph, target_words=180)
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk.split()) <= 180 + 10  # allow last sentence to slightly exceed


def test_chunk_empty_input():
    assert chunk_text("") == []
    assert chunk_text("   \n\n  ") == []
