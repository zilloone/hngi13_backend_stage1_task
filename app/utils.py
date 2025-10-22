import hashlib
import re
from datetime import datetime, timezone
from typing import Any

from app.models import StringResponse, Properties

def generate_sha256(text: str) -> str:
    # Hash any text using sha256 algorithm
    return hashlib.sha256(text.encode("utf-8")).hexdigest()



def string_analyzer(text: str):
    lower_text = text.lower()
    lower_text = lower_text.replace(" ", "")
    reversed_text = lower_text[::-1]
    if reversed_text == lower_text:
        is_palindrome = True
    else:
        is_palindrome = False
    unique_chars = set(lower_text)

    word_count = len(text.split())

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
        word_count = word_count,
        sha256_hash =  sha256_hash,
        character_frequency_map = character_frequncy_map
    )
    

    return data


def now_isoutc() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_nl_query(q: str) -> dict[str, Any]:
    s = q.lower()
    parsed: dict[str, Any] = {}

    
    if re.search(r'\bsingle word\b|\bone word\b', s):
        parsed['word_count'] = 1

    if 'palindrom' in s:
        parsed['is_palindrome'] = True

    m = re.search(r'longer than (\d+)', s)
    if m:
        parsed['min_length'] = int(m.group(1)) + 1

    
    m = re.search(r'shorter than (\d+)', s)
    if m:
        parsed['max_length'] = int(m.group(1)) - 1

    
    if re.search(r'first vowel', s):
        parsed['contains_character'] = 'a'

    m = re.search(r'letter\s+([a-zA-Z])', s)
    if m:
        parsed['contains_character'] = m.group(1)

    if 'containing the letter' in s and 'contains_character' not in parsed:
        m = re.search(r'containing the letter\s+([a-zA-Z])', s)
        if m:
            parsed['contains_character'] = m.group(1)

    if not parsed:
        raise ValueError("Unable to parse natural language query")

    # conflict check: min_length > max_length
    if 'min_length' in parsed and 'max_length' in parsed and parsed['min_length'] > parsed['max_length']:
        raise ValueError("Parsed filters conflict: min_length > max_length")

    return parsed




