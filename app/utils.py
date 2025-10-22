import hashlib
import re
from datetime import datetime, timezone

from app.models import StringResponse, Properties

def generate_sha256(text: str) -> str:
    # Hash any text using sha256 algorithm
    return hashlib.sha256(text.encode()).hexdigest()



def string_analyzer(text: str):
    lower_text = text.lower()
    lower_text = lower_text.replace(" ", "")
    reversed_text = lower_text[::-1]
    if reversed_text == lower_text:
        is_palindrome = True
    else:
        is_palindrome = False
    unique_chars = set(lower_text)

    words_count = len(text.split())

    sha256_hash = generate_sha256(text=text)

    character_frequncy_map = {}
    for char in lower_text:
        if char in character_frequncy_map:
            character_frequncy_map[char] += 1
        else:
            character_frequncy_map[char] = 1

    data = Properties(
        length = len(lower_text),
        is_palindrome = is_palindrome,
        unique_characters = len(unique_chars),
        words_count = words_count,
        sha256_hash =  sha256_hash,
        character_frequency_map = character_frequncy_map
    )
    

    return data


def now_isoutc() -> str:
    return datetime.now(timezone.utc).isoformat()

def parse_nl_query(text: str):
    text = text.lower()
    filters = {}

    if "palindrom" in text:
        filters["is_palindrome"] = True

    if "single word" in text or "one word" in text:
        filters["word_count"] = 1

    if match := re.search(r"longer than (\d+)", text):
        filters["min_length"] = int(match.group(1)) + 1

    if match := re.search(r"shorter than (\d+)", text):
        filters["max_length"] = int(match.group(1)) - 1

    if match := re.search(r"letter\s+([a-zA-Z])", text):
        filters["contains_character"] = match.group(1)

    if not filters:
        raise ValueError("Could not understand the query.")

    return filters




