"""
language_filter.py
Language filtering utilities.
"""

from config import (
    SUPPORTED_LANGUAGES,
    LANGUAGE_ALIASES
)

def normalize(language):
    if language is None:
        return ""
    language = language.lower().strip()
    return LANGUAGE_ALIASES.get(
        language,
        language
    )


def filter_sample(sample):
    language = normalize(
        sample.get(
            "language",
            ""
        )
    )

    if not language:
        return False
    sample["language"] = language
    return language in SUPPORTED_LANGUAGES