"""
validate.py
Validation for processed samples.
"""

from typing import Dict, List
from config import (
    MAX_TOKENS,
    MIN_TOKENS
)
from utils.tokenizer import (
    sample_tokens
)


REQUIRED_FIELDS = [
    "instruction",
    "input",
    "output",
    "language",
    "license"
]


def validate_sample(sample: Dict) -> List[str]:
    errors = []
    # ----------------------------------------------------
    # Required fields
    # ----------------------------------------------------

    for field in REQUIRED_FIELDS:
        if field not in sample:
            errors.append(
                f"Missing field: {field}"
            )

    if errors:
        return errors
    # ----------------------------------------------------
    # Type checking
    # ----------------------------------------------------
    for field in REQUIRED_FIELDS:
        if not isinstance(sample[field], str):
            errors.append(
                f"{field} must be str"
            )

    if errors:
        return errors
    # ----------------------------------------------------
    # Empty fields
    # ----------------------------------------------------

    if not sample["instruction"].strip():
        errors.append(
            "Instruction empty"
        )

    if not sample["output"].strip():
        errors.append(
            "Output empty"
        )

    # ----------------------------------------------------
    # UTF-8 validation
    # ----------------------------------------------------

    try:
        sample["output"].encode("utf8")
    except UnicodeEncodeError:
        errors.append(
            "Invalid UTF-8"
        )

    # ----------------------------------------------------
    # Token validation
    # ----------------------------------------------------

    total = sample_tokens(sample)
    if total > MAX_TOKENS:
        errors.append(
            f"Too many tokens ({total})"
        )

    if total < MIN_TOKENS:
        errors.append(
            f"Too few tokens ({total})"
        )

    return errors


def is_valid(sample):
    return len(
        validate_sample(sample)
    ) == 0