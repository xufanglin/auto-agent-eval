"""
Text statistics utilities.
"""
from collections import Counter
import re


def word_count(text: str) -> int:
    """Return the number of words in the text."""
    return len(text.split())


def char_count(text: str, include_spaces: bool = True) -> int:
    """Return character count, optionally excluding spaces."""
    if include_spaces:
        return len(text)
    return len(text.replace(" ", ""))


def most_common_words(text: str, n: int = 5) -> list[tuple[str, int]]:
    """Return the n most common words (case-insensitive, no punctuation)."""
    words = re.findall(r"[a-z]+", text.lower())
    return Counter(words).most_common(n)


def average_word_length(text: str) -> float:
    """Return the average word length. Raises ValueError if text has no words."""
    words = text.split()
    if not words:
        raise ValueError("Text contains no words")
    return sum(len(w) for w in words) / len(words)


def is_palindrome(s: str) -> bool:
    """Return True if s is a palindrome (case-insensitive, ignores non-alphanumeric)."""
    cleaned = re.sub(r"[^a-z0-9]", "", s.lower())
    return cleaned == cleaned[::-1]


def truncate(text: str, max_len: int, suffix: str = "...") -> str:
    """
    Truncate text to max_len characters.
    If truncated, append suffix. The total length including suffix will not exceed max_len.
    """
    if len(text) <= max_len:
        return text
    return text[: max_len - len(suffix)] + suffix
