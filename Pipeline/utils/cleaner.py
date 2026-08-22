"""
Cleaner utilities.
Never modifies indentation.
"""

import re

def normalize_newlines(text):
    return (
        text
        .replace("\r\n", "\n")
        .replace("\r", "\n")
    )

def remove_trailing_spaces(text):
    return "\n".join(
        line.rstrip()
        for line in text.split("\n")
    )

def collapse_blank_lines(
    text,
    maximum=2
):
    pattern = r"\n{" + str(maximum + 1) + ",}"
    return re.sub(
        pattern,
        "\n" * maximum,
        text
    )

def remove_invalid_utf(text):
    return (
        text
        .encode(
            "utf8",
            "ignore"
        )
        .decode("utf8")
    )

def clean_text(text):
    if text is None:
        return ""
    text = remove_invalid_utf(text)
    text = normalize_newlines(text)
    text = remove_trailing_spaces(text)
    text = collapse_blank_lines(text)
    return text.strip()

def clean_sample(sample):
    sample["instruction"] = clean_text(
        sample.get(
            "instruction",
            ""
        )
    )

    sample["input"] = clean_text(
        sample.get(
            "input",
            ""
        )
    )

    sample["output"] = clean_text(
        sample.get(
            "output",
            ""
        )
    )

    sample["language"] = (
        sample
        .get("language", "")
        .lower()
        .strip()
    )

    sample["license"] = (
        sample
        .get("license", "")
        .lower()
        .strip()
    )

    return sample

def is_empty(sample):
    return (
        len(sample["output"]) == 0
    )

def has_binary_content(text):
    return "\x00" in text

def is_valid(sample):
    if is_empty(sample):
        return False
    if has_binary_content(
        sample["output"]
    ):
        return False
    return True